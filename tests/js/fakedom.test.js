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
