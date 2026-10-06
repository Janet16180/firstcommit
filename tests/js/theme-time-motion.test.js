"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, record } = require("./load");

installBrowser();
const { RepoMap, TimeTheme, TimeMotion } = load(["dom.js", "map.js", "theme-time.js", "theme-time-motion.js"], ["RepoMap", "TimeTheme", "TimeMotion"]);
const theme = TimeTheme.map;
const { sizes } = theme;

const full = (name) => name.padEnd(40, "0");

/* A snapshot from commits newest first as [name, [parent names]], refs as [name, kind, target]. */
function snap({ commits, refs = [["main", "branch", commits[0][0]]], head = commits[0][0], branch = "main" }) {
  return {
    ...record("snapshots").one,
    head: full(head),
    branch,
    commits: commits.map(([name, parents], index) => ({
      hash: full(name), short: full(name).slice(0, 7), parents: parents.map(full), subject: `Commit ${name}`, author: "Alex Kim", time: 1000 - index,
    })),
    refs: refs.map(([name, kind, target]) => ({ name, kind, target: full(target) })),
  };
}

const drawn = (spec) => RepoMap.layout(snap(spec), { theme });

/* Renders `after`, plays the motions from `before`, and returns what each animate() call got. */
function played(before, after, reduced = false) {
  const calls = [];
  const figure = RepoMap.render(snap(after), { theme });
  const proto = Object.getPrototypeOf(figure);
  proto.animate = function (frames, timing) {
    const call = { node: this, frames, timing, onfinish: null };
    calls.push(call);
    return call;
  };
  proto.getTotalLength = () => 100;
  const animations = TimeMotion.play(figure, TimeMotion.motions(drawn(before), drawn(after), sizes), theme, reduced);
  delete proto.animate;
  delete proto.getTotalLength;
  return { figure, calls, animations };
}

const on = (calls, selector) => calls.filter((call) => call.node.closest(selector));
const ONE = { commits: [["b", ["a"]], ["a", []]] };
const TWO = { commits: [["c", ["b"]], ["b", ["a"]], ["a", []]] };

const motions = (before, after) => TimeMotion.motions(before, after, sizes);
const short = (hashes) => hashes.map((hash) => hash.replace(/0+$/, ""));
const slides = (motion) => Object.fromEntries(motion.slides.map(({ key, dx, dy }) => [key, [dx, dy]]));
const at = (map, name) => map.commits.find((commit) => commit.hash === full(name));

test("nothing moves on the first drawing, or when nothing changed", () => {
  const map = drawn({ commits: [["b", ["a"]], ["a", []]] });
  for (const motion of [motions(null, map), motions(map, map)]) {
    assert.deepEqual(motion, { born: [], appear: [], slides: [], texts: [], dial: null, ghosts: [], lines: [], lift: 0 });
  }
});

test("a new commit is born, and the branch tab, HEAD's tab and HEAD's dial slide up onto it from the old tip", () => {
  const before = drawn({ commits: [["b", ["a"]], ["a", []]] });
  const after = drawn({ commits: [["c", ["b"]], ["b", ["a"]], ["a", []]] });
  const motion = motions(before, after);
  assert.deepEqual(short(motion.born), ["c"]);
  assert.deepEqual(slides(motion), { head: [0, sizes.row], "branch:main": [0, sizes.row] });
  assert.deepEqual(motion.dial, { dx: 0, dy: sizes.row });
  assert.deepEqual(motion.lines, [{ from: full("c"), to: full("b") }]);
  assert.equal(motion.lift, 0);
});

test("a commit's hash and subject slide sideways when the tabs before them leave or arrive", () => {
  const before = drawn({ commits: [["b", ["a"]], ["a", []]] });
  const after = drawn({ commits: [["c", ["b"]], ["b", ["a"]], ["a", []]] });
  const tabsWidth = at(before, "b").labels.reduce((sum, label) => sum + label.width + sizes.chipPad, 0);
  assert.deepEqual(motions(before, after).texts, [{ hash: full("b"), dx: tabsWidth }]);
  assert.deepEqual(motions(after, before).texts, [{ hash: full("b"), dx: -tabsWidth }]);
});

test("a reset slides the tab back down and leaves a fading ghost of the commit no label reaches, lifting the map so the ghost shows", () => {
  const before = drawn({ commits: [["c", ["b"]], ["b", ["a"]], ["a", []]] });
  const after = drawn({ commits: [["b", ["a"]], ["a", []]] });
  const motion = motions(before, after);
  const b = at(after, "b");
  assert.deepEqual(slides(motion), { head: [0, -sizes.row], "branch:main": [0, -sizes.row] });
  assert.deepEqual(motion.dial, { dx: 0, dy: -sizes.row });
  const tabsWidth = at(before, "c").labels.reduce((sum, label) => sum + label.width + sizes.chipPad, 0);
  assert.deepEqual(motion.ghosts, [{
    hash: full("c"), short: full("c").slice(0, 7), subject: "Commit c", x: b.x, y: b.y - sizes.row, textX: after.textStart + tabsWidth, lane: 0, parent: { x: b.x, y: b.y }, replacedBy: null,
  }]);
  assert.equal(motion.lift, sizes.row);
  assert.deepEqual(motion.born, []);
});

