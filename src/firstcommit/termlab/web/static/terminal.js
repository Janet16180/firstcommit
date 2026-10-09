"use strict";

/*
 * The page's terminal: xterm.js (vendored, see xterm-LICENSE.txt) talking to the
 * player's own shell through the /api/terminal WebSocket (or another terminal path), whose protocol is
 * documented in termlab/web/terminal.py. Binary frames carry bytes both ways; the
 * only text frame we send is a resize. One pane can live for the whole page and
 * survive look switches; dispose() closes it.
 *
 * Needs xterm.js and its fit addon loaded first. Defines one global, createTerminal.
 */

/*
 * Builds the pane; `start()` opens it once it is in the page. Options:
 * - protocol: the game's WebSocket subprotocol, as in the server's TerminalSettings.
 * - token: returns the access key, or null; read at each connection.
 * - command: the command that starts the server, named in the notices.
 * - looks: { name: { fontFamily, fontSize, theme } } with xterm theme colors; the first is the
 *   default. fontSize is in CSS pixels, 14 when left out.
 * - storagePrefix: prefix of the localStorage keys that remember the player's open/closed
 *   choice and height.
 * - onUnreachable: called when the terminal cannot connect. A refused handshake looks like a
 *   network failure (1006), so the page asks its API, which tells a stale key apart.
 * - maxTerminals: the server's limit, for the "too many terminals" notice.
 * - roomAbove: pixels of the pane's parent kept for the page above the terminal.
 * - openFromHeight: window height from which the pane starts open, unless the player chose.
 * - labels: { connecting, connected, hide, show, hint }, the words of the status, the button and
 *   the paste and copy hint in the game's language; English for any left out. setLabels()
 *   changes some of them later.
 * - path: the terminal's path on the server, /api/terminal unless the server serves more.
 * - onTitle: called with each title the shell sets (an OSC 0 or 2 sequence), "" included.
 * - onClose: called each time the shell's connection closes, and when the pane is disposed: the
 *   programs it ran have been hung up, so anything their titles announced is over.
 */
