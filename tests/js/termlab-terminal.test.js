"use strict";

/* terminal.js runs in a VM context with stand-ins for the DOM, xterm.js and WebSocket, so a test
   decides when the fonts load, when a socket opens or closes, and when a timer fires. */

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const SOURCE = fs.readFileSync(path.join(__dirname, "..", "..", "src", "firstcommit", "termlab", "web", "static", "terminal.js"), "utf8");

const created = [];

function element() {
  const classes = new Set();
  let text = "";
  const made = {
    classList: { toggle: (name, on) => (on ? classes.add(name) : classes.delete(name)), contains: (name) => classes.has(name) },
    dataset: {},
    style: {},
    offsetHeight: 200,
    offsetWidth: 600,
    parentElement: { clientHeight: 900 },
    setAttribute() {},
    addEventListener() {},
    append(...children) {
      text += children.filter((child) => typeof child === "string").join("");
    },
    remove() {},
    focus() {},
    get textContent() {
      return text;
    },
    set textContent(value) {
      text = value;
    },
  };
  created.push(made);
  return made;
}

/* A pane whose sockets, terminal output and timers the test can see. */
function page({ token = () => "KEY", looks = { plain: { fontFamily: "monospace", theme: {} } }, labels, ...chosen } = {}) {
  created.length = 0;
  const seen = { sockets: [], written: [], timers: [], fonts: [], terminals: [], elements: created };
  let fontsLoaded = null;
  class FakeSocket {
    constructor(url, protocols) {
      Object.assign(this, { url, protocols, sent: [], readyState: 0, closedByPage: false });
      seen.sockets.push(this);
    }

    send(data) {
      this.sent.push(data);
    }

    close() {
      this.closedByPage = true;
      this.readyState = 3;
    }
  }
  FakeSocket.OPEN = 1;
  class Terminal {
    constructor(options) {
      Object.assign(this, { options: { ...options }, cols: 80, rows: 24 });
      seen.terminals.push(this);
    }

    write(data) {
      seen.written.push(typeof data === "string" ? data : "<bytes>");
    }

    loadAddon() {}
    open() {}
    focus() {}
    dispose() {}
    attachCustomKeyEventHandler() {}
    onData() {}
    onResize() {}
    onTitleChange(handler) {
      this.titleChanged = handler;
    }
  }
  const context = vm.createContext({
    document: {
      createElement: element,
      fonts: {
        load: (font) => {
          seen.fonts.push(font);
          return new Promise((resolve) => (fontsLoaded = resolve));
        },
      },
    },
    Terminal,
    FitAddon: { FitAddon: class { fit() {} } },
    WebSocket: FakeSocket,
    ResizeObserver: class { observe() {} },
    requestAnimationFrame: () => 0,
    setTimeout: (callback) => seen.timers.push(callback),
    clearTimeout() {},
    localStorage: { getItem: () => null, setItem() {} },
    window: { innerHeight: 1000 },
    location: { protocol: "http:", host: "localhost:8800" },
    navigator: {},
    TextEncoder,
  });
  vm.runInContext(SOURCE, context);
  const pane = context.createTerminal({
    protocol: "testgame",
    token,
    command: "testgame serve",
    looks,
    storagePrefix: "testgame.",
    labels,
    ...chosen,
  });
  return { pane, seen, loadFonts: () => fontsLoaded() };
}

/* Start the pane, let its fonts load, and return its socket. */
async function started(current) {
  const starting = current.pane.start();
  current.loadFonts();
  await starting;
  return current.seen.sockets[0];
}

/* What the browser does when the server accepts a socket and selects a protocol. */
function accept(socket, protocol = "testgame") {
  socket.protocol = protocol;
  socket.readyState = 1;
  socket.onopen();
}

test("two starts while the fonts load open one socket, offering the protocol and the key (B1)", async () => {
  const current = page();
  const first = current.pane.start();
  const second = current.pane.start();
  current.loadFonts();
  await Promise.all([first, second]);
  assert.equal(current.seen.sockets.length, 1);
  assert.deepEqual([...current.seen.sockets[0].protocols], ["testgame", "t.KEY"]);
  assert.equal(current.seen.sockets[0].url, "ws://localhost:8800/api/terminal");
});

test("a socket opened with another protocol is closed, sends nothing and says the key was refused", async () => {
  const current = page();
  const socket = await started(current);
  accept(socket, "");
  assert.equal(socket.closedByPage, true);
  assert.deepEqual(socket.sent, []);
  assert.ok(current.seen.written.some((text) => text.includes("did not accept this terminal's access key")));
});

test("a replaced socket's late events change nothing", async () => {
  let key = "OLD";
  const current = page({ token: () => key });
  const old = await started(current);
  accept(old);
  old.onclose({ code: 1013 });
  key = "NEW";
  current.seen.timers.shift()();
  assert.deepEqual([...current.seen.sockets[1].protocols], ["testgame", "t.NEW"]);

  /* Typed while reconnecting: it waits for the new socket, never the old one. */
  current.pane.type("ls");
  const written = current.seen.written.length;
  old.onmessage({ data: new ArrayBuffer(3) });
  old.onclose({ code: 1006 });
  old.onopen();
  assert.equal(current.seen.written.length, written);
  assert.deepEqual(current.seen.timers, []);
  assert.equal(old.sent.length, 1, "only the resize it sent while it was current");

  const fresh = current.seen.sockets[1];
  accept(fresh);
  assert.equal(Buffer.from(fresh.sent[fresh.sent.length - 1]).toString("utf8"), "ls");
});

test("type() drops C0 and C1 control characters and DEL, and keeps the rest", async () => {
  const current = page();
  const socket = await started(current);
  accept(socket);
  current.pane.type("rm -rf x\n\r\x03\x1b[A\x7f\x00\x15 y\x9b\x85\x9f café");
  const sent = Buffer.from(socket.sent[socket.sent.length - 1]).toString("utf8");
  assert.equal(sent, "rm -rf x[A y café");
});