test("a merge commit is born and its lines to both parents draw in, so the timelines visibly join", () => {
  const before = drawn({ commits: [["c", ["a"]], ["f", ["a"]], ["a", []]], refs: [["main", "branch", "c"], ["feature", "branch", "f"]] });
  const after = drawn({ commits: [["m", ["c", "f"]], ["c", ["a"]], ["f", ["a"]], ["a", []]], refs: [["main", "branch", "m"], ["feature", "branch", "f"]], head: "m" });
  const motion = motions(before, after);
  assert.deepEqual(short(motion.born), ["m"]);
  assert.deepEqual(motion.lines, [{ from: full("m"), to: full("c") }, { from: full("m"), to: full("f") }]);
  assert.deepEqual(Object.keys(slides(motion)).sort(), ["branch:main", "head"]);
});

test("a push moves origin/main from the commit it was on to the one pushed", () => {
  const before = drawn({ commits: [["c", ["b"]], ["b", ["a"]], ["a", []]], refs: [["main", "branch", "c"], ["origin/main", "remote", "b"]] });
  const after = drawn({ commits: [["c", ["b"]], ["b", ["a"]], ["a", []]], refs: [["main", "branch", "c"], ["origin/main", "remote", "c"]] });
  const motion = motions(before, after);
  assert.deepEqual(Object.keys(slides(motion)), ["remote:origin/main"]);
  const [dx, dy] = slides(motion)["remote:origin/main"];
  assert.equal(dy, sizes.row);
  assert.ok(dx < 0, "on b it was the first tab; on c it comes after HEAD and main");
  assert.equal(motion.dial, null);
  assert.deepEqual(motion.born, []);
});

test("switching branches makes HEAD's dial and tab travel to the other timeline's tip", () => {
  const commits = [["c", ["a"]], ["f", ["a"]], ["a", []]];
  const refs = [["main", "branch", "c"], ["feature", "branch", "f"]];
  const before = drawn({ commits, refs, head: "c", branch: "main" });
  const after = drawn({ commits, refs, head: "f", branch: "feature" });
  const motion = motions(before, after);
  const [c, f] = [at(after, "c"), at(after, "f")];
  assert.deepEqual(motion.dial, { dx: c.x - f.x, dy: c.y - f.y });
  assert.equal(slides(motion).head[1], c.y - f.y);
  assert.deepEqual(Object.keys(slides(motion)).sort(), ["branch:feature", "branch:main", "head"]);
  assert.equal(slides(motion)["branch:main"][1], 0, "main stays on c and only shifts sideways as HEAD's tab leaves");
});

test("a new branch or tag fades in where it is, instead of sliding", () => {
  const before = drawn({ commits: [["b", ["a"]], ["a", []]] });
  const after = drawn({ commits: [["b", ["a"]], ["a", []]], refs: [["main", "branch", "b"], ["v1", "tag", "b"], ["topic", "branch", "a"]] });
  const motion = motions(before, after);
  assert.deepEqual(motion.appear.sort(), ["branch:topic", "tag:v1"]);
  assert.deepEqual(motion.slides, []);
});

test("an amended commit fades out where its replacement is born, so the tab stays put", () => {
  const before = drawn({ commits: [["c", ["b"]], ["b", ["a"]], ["a", []]] });
  const after = drawn({ commits: [["d", ["b"]], ["b", ["a"]], ["a", []]] });
  const motion = motions(before, after);
  const d = at(after, "d");
  assert.deepEqual(short(motion.born), ["d"]);
  assert.deepEqual(motion.ghosts.map(({ hash, x, y, replacedBy }) => [hash, x, y, replacedBy]), [[full("c"), d.x, d.y, full("d")]]);
  assert.deepEqual(motion.slides, []);
  assert.equal(motion.dial, null);
  assert.equal(motion.lift, 0);
});

test("a tab whose old commit cannot be placed on the new map fades in instead of sliding", () => {
  const before = drawn({ commits: [["x", ["w"]], ["w", []]] });
  const after = drawn({ commits: [["y", []]] });
  const motion = motions(before, after);
  assert.deepEqual(motion.ghosts, []);
  assert.deepEqual(motion.slides, []);
  assert.deepEqual(motion.appear.sort(), ["branch:main", "head"]);
  assert.equal(motion.dial, null);
});

test("every motion comes from a difference between the two drawings", () => {
  const before = drawn({ commits: [["c", ["b"]], ["b", ["a"]], ["a", []]], refs: [["main", "branch", "c"], ["v1", "tag", "a"]] });
  const after = drawn({ commits: [["d", ["c"]], ["c", ["b"]], ["b", ["a"]], ["a", []]], refs: [["main", "branch", "d"], ["v1", "tag", "a"]] });
  const motion = motions(before, after);
  assert.ok(!motion.slides.some((slide) => slide.key === "tag:v1"), "the tag did not move");
  assert.ok(!motion.appear.includes("tag:v1"));
  assert.deepEqual(short(motion.born), ["d"]);
});

