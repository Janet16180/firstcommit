"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { html, makeEvent, SVG_NS } = require("./fakedom");
const { installBrowser, load } = require("./load");

installBrowser();
const { Dom } = load(["dom.js"], ["Dom"]);

test("an element gets its class, attributes and children in order", () => {
  const node = Dom.el("p", { class: "lead", title: "a tip" }, "Run ", Dom.el("code", {}, "git status"), " now.");
  assert.equal(html(node), '<p class="lead" title="a tip">Run <code>git status</code> now.</p>');
});

test("missing children are skipped and lists of children are flattened", () => {
  const node = Dom.el("ul", {}, null, [Dom.el("li", {}, "a"), [Dom.el("li", {}, "b")]], undefined, false);
  assert.equal(html(node), "<ul><li>a</li><li>b</li></ul>");
});

test("text children stay text, whatever they contain", () => {
  assert.equal(html(Dom.el("p", {}, "<b>not bold</b>", 3)), "<p>&lt;b&gt;not bold&lt;/b&gt;3</p>");
});

test("on-attributes become listeners, not attributes", () => {
  let clicks = 0;
  const button = Dom.el("button", { type: "button", onclick: () => (clicks += 1) }, "Go");
  button.dispatchEvent(makeEvent("click"));
  assert.equal(clicks, 1);
  assert.equal(button.hasAttribute("onclick"), false);
});

test("true attributes are present and empty, false or missing ones are left out", () => {
  const input = Dom.el("input", { disabled: true, hidden: false, placeholder: null, "aria-label": "Answer" });
  assert.equal(html(input), '<input disabled aria-label="Answer"></input>');
});

test("svg elements are made in the svg namespace with their attributes", () => {
  const circle = Dom.svg("circle", { class: "commit", cx: 10, cy: 20, r: 6 });
  assert.equal(circle.namespaceURI, SVG_NS);
  assert.equal(html(Dom.svg("g", {}, circle)), '<g><circle class="commit" cx="10" cy="20" r="6"></circle></g>');
});

test("clear empties an element", () => {
  const list = Dom.el("ul", {}, Dom.el("li", {}, "a"));
  Dom.clear(list);
  assert.equal(html(list), "<ul></ul>");
});
