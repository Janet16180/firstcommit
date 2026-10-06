"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const STATIC = path.join(__dirname, "..", "..", "src", "firstcommit", "web", "static");
const page = fs.readFileSync(path.join(STATIC, "index.html"), "utf8");
const scripts = [...page.matchAll(/<script src="\/static\/([^"]+)"><\/script>/g)].map((match) => match[1]);
const ours = scripts.filter((name) => fs.existsSync(path.join(STATIC, name)));
const names = (name, kind) => {
  const found = fs.readFileSync(path.join(STATIC, name), "utf8").match(new RegExp(`/\\* ${kind} ([^*]+)\\*/`));
  return found ? found[1].split(",").map((word) => word.trim()) : [];
};
const everyScript = fs.readdirSync(STATIC).filter((name) => name.endsWith(".js"));
const exporter = new Map(everyScript.flatMap((name) => names(name, "exported").map((global) => [global, name])));

test("the page loads every script another script needs, before it", () => {
  for (const [index, name] of ours.entries()) {
    for (const global of names(name, "global").filter((word) => exporter.has(word))) {
      const at = ours.indexOf(exporter.get(global));
      assert.ok(at >= 0 && at < index, `${name} needs ${global} from ${exporter.get(global)}, loaded before it`);
    }
  }
});

test("the page loads the time-travel theme's motions, places and map guide, and their stylesheets", () => {
  for (const name of ["theme-time.js", "theme-time-motion.js", "theme-time-places.js", "theme-time-guide.js"]) assert.ok(scripts.includes(name), name);
  for (const name of ["theme-time.css", "theme-time-share.css", "theme-time-guide.css"]) assert.match(page, new RegExp(`href="/static/${name}"`));
});
