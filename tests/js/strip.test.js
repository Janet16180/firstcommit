"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

installBrowser();
const { Strip, Strings } = load(["dom.js", "strings.js", "art-pixels.js", "art-sprites.js", "strip.js"], ["Strip", "Strings"]);

const file = (path, state = "saved") => ({ path, state });
const capsule = (hash, author = "You") => ({ hash, short: hash, subject: hash, author, parents: [], lane: 0, revert: false, labels: [] });
const reading = (fields = {}) => ({ repository: true, workshop: [], dock: [], vault: [], remote: null, crew: null, ...fields });
const card = (strip, zone) => strip.element.querySelector(`.strip-card[data-zone="${zone}"]`);
const texts = (node, selector) => [...node.querySelectorAll(selector)].map((item) => item.textContent);

test("each card shows up to three items and folds the rest into a count", () => {
  const strip = Strip.create({ onExpand: () => {} });
  strip.update(reading({ workshop: ["a", "b", "c", "d", "e"].map((name) => file(`${name}.txt`)), vault: ["c1", "c2", "c3", "c4"].map((hash) => capsule(hash)) }));
  assert.deepEqual(texts(card(strip, "workshop"), ".strip-file"), ["a.txt", "b.txt", "c.txt"]);
  assert.equal(card(strip, "workshop").querySelector(".strip-more").textContent, "+2");
  assert.equal(card(strip, "vault").querySelectorAll(".strip-capsule").length, 3);
  assert.equal(card(strip, "vault").querySelector(".strip-more").textContent, "+1");
});

test("the strip hides hashes and branch names on purpose: a capsule is only its block, in its author's colour", () => {
  const strip = Strip.create({ onExpand: () => {} });
  strip.update(reading({ vault: [{ ...capsule("abc1234", "Alex"), labels: [{ text: "HEAD → main", kind: "head" }] }] }));
  const vault = card(strip, "vault");
  assert.doesNotMatch(vault.textContent, /abc1234|main/);
  assert.equal(vault.querySelector(".strip-capsule").dataset.author, "alex");
});

test("an edited or new file carries the tag that says it is on no branch yet", () => {
  const strip = Strip.create({ onExpand: () => {} });
  strip.update(reading({ workshop: [file("notes.txt", "edited"), file("probe.txt", "new"), file("README.md")] }));
  const tagged = [...card(strip, "workshop").querySelectorAll(".strip-file")].filter((node) => node.querySelector(".strip-tag")).map((node) => node.firstChild.textContent);
  assert.deepEqual(tagged, ["notes.txt", "probe.txt"]);
  assert.equal(card(strip, "workshop").querySelector(".strip-tag").textContent, "on no branch");
});

test("every card badges how many items it holds, and a card that is off says so", () => {
  const strip = Strip.create({ onExpand: () => {} });
  strip.update(reading({ workshop: [file("a.txt")], dock: [], vault: null, repository: false }));
  assert.equal(card(strip, "workshop").querySelector(".strip-count").textContent, "1");
  assert.equal(card(strip, "dock").querySelector(".strip-count").textContent, "0");
  assert.ok(card(strip, "vault").classList.contains("is-off"));
  assert.equal(card(strip, "remote"), null);
});

test("a level with a mothership has its card; tapping any card asks to expand it back into its zone", () => {
  const asked = [];
  const strip = Strip.create({ onExpand: (zone) => asked.push(zone) });
  strip.update(reading({ remote: [capsule("m1")] }));
  assert.deepEqual([...strip.element.querySelectorAll(".strip-card")].map((node) => node.dataset.zone), ["workshop", "dock", "vault", "remote"]);
  card(strip, "remote").click();
  card(strip, "workshop").click();
  assert.deepEqual(asked, ["remote", "workshop"]);
});

test("the cards speak the page's language", () => {
  Strings.use("es");
  try {
    const strip = Strip.create({ onExpand: () => {} });
    strip.update(reading({ workshop: [file("notes.txt", "edited")] }));
    assert.match(card(strip, "workshop").textContent, /Taller/);
    assert.match(card(strip, "workshop").textContent, /en ningún branch/);
  } finally {
    Strings.use("en");
  }
});
