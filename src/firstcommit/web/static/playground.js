"use strict";

/*
 * The two-person playground (docs/drafts/playground.md, parts 1, 4, 5, 6.2, 7 and 8): the share
 * figure of you, GitHub and Alex (`share`, theme-time-share.js's TimeShare), each person's buttons
 * in their slot under their computer, the result of the last press, and that result said in one
 * sentence to a polite live region. It draws what the server sends (Observation.buttons and
 * PressView) and hands presses and lines to type to its owner: every button runs on the server.
 *
 * Buttons are real buttons in a toolbar per person; arrow keys move between them. An off button
 * stays focusable (aria-disabled) and its description says why; an on button's description is the
 * line it runs. The line, or the reason, also shows under the bar for the button focused or
 * hovered. Needs dom.js and markup.js. Defines one global, PlaygroundPanel.
 */

/* global Dom, Markup */
/* exported PlaygroundPanel */

const PlaygroundPanel = (function () {
  const { el } = Dom;
  const PEOPLE = { you: { ran: "You ran", bar: "Your buttons" }, alex: { ran: "Alex ran", bar: "Alex's buttons" } };
  const TYPE = "Type it in the terminal";
  const OFF = "That button cannot be pressed now.";
  const KEYS = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };

  /* The status in words: done, or who refused with its exit status (git's, or the shell's). */
  function statusWords({ command, status }) {
    const refuser = command.startsWith("git ") ? "Git refused" : "It failed";
    return status === 0 ? "done" : `${refuser} (exit status ${status})`;
  }

  /* Everything below works on one `panel`: share, the owner's callbacks, the element and its
     parts, the observation drawn last, the animations still running, whether a press is running,
     the button to keep focus on, and a counter for description ids. */

  const offNow = (panel, view) => panel.pressing || view.off !== "";

  function press(panel, person, view) {
    if (offNow(panel, view)) return;
    for (const animation of panel.running) animation.finish();
    panel.running = [];
    panel.focus = { person, id: view.id };
    panel.onPress(person, view.id);
  }

  function showLine(panel, line, person, view) {
    line.textContent = panel.pressing ? "" : view.off || view.line;
    panel.focus = { person, id: view.id };
  }

  /* Arrow keys, Home and End move between a bar's buttons; the one reached joins the tab order. */
  function rove(event, buttons) {
    const at = buttons.indexOf(event.currentTarget);
    const to = event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : KEYS[event.key] === undefined ? null : (at + KEYS[event.key] + buttons.length) % buttons.length;
    if (to === null) return;
    event.preventDefault();
    for (const [index, item] of buttons.entries()) item.setAttribute("tabindex", index === to ? "0" : "-1");
    buttons[to].focus();
  }

  function barButton(panel, person, view, line) {
    panel.ids += 1;
    const described = el("span", { id: `pg-line-${panel.ids}`, hidden: true }, view.off || view.line);
    const node = el("button", {
      type: "button",
      class: "btn btn-small pg-button",
      "data-id": view.id,
      "data-off": view.off || null,
      "aria-disabled": offNow(panel, view) ? "true" : null,
      "aria-describedby": described.id,
      tabindex: "-1",
      onclick: () => press(panel, person, view),
      onfocus: () => showLine(panel, line, person, view),
      onmouseenter: () => showLine(panel, line, person, view),
    }, view.label);
    return { node, described };
  }

  /* One person's toolbar, its first button (or the one focused last) in the tab order. */
  function bar(panel, person, views) {
    const line = el("p", { class: "pg-line", "aria-hidden": "true" });
    const made = views.map((view) => barButton(panel, person, view, line));
    const buttons = made.map(({ node }) => node);
    const kept = panel.focus && panel.focus.person === person ? views.findIndex((view) => view.id === panel.focus.id) : -1;
    if (buttons.length) buttons[Math.max(kept, 0)].setAttribute("tabindex", "0");
    for (const node of buttons) node.addEventListener("keydown", (event) => rove(event, buttons));
    return el("div", { class: "pg-bar" },
      el("div", { class: "pg-buttons", role: "toolbar", "aria-label": PEOPLE[person].bar }, buttons, made.map(({ described }) => described)),
      line,
    );
  }

  /* The pressing person, for a change the page did not press: Alex when only Alex's clone told something. */
  const actorOf = (observation) => (observation.events.length === 0 && observation.teammate_events.length > 0 ? "alex" : "you");

  function draw(panel, observation, person) {
    const text = JSON.stringify([panel.share.observed(observation), observation.buttons]);
    if (text === panel.drawnText) return;
    const before = panel.drawn;
    const who = person || actorOf(observation);
    const commands = before ? panel.share.pressed(before, observation, who) : [];
    const shown = panel.figure ? panel.figure.getAttribute("data-shown") : "you";
    const after = panel.share.observed(observation);
    const figure = panel.share.render(after, { person: before ? who : null, commands, shown });
    for (const [owner, views] of Object.entries(observation.buttons)) figure.querySelector(`[data-slot="${owner}"]`).append(bar(panel, owner, views));
    const hadFocus = panel.figure !== null && panel.figure.contains(document.activeElement);
    panel.host.replaceChildren(figure);
    panel.figure = figure;
    panel.drawn = observation;
    panel.drawnText = text;
    if (hadFocus) refocus(panel);
    if (before) panel.running = panel.share.play(figure, panel.share.observed(before), after, who, commands);
  }

  /* Focus back on the button pressed or focused last, now that the bars were drawn again. */
  function refocus(panel) {
    const { person, id } = panel.focus || {};
    const slot = panel.figure.querySelector(`[data-slot="${person}"]`);
    const node = slot && [...slot.querySelectorAll(".pg-button")].find((item) => item.getAttribute("data-id") === id);
    if (node) node.focus();
  }

  function busy(panel, on) {
    panel.pressing = on;
    panel.element.setAttribute("aria-busy", String(on));
    for (const node of panel.element.querySelectorAll(".pg-button, .pg-fix")) {
      if (on || node.hasAttribute("data-off")) node.setAttribute("aria-disabled", "true");
      else node.removeAttribute("aria-disabled");
    }
  }

  /* The fix the explanation offers: its button, as the pressing person's bar has it now. */
  function fixButton(panel, person, id) {
    const view = id && panel.drawn && (panel.drawn.buttons[person] || []).find((item) => item.id === id);
    return view && el("button", { type: "button", class: "btn btn-primary btn-small pg-fix", "data-off": view.off || null, "aria-disabled": offNow(panel, view) ? "true" : null, title: view.off || view.line, onclick: () => press(panel, person, view) }, view.label);
  }

  const typeLine = (panel, line) => el("div", { class: "command" },
    el("code", {}, line),
    el("button", { type: "button", class: "btn btn-ghost btn-small type-command", title: "Types the line at the prompt; press Enter in the terminal to run it", onclick: () => panel.onType(line) }, TYPE),
  );

  function result(panel, view) {
    const { press: pressed, explanation, fix, fix_line: fixLine } = view;
    const mine = pressed.person === "you";
    const parts = [
      el("p", { class: "pg-ran" },
        el("span", { class: "pg-who" }, PEOPLE[pressed.person].ran), " ",
        el("code", {}, pressed.command), " ",
        el("span", { class: `pg-status ${pressed.status === 0 ? "is-done" : "is-refused"}` }, statusWords(pressed)),
      ),
      mine && typeLine(panel, pressed.command),
      pressed.output !== "" && el("pre", { class: "pg-output" }, pressed.output),
      explanation && el("div", { class: "pg-explanation prose" }, Markup.render(explanation)),
      fixButton(panel, pressed.person, fix),
      mine && fixLine !== "" && typeLine(panel, fixLine),
    ];
    panel.box.replaceChildren(...parts.filter(Boolean));
    panel.box.hidden = false;
    const status = pressed.status === 0 ? "Done." : `${statusWords(pressed).replace(" (", ", ").replace(")", "")}.`;
    panel.announce.textContent = [`${PEOPLE[pressed.person].ran} ${pressed.command}.`, status, explanation ? Markup.plain(explanation) : ""].filter(Boolean).join(" ");
  }

  function refused(panel, reason) {
    panel.box.replaceChildren(el("p", { class: "pg-ran" }, el("span", { class: "pg-status is-refused" }, OFF)), el("p", {}, reason));
    panel.box.hidden = false;
    panel.announce.textContent = `${OFF} ${reason}`;
  }

  /* options: share (TimeShare), onPress(person, button id), onType(line). */
  function create({ share, onPress, onType }) {
    const host = el("div", { class: "pg-figure" });
    const box = el("section", { class: "pg-result", "aria-label": "The last press", hidden: true });
    const announce = el("p", { class: "sr-only", "aria-live": "polite" });
    const element = el("div", { class: "playground", "aria-busy": "false" }, host, box, announce);
    const panel = { share, onPress, onType, element, host, box, announce, figure: null, drawn: null, drawnText: null, running: [], pressing: false, focus: null, ids: 0 };

    return {
      element,

      /* Draws an observation (with `buttons`); after a press, `person` is who pressed. A change
         from the observation drawn before plays in that person's computer and GitHub. */
      draw: (observation, { person = null } = {}) => draw(panel, observation, person),

      /* While a press runs, every button is off and nothing else is pressed. */
      busy: (on) => busy(panel, on),

      /* Shows a press's result (PressView) and announces it. */
      result: (view) => result(panel, view),

      /* Shows why the server would not press a button that was off when it arrived. */
      refused: (reason) => refused(panel, reason),
    };
  }

  return { create };
})();
