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

const styles = [...page.matchAll(/<link rel="stylesheet" href="\/static\/([^"]+)">/g)].map((match) => match[1]);

test("the page wears the Orbit look: the shipped fonts, the art's styles and the design's stylesheet last, over app.css", () => {
  assert.deepEqual(styles.slice(styles.indexOf("app.css")), ["app.css", "fonts.css", "art-style.css", "art-infographics.css", "orbit.css"]);
});

test("the page loads nothing from the network", () => {
  assert.doesNotMatch(page, /(src|href)="(https?:)?\/\//);
});

test("the old level page, its lessons and the time theme are gone", () => {
  const old = ["home.js", "level.js", "practice.js", "live.js", "lesson.js", "quest.js", "challenge.js", "celebrate.js", "playground.js", "map.js"];
  const theme = ["theme-time.js", "theme-time-motion.js", "theme-time-places.js", "theme-time-share.js", "theme-time-guide.js", "theme-time.css", "theme-time-share.css", "theme-time-guide.css"];
  for (const name of [...old, ...theme]) assert.ok(!fs.existsSync(path.join(STATIC, name)), name);
});

test("the page loads the map screen, the level screen and their parts", () => {
  for (const name of ["places.js", "art-pixels.js", "art-sprites.js", "art-sky.js", "art-scenes.js", "typed.js", "scene.js", "art-infographics.js", "infographic-text.js", "field-guide.js", "zones.js", "zone-panel.js", "mission.js", "comms.js", "completion.js", "art-moments.js", "moment-layer.js", "view-tabs.js", "strip.js", "sides.js", "tape.js", "births.js", "chain.js", "folder-row.js", "desk.js", "move-log.js", "target-chart.js", "git-graph.js", "pictures.js", "level-screen.js", "starmap.js", "dev.js"]) assert.ok(scripts.includes(name), name);
});