test("run() types the line without its control characters and presses Enter once", async () => {
  const current = page();
  const socket = await started(current);
  accept(socket);
  current.pane.run("git status\n\r\x03\x9b -s");
  const sent = Buffer.from(socket.sent[socket.sent.length - 1]).toString("utf8");
  assert.equal(sent, "git status -s\r");
});

test("keys() sends its keys as they are, control keys included, and presses nothing more", async () => {
  const current = page();
  const socket = await started(current);
  accept(socket);
  current.pane.keys("\x1b:q!\r");
  current.pane.keys("\x18n");
  const sent = socket.sent.slice(-2).map((data) => Buffer.from(data).toString("utf8"));
  assert.deepEqual(sent, ["\x1b:q!\r", "\x18n"]);
});

test("a line run while the terminal connects waits for it, then runs", async () => {
  let key = "OLD";
  const current = page({ token: () => key });
  const old = await started(current);
  accept(old);
  old.onclose({ code: 1013 });
  key = "NEW";
  current.seen.timers.shift()();
  current.pane.run("git log");
  const fresh = current.seen.sockets[1];
  accept(fresh);
  assert.equal(Buffer.from(fresh.sent[fresh.sent.length - 1]).toString("utf8"), "git log\r");
});

test("a look without a font size draws at 14 px and waits for its font at that size", async () => {
  const current = page();
  await started(current);
  assert.equal(current.seen.terminals[0].options.fontSize, 14);
  assert.deepEqual(current.seen.fonts, ["14px monospace"]);
});

test("a look's font size sets the terminal's size and the size its font is loaded at", async () => {
  const looks = { crt: { fontFamily: "VT323", fontSize: 19, theme: {} }, plain: { fontFamily: "monospace", theme: {} } };
  const current = page({ looks });
  await started(current);
  const terminal = current.seen.terminals[0];
  assert.deepEqual([terminal.options.fontSize, terminal.options.fontFamily], [19, "VT323"]);
  assert.deepEqual(current.seen.fonts, ["19px VT323"]);

  const switching = current.pane.setLook("plain", "Plain");
  current.loadFonts();
  await switching;
  assert.deepEqual([terminal.options.fontSize, terminal.options.fontFamily], [14, "monospace"]);
  assert.equal(current.seen.fonts[1], "14px monospace");
});

/* The texts the pane shows now, in the order its elements were made. */
function texts(current) {
  return current.seen.elements.map((made) => made.textContent).filter((text) => text !== "");
}

test("the status and the hide button speak English unless the game gives its own labels", async () => {
  const english = page();
  accept(await started(english));
  assert.ok(texts(english).includes("connected") && texts(english).includes("hide"));
  const spanish = page({ labels: { connecting: "conectando", connected: "conectado", hide: "ocultar" } });
  assert.ok(texts(spanish).includes("conectando"));
  accept(await started(spanish));
  assert.ok(texts(spanish).includes("conectado") && texts(spanish).includes("ocultar"));
  assert.ok(!texts(spanish).includes("connected") && !texts(spanish).includes("hide"));
});

test("the paste and copy hint speaks the game's language, and setLabels changes it at once", () => {
  const ENGLISH = "Ctrl+V paste · Ctrl+C copies a selection";
  const SPANISH = "Ctrl+V pega · Ctrl+C copia lo seleccionado";
  assert.ok(texts(page()).includes(ENGLISH));
  const spanish = page({ labels: { hint: SPANISH } });
  assert.ok(texts(spanish).includes(SPANISH) && !texts(spanish).includes(ENGLISH));
  spanish.pane.setLabels({ hint: ENGLISH });
  assert.ok(texts(spanish).includes(ENGLISH) && !texts(spanish).includes(SPANISH));
});

test("setLabels changes the status and the button at once, and later states use the new labels", async () => {
  const current = page();
  const socket = await started(current);
  current.pane.setLabels({ connected: "conectado", hide: "ocultar", show: "mostrar" });
  assert.ok(texts(current).includes("connecting") && texts(current).includes("ocultar"));
  accept(socket);
  assert.ok(texts(current).includes("conectado"));
  current.pane.setLabels({ connected: "connected" });
  assert.ok(texts(current).includes("connected") && texts(current).includes("ocultar"));
});

test("each time the shell's connection closes, and when the pane is disposed, onClose is told", async () => {
  let closes = 0;
  const current = page({ onClose: () => (closes += 1) });
  const socket = await started(current);
  accept(socket);
  socket.onclose({ code: 1000 });
  assert.equal(closes, 1);
  current.pane.dispose();
  assert.equal(closes, 2);
});

test("a replaced socket's late close tells onClose nothing", async () => {
  let closes = 0;
  const current = page({ onClose: () => (closes += 1) });
  const old = await started(current);
  accept(old);
  old.onclose({ code: 1013 });
  current.seen.timers.shift()();
  old.onclose({ code: 1006 });
  assert.equal(closes, 1);
});

test("a pane connects to /api/terminal, or to the path it was given", async () => {
  assert.equal((await started(page())).url, "ws://localhost:8800/api/terminal");
  assert.equal((await started(page({ path: "/api/terminal/second" }))).url, "ws://localhost:8800/api/terminal/second");
});

test("each title the shell sets reaches onTitle", async () => {
  const titles = [];
  const current = page({ onTitle: (title) => titles.push(title) });
  await started(current);
  current.seen.terminals[0].titleChanged("vim notes.txt");
  current.seen.terminals[0].titleChanged("");
  assert.deepEqual(titles, ["vim notes.txt", ""]);
});