function createTerminal({
  protocol,
  token,
  command,
  looks,
  storagePrefix,
  onUnreachable = () => {},
  maxTerminals = 3,
  roomAbove = 300,
  openFromHeight = 820,
  labels = {},
  path = "/api/terminal",
  onTitle = () => {},
  onClose = () => {},
}) {
  /* What each close code means for the player, and whether to reconnect without being asked. */
  const closed = {
    1000: { status: "shell exited", text: "The shell exited. Press Enter or click here to start a new one.", retry: false },
    1013: { status: "too many terminals", text: `Too many terminals are open (${maxTerminals} at most): close one in another tab. Retrying.`, retry: true },
    1011: { status: "no shell", text: "The server could not start a shell. Press Enter or click here to try again.", retry: false },
    1002: { status: "disconnected", text: "The connection broke the protocol. Press Enter or click here to reconnect.", retry: false },
    1009: { status: "disconnected", text: "A message was too big for the terminal. Press Enter or click here to reconnect.", retry: false },
  };
  const unreachable = { status: "offline", text: `Cannot reach the terminal: is \`${command}\` still running? Retrying.`, retry: true };
  const minHeight = 120;
  const defaultFontSize = 14;
  const defaultLook = Object.values(looks)[0];
  let words = { connecting: "connecting", connected: "connected", hide: "hide", show: "show", hint: "Ctrl+V paste · Ctrl+C copies a selection", ...labels };

  function node(tag, attributes, ...children) {
    const made = document.createElement(tag);
    for (const [key, value] of Object.entries(attributes)) {
      if (key === "class") made.className = value;
      else if (key.startsWith("on")) made.addEventListener(key.slice(2), value);
      else made.setAttribute(key, value);
    }
    made.append(...children);
    return made;
  }

  /* The player's choices, as JSON; null when storage is blocked or holds nothing. */
  function recall(key) {
    try {
      return JSON.parse(localStorage.getItem(storagePrefix + key));
    } catch (error) {
      return null;
    }
  }

  function remember(key, value) {
    try {
      localStorage.setItem(storagePrefix + key, JSON.stringify(value));
    } catch (error) {
      /* Storage is blocked: the choice lasts until the page closes. */
    }
  }

  const encoder = new TextEncoder();
  const host = node("div", { class: "term-host" });
  const statusText = node("span", {}, words.connecting);
  const status = node("span", { class: "term-status", "data-state": "connecting", role: "status" }, node("i", { "aria-hidden": "true" }), statusText);
  const toggle = node("button", { class: "term-toggle", type: "button", onclick: () => setOpen(panel.classList.contains("is-closed"), true) });
  const title = node("span", { class: "term-title" });
  const hint = node("span", { class: "term-hint" }, words.hint);
  const panel = node("section", { class: "panel term-panel", "aria-label": "Terminal" },
    node("div", { class: "term-head" }, title, status,
      node("div", { class: "term-actions" }, hint, toggle),
    ),
    host,
  );
  const grip = node("div", {
    class: "term-grip",
    role: "separator",
    tabindex: "0",
    "aria-orientation": "horizontal",
    "aria-label": "Resize the terminal (Up and Down arrows)",
    title: "Drag to resize the terminal",
  });
  const element = node("div", { class: "term-dock" }, grip, panel);

  const sizeOf = (chosen) => chosen.fontSize || defaultFontSize;
  const term = new Terminal({ cursorBlink: true, fontSize: sizeOf(defaultLook), lineHeight: 1.15, scrollback: 5000 });
  const fitAddon = new FitAddon.FitAddon();
  term.loadAddon(fitAddon);
  let look = defaultLook;
  let socket = null;
  let started = false;
  let opened = false;
  let disposed = false;
  let waiting = false;
  let attempts = 0;
  let retryTimer = null;
  let pending = "";
  /* The label the status shows, when it shows one (other statuses are built from a close code). */
  let statusLabel = "connecting";

  function setStatus(state, text, label = null) {
    status.dataset.state = state;
    statusText.textContent = text;
    statusLabel = label;
  }

  function showToggle() {
    toggle.textContent = panel.classList.contains("is-closed") ? words.show : words.hide;
  }

  function isOpen() {
    return socket !== null && socket.readyState === WebSocket.OPEN;
  }

  function sendSize() {
    if (isOpen()) socket.send(JSON.stringify({ type: "resize", cols: term.cols, rows: term.rows }));
  }

  /* Fit the terminal to its box, unless the box is hidden (fitting to nothing would mean 1 row). */
  function fit() {
    if (opened && host.offsetHeight > 0 && host.offsetWidth > 0) fitAddon.fit();
  }

  function connect() {
    clearTimeout(retryTimer);
    waiting = false;
    setStatus("connecting", words.connecting, "connecting");
    /* A page cannot add headers to a WebSocket, so the key travels as a second subprotocol.
       Each handler acts only while its own socket is the current one. */
    const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}${path}`, [protocol, `t.${token()}`]);
    socket = ws;
    ws.binaryType = "arraybuffer";
    ws.onopen = () => {
      if (ws !== socket) return;
      if (ws.protocol !== protocol) {
        socket = null;
        ws.close();
        refused();
        return;
      }
      setStatus("open", words.connected, "connected");
      sendSize();
      if (pending) ws.send(encoder.encode(pending));
      pending = "";
    };
    /* A server that is full accepts the connection and then closes it, so only output
       from the shell proves the connection works and resets the backoff. */
    ws.onmessage = (event) => {
      if (ws !== socket || typeof event.data === "string") return;
      attempts = 0;
      term.write(new Uint8Array(event.data));
    };
    ws.onclose = (event) => {
      if (ws !== socket) return;
      socket = null;
      if (disposed) return;
      onClose();
      const info = closed[event.code] || unreachable;
      if (info === unreachable) onUnreachable();
      if (attempts === 0) term.write(`\r\n\x1b[33m[${info.text}]\x1b[0m\r\n`);
      if (info.retry) {
        const delay = Math.min(1000 * 2 ** attempts, 15000);
        attempts += 1;
        setStatus("retry", `${info.status}: retrying in ${Math.round(delay / 1000)} s`);
        retryTimer = setTimeout(connect, delay);
      } else {
        waiting = true;
        setStatus("closed", info.status);
      }
    };
  }

  function refused() {
    term.write(`\r\n\x1b[33m[The server did not accept this terminal's access key. Open the link that ${command} printed.]\x1b[0m\r\n`);
    waiting = true;
    setStatus("closed", "not authorized");
  }

  /* Only the player's own choices are remembered, not the defaults picked for the window size. */
  function setOpen(open, chosen) {
    panel.classList.toggle("is-closed", !open);
    element.classList.toggle("is-closed", !open);
    showToggle();
    toggle.setAttribute("aria-expanded", String(open));
    if (chosen) remember("terminal", open ? "open" : "closed");
    if (open) requestAnimationFrame(() => fit());
  }

  /* The terminal's height, kept between a few rows and what leaves the page roomAbove pixels. */
  function setHeight(px, chosen) {
    const room = element.parentElement ? element.parentElement.clientHeight - roomAbove : 600;
    const height = Math.round(Math.max(minHeight, Math.min(px, Math.max(room, minHeight))));
    host.style.height = `${height}px`;
    grip.setAttribute("aria-valuenow", String(height));
    if (chosen) remember("terminalHeight", height);
  }

  /* Ctrl+V pastes and Ctrl+C copies a selection, as in Windows Terminal, instead of sending ^V
     (which makes the tty take the next key literally) and ^C. Without a selection Ctrl+C
     still interrupts. Returning false makes xterm leave the key to the browser. */
  term.attachCustomKeyEventHandler((event) => {
    if (event.type !== "keydown" || !event.ctrlKey || event.altKey || event.metaKey) return true;
    if (event.code === "KeyV") return false;
    if (event.code !== "KeyC" || !term.hasSelection()) return true;
    event.preventDefault();
    navigator.clipboard.writeText(term.getSelection())
      .then(() => term.clearSelection())
      .catch(() => null); /* Clipboard refused: keep the selection, so the context menu can still copy it. */
    return false;
  });

  term.onData((data) => {
    if (isOpen()) socket.send(encoder.encode(data));
    else if (waiting && data.includes("\r")) connect();
  });
  term.onResize(() => sendSize());
  term.onTitleChange((shellTitle) => onTitle(shellTitle));
  host.addEventListener("click", () => waiting && connect());
  new ResizeObserver(() => requestAnimationFrame(() => fit())).observe(host);

  grip.addEventListener("pointerdown", (event) => {
    const startY = event.clientY;
    const startHeight = host.offsetHeight;
    grip.setPointerCapture(event.pointerId);
    const move = (moved) => setHeight(startHeight - (moved.clientY - startY), true);
    grip.addEventListener("pointermove", move);
    grip.addEventListener("pointerup", () => grip.removeEventListener("pointermove", move), { once: true });
  });
  grip.addEventListener("keydown", (event) => {
    const step = { ArrowUp: 24, ArrowDown: -24 }[event.key];
    if (!step) return;
    event.preventDefault();
    setHeight(host.offsetHeight + step, true);
  });

  /* Drop C0 and C1 control characters and DEL. */
  function withoutControls(text) {
    // eslint-disable-next-line no-control-regex
    return text.replace(/[\x00-\x1f\x7f-\x9f]/g, "");
  }

  /* Send keys to the shell, opening the pane and connecting first when needed. */
  function send(keys) {
    if (panel.classList.contains("is-closed")) setOpen(true, false);
    term.focus();
    if (isOpen()) {
      socket.send(encoder.encode(keys));
      return;
    }
    pending = keys;
    if (waiting) connect();
  }

  return {
    element,

    /* Open xterm once its fonts are in, then connect; later calls just refit the moved pane. */
    async start() {
      const choice = recall("terminal");
      setOpen(choice ? choice === "open" : window.innerHeight >= openFromHeight, false);
      setHeight(recall("terminalHeight") || 240, false);
      /* Set before the await: a second call while the font loads (a look switch re-rendering
         the page) must not open a second xterm and socket. */
      if (started) {
        requestAnimationFrame(() => fit());
        return;
      }
      started = true;
      await document.fonts.load(`${sizeOf(look)}px ${look.fontFamily}`).catch(() => null);
      if (disposed) return;
      term.options.fontFamily = look.fontFamily;
      term.options.fontSize = sizeOf(look);
      term.options.theme = look.theme;
      term.open(host);
      opened = true;
      fit();
      connect();
    },

    /* Use other words for the status, the button and the hint, at once; the words left out stay. */
    setLabels(newLabels) {
      words = { ...words, ...newLabels };
      hint.textContent = words.hint;
      if (statusLabel) statusText.textContent = words[statusLabel];
      showToggle();
    },

    /* Switch to one of the looks (the default one for an unknown name) and set the pane's title. */
    async setLook(name, label) {
      look = looks[name] || defaultLook;
      title.textContent = label;
      if (!opened) return;
      term.options.theme = look.theme;
      await document.fonts.load(`${sizeOf(look)}px ${look.fontFamily}`).catch(() => null);
      term.options.fontFamily = look.fontFamily;
      term.options.fontSize = sizeOf(look);
      fit();
    },

    /* Type a command at the prompt without pressing Enter, so the player can read or edit it first.
       Control characters are dropped: a newline or Ctrl-key in the text could run or alter something,
       and xterm.js acts on C1 controls (U+0080 to U+009F) when the shell echoes them. */
    type(text) {
      send(withoutControls(text));
    },

    /* Type a command at the prompt and press Enter: its control characters are dropped as in type(),
       so the one Enter added is the only one sent. */
    run(line) {
      send(`${withoutControls(line)}\r`);
    },

    /* Send keys exactly as given, control keys included, as if the player pressed them: for a
       game's own button that drives a program in the terminal, such as Esc then :q! in vim. */
    keys(raw) {
      send(raw);
    },

    dispose() {
      if (!disposed) onClose();
      disposed = true;
      clearTimeout(retryTimer);
      if (socket) {
        socket.onclose = null;
        socket.close(1000);
      }
      term.dispose();
      element.remove();
    },
  };
}
