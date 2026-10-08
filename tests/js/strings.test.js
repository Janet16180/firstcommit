"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const { STATIC, installBrowser, load } = require("./load");

installBrowser();
const { Strings, InfographicText } = load(["strings.js", "infographic-text.js"], ["Strings", "InfographicText"]);

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

test("a group gathers the strings under a prefix, by the rest of their key", () => {
  Strings.use("es");
  const group = Strings.group("sceneCaption.planet.");
  assert.equal(group.folder, "una carpeta común");
  assert.equal(group.question, "¿Git la conoce?");
  assert.deepEqual(Object.keys(group).sort(), ["folder", "question"]);
  Strings.use("en");
});

/* The forms docs/i18n-glossary.md rules out live in engine's tests/test_translations.py (NEVER);
   the page's Spanish keeps the same list. */
const TRANSLATIONS = path.join(STATIC, "..", "..", "..", "..", "tests", "test_translations.py");
const glossary = fs.existsSync(TRANSLATIONS) ? fs.readFileSync(TRANSLATIONS, "utf8") : "";
const never = () => [...glossary.split("NEVER = {")[1].split("\n}")[0].matchAll(/^\s+"([^"]+)":/gm)].map((match) => match[1]);
const prose = (text) => text.replace(/`[^`]*`/g, " ").replace(/\bgit [\w\- <>.]+/g, " ");

/* Every Spanish text of the page: the table's strings (plurals included) and the guide's `es` words. */
const guide = (value) => {
  if (!value || typeof value !== "object") return [];
  if ("es" in value) return [value.es];
  return Object.values(value).flatMap(guide);
};
const SPANISH = [...Object.values(es).flatMap((entry) => (typeof entry === "string" ? [entry] : Object.values(entry))), ...guide(InfographicText)];

test("the page's Spanish never uses a form the glossary rules out", { skip: !glossary.includes("NEVER = {") && "engine's glossary list has not merged yet" }, () => {
  const texts = SPANISH;
  const found = never().flatMap((word) => texts.filter((text) => new RegExp(`(?<![\\p{L}])${word}(?![\\p{L}])`, "u").test(prose(text))).map((text) => `${word}: ${text}`));
  assert.deepEqual(found, []);
});

test("the page's Spanish uses the glossary's words for the working folder (la carpeta), history, a snapshot and untracked", () => {
  const texts = SPANISH.map(prose);
  for (const word of ["directorio de trabajo", "historial", "foto del proyecto", "untracked", "modified", "staged", "committed", "el carpeta", "del carpeta", "al carpeta"]) {
    assert.deepEqual(texts.filter((text) => text.includes(word)), [], word);
  }
});
