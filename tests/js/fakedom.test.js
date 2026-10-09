"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { createDocument } = require("./fakedom");

function list() {
  const document = createDocument();
  for (const name of ["a", "b", "c"]) {
    const item = document.createElement("li");
    item.setAttribute("id", name);
    document.body.append(item);
  }
  return document.body.querySelectorAll("li");
}

test("querySelectorAll gives what a browser's NodeList offers: length, index, item, forEach and iteration", () => {
  const nodes = list();
  assert.equal(nodes.length, 3);
  assert.equal(nodes[1].getAttribute("id"), "b");
  assert.equal(nodes.item(2).getAttribute("id"), "c");
  assert.equal(nodes.item(3), null);
  const seen = [];
  nodes.forEach((node, index) => seen.push(`${index}${node.getAttribute("id")}`));
  assert.deepEqual(seen, ["0a", "1b", "2c"]);
  assert.deepEqual([...nodes].map((node) => node.getAttribute("id")), ["a", "b", "c"]);
});

test("querySelectorAll has no array methods, as in a browser, so code that needs them fails here too", () => {
  const nodes = list();
  for (const method of ["filter", "map", "find", "some", "every", "reduce", "includes", "indexOf", "slice"]) assert.equal(nodes[method], undefined, method);
  assert.equal(Array.isArray(nodes), false);
});

test("querySelectorAll and closest take a selector list, as a browser does", () => {
  const document = createDocument();
  const form = document.createElement("form");
  const choice = document.createElement("button");
  choice.setAttribute("class", "choice");
  const submit = document.createElement("button");
  form.append(submit);
  document.body.append(choice, form);
  assert.deepEqual([...document.body.querySelectorAll("button.choice, form button")], [choice, submit]);
  assert.equal(submit.closest("section, form"), form);
});

test("a selector the fake does not understand is refused by name, never matched loosely", () => {
  const document = createDocument();
  const root = document.createElement("div");
  root.append(document.createElement("span"));
  assert.throws(() => root.querySelector("[class~=lock]"), /does not support the selector part "\[class~=lock\]"/);
  assert.throws(() => root.querySelector("li:first-child"), /does not support/);
  assert.ok(root.querySelector("span"));
});

test("attribute values match quoted or not, by prefix with ^= or anywhere with *=, and :not() leaves out what it names", () => {
  const document = createDocument();
  const root = document.createElement("div");
  const tab = document.createElement("button");
  tab.setAttribute("role", "tab");
  tab.setAttribute("fill", "var(--z-va)");
  tab.classList.add("on");
  const other = document.createElement("button");
  other.setAttribute("role", "button");
  root.append(tab, other);
  assert.deepEqual(root.querySelectorAll("[role=tab]").length, 1);
  assert.deepEqual(root.querySelectorAll('[role="tab"]').length, 1);
  assert.equal(root.querySelector('[fill^="var("]'), tab);
  assert.equal(root.querySelector("[fill*=z-va]"), tab);
  assert.equal(root.querySelector("button:not(.on)"), other);
  assert.equal(root.querySelectorAll("button:not([role=tab])").length, 1);
  assert.equal(root.querySelector('button:not([fill="var(--z-va)"])'), other);
});