test("under reduced motion nothing plays", () => {
  const { calls, animations } = played(ONE, TWO, true);
  assert.deepEqual(calls, []);
  assert.deepEqual(animations, []);
});

test("a new commit's save point grows in while the tabs and HEAD's dial start from the old tip", () => {
  const { calls } = played(ONE, TWO);
  const born = on(calls, `[data-hash="${full("c")}"]`).filter((call) => call.node.getAttribute("class") === "tt-save");
  assert.equal(born.length, 1);
  assert.match(born[0].frames[0].transform, /scale/);
  const tab = on(calls, '[data-label="branch:main"]');
  assert.equal(tab[0].frames[0].transform, `translate(0px, ${sizes.row}px)`);
  const dial = on(calls, ".tt-now");
  assert.equal(dial[0].frames[0].transform, `translate(0px, ${sizes.row}px)`);
  assert.equal(dial[0].frames[1].transform, "translate(0px, 0px)");
});

test("a reset draws a ghost of the dropped commit that fades and is removed when done, with the map lifted meanwhile", () => {
  const { figure, calls } = played(TWO, ONE);
  const ghosts = figure.querySelector(".tt-ghosts");
  assert.ok(ghosts);
  assert.equal(ghosts.querySelectorAll(".tt-ghost").length, 1);
  assert.equal(ghosts.querySelector(".map-hash").textContent, "c000000");
  assert.equal(ghosts.querySelector(".map-subject").textContent, "Commit c");
  const fade = calls.find((call) => call.node === ghosts);
  assert.equal(fade.frames[1].opacity, 0);
  fade.onfinish();
  assert.equal(figure.querySelector(".tt-ghosts"), null);
  const lifted = calls.filter((call) => call.frames[0].marginTop === `${sizes.row}px`);
  assert.deepEqual(lifted.map((call) => call.node.getAttribute("class")), ["map-graph"]);
});

test("the merge's new line draws in from the merged branch's tip", () => {
  const before = { commits: [["c", ["a"]], ["f", ["a"]], ["a", []]], refs: [["main", "branch", "c"], ["feature", "branch", "f"]] };
  const after = { commits: [["m", ["c", "f"]], ["c", ["a"]], ["f", ["a"]], ["a", []]], refs: [["main", "branch", "m"], ["feature", "branch", "f"]], head: "m" };
  const { calls } = played(before, after);
  const join = calls.find((call) => call.node.getAttribute("data-from") === full("m") && call.node.getAttribute("data-to") === full("f"));
  assert.deepEqual(join.frames.map((frame) => frame.strokeDashoffset), [-100, 0]);
});

test("every motion is over within 600 ms", () => {
  const cases = [[ONE, TWO], [TWO, ONE], [{ commits: [["c", ["a"]], ["f", ["a"]], ["a", []]], refs: [["main", "branch", "c"], ["feature", "branch", "f"]] }, { commits: [["m", ["c", "f"]], ["c", ["a"]], ["f", ["a"]], ["a", []]], refs: [["main", "branch", "m"], ["feature", "branch", "f"]], head: "m" }]];
  for (const [before, after] of cases) {
    for (const { timing } of played(before, after).calls) assert.ok((timing.delay || 0) + timing.duration <= 600, JSON.stringify(timing));
  }
});

test("a replaced commit fades out before its replacement appears in the same place, so their texts never overlap", () => {
  const { figure, calls } = played(TWO, { commits: [["d", ["b"]], ["b", ["a"]], ["a", []]] });
  const end = (call) => (call.timing.delay || 0) + call.timing.duration;
  const out = calls.find((call) => call.node === figure.querySelector(".tt-ghosts"));
  const newText = on(calls, `[data-hash="${full("d")}"]`).filter((call) => call.node.getAttribute("class") === "map-hash");
  assert.ok(end(out) <= newText[0].timing.delay, `${end(out)} > ${newText[0].timing.delay}`);
});

test("when the drawing gains a line, tabs and texts start exactly where they were drawn, so they never overlap on the way", () => {
  const before = drawn({ commits: [["b", ["a"]], ["a", []]], refs: [["main", "branch", "b"], ["origin/main", "remote", "b"]] });
  const after = drawn({ commits: [["c", ["b"]], ["b", ["a"]], ["a", []]], refs: [["main", "branch", "b"], ["origin/main", "remote", "c"]], head: "b" });
  assert.ok(after.textStart > before.textStart, "the fetched commit draws a second line");
  const motion = motions(before, after);
  const tabX = (map, hash, kind) => {
    const commit = at(map, hash);
    let x = map.textStart;
    for (const label of commit.labels) {
      if (label.kind === kind) return x;
      x += label.width + sizes.chipPad;
    }
    return null;
  };
  const slide = motion.slides.find((move) => move.key === "remote:origin/main");
  assert.equal(tabX(after, "c", "remote") + slide.dx, tabX(before, "b", "remote"));
  const text = motion.texts.find((move) => move.hash === full("b"));
  const textX = (map, name) => at(map, name).labels.reduce((x, label) => x + label.width + sizes.chipPad, map.textStart);
  assert.equal(textX(after, "b") + text.dx, textX(before, "b"));
});
