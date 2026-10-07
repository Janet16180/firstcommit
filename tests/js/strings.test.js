"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const { STATIC, installBrowser, load } = require("./load");

installBrowser();
const { Strings } = load(["strings.js"], ["Strings"]);

const { en, es } = Strings.TABLES;
const placeholders = (entry) => JSON.stringify(entry).match(/\{\w+\}/g)?.sort() || [];
const ticks = (entry) => (JSON.stringify(entry).match(/`/g) || []).length;

test("every key exists in English and in Spanish, and nothing else", () => {
  assert.deepEqual(Object.keys(es).sort(), Object.keys(en).sort());
});

test("each Spanish string takes the same values, plural forms and commands as its English one", () => {
  for (const key of Object.keys(en)) {
    assert.deepEqual(placeholders(es[key]), placeholders(en[key]), key);
    assert.equal(typeof es[key], typeof en[key], key);
    assert.equal(ticks(es[key]), ticks(en[key]), key);
  }
});

test("every key a page script asks for exists", () => {
  const scripts = fs.readdirSync(STATIC).filter((name) => name.endsWith(".js") && !name.startsWith("theme-time"));
  const asked = scripts.flatMap((name) => [...fs.readFileSync(path.join(STATIC, name), "utf8").matchAll(/\b(?:t|parts)\("([\w.]+)"/g)].map((match) => match[1]));
  assert.ok(asked.length > 50, `only ${asked.length} keys asked for`);
  for (const key of asked) assert.ok(key in en, key);
});

test("a string takes its values, and a plural takes the form for its count", () => {
  Strings.use("en");
  assert.equal(Strings.t("map.review", { count: 1 }), "Review 1 card");
  assert.equal(Strings.t("map.review", { count: 4 }), "Review 4 cards");
  Strings.use("es");
  assert.equal(Strings.t("map.review", { count: 4 }), "Repasar 4 tarjetas");
  Strings.use("en");
});

test("a sentence with a command is cut at its backticks", () => {
  assert.deepEqual(Strings.parts("zones.empty.dock"), ["Empty dock. Load changes with ", { code: "git add" }, "."]);
});

test("an unknown language falls back to English, and an unknown key is a bug", () => {
  Strings.use("fr");
  assert.equal(Strings.language(), "en");
  assert.throws(() => Strings.t("no.such.key"), /no string/);
});
