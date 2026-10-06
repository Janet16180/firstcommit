"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, record } = require("./load");

const document = installBrowser();
const { TimeGuide } = load(["dom.js", "map.js", "theme-time.js", "theme-time-motion.js", "theme-time-guide.js"], ["TimeGuide"]);

/* A storage like localStorage, or one that throws like a blocked one. */
function storage({ blocked = false, items = {} } = {}) {
  const kept = new Map(Object.entries(items));
  const refuse = () => {
    throw new Error("storage is blocked");
  };
  return blocked ? { getItem: refuse, setItem: refuse } : { getItem: (key) => kept.get(key) ?? null, setItem: (key, value) => kept.set(key, value), kept };
}

const full = (name) => name.padEnd(40, "0");

/* A snapshot: commits newest first as [name, [parents]], refs as [name, kind, target]. */
function repo({ commits = [], refs = [], branch = "main", head = commits.length ? commits[0][0] : null, bare = false }) {
  return {
    ...record("snapshots").one,
    bare,
    head: bare || head === null ? null : full(head),
    branch,
    commits: commits.map(([name, parents], index) => ({
      hash: full(name), short: full(name).slice(0, 7), parents: parents.map(full), subject: `Commit ${name}`, author: "Sam Lee", time: 1000 - index,
    })),
    refs: refs.map(([name, kind, target]) => ({ name, kind, target: full(target) })),
    files: [],
  };
}

const TWO = [["b", ["a"]], ["a", []]];
const THREE = [["c", ["b"]], ...TWO];
const FIGURES = {
  branch: {
    before: repo({ commits: TWO, refs: [["idea", "branch", "b"], ["main", "branch", "b"]], branch: "idea" }),
    after: repo({ commits: THREE, refs: [["idea", "branch", "c"], ["main", "branch", "b"]], branch: "idea" }),
    transcript: [{ command: "git commit -m 'Sketch an idea'", output: "[idea c000000] Sketch an idea\n" }],
  },
  archive: {
    before: repo({ commits: TWO.slice(1), refs: [["main", "branch", "a"]], bare: true }),
    after: repo({ commits: TWO, refs: [["main", "branch", "b"]], bare: true }),
    transcript: [{ command: "cd ../../project", output: "" }, { command: "git push", output: "To ../github/project.git\n" }, { command: "cd ../github/project.git", output: "" }],
  },
};

const section = (id) => [...document.querySelectorAll("dialog.tt-guide section")].find((node) => node.getAttribute("data-section") === id);
const plain = (text) => text.replaceAll("`", "").replaceAll("**", "");

function opened({ figures = FIGURES, reducedMotion = true } = {}) {
  document.body.replaceChildren();
  global.matchMedia = (query) => ({ matches: query.includes("reduce") ? reducedMotion : false, addEventListener() {} });
  const guide = TimeGuide.create({ storage: storage(), figures });
  guide.button().click();
  return document.querySelector("dialog.tt-guide");
}

/* Records every animate() call while `run(calls)` runs; each animation can be paused and played. */
function animating(run) {
  const calls = [];
  const proto = Object.getPrototypeOf(document.createElement("div"));
  proto.animate = function (frames, timing) {
    const call = { node: this, frames, timing, onfinish: null, paused: false, pause() { this.paused = true; }, play() { this.paused = false; }, cancel() {} };
    calls.push(call);
    return call;
  };
  proto.getTotalLength = () => 100;
  try {
    return { result: run(calls), calls };
  } finally {
    delete proto.animate;
    delete proto.getTotalLength;
  }
}

/* A stand-in IntersectionObserver whose callbacks a test calls by hand. */
function observing() {
  const observers = [];
  global.IntersectionObserver = class {
    constructor(callback) {
      this.callback = callback;
      this.nodes = [];
      this.disconnected = false;
      observers.push(this);
    }

    observe(node) {
      this.nodes.push(node);
    }

    disconnect() {
      this.disconnected = true;
    }
  };
  return observers;
}

test("the guide pairs each picture with Git's word, built on the rule that the past never changes", () => {
  const titles = TimeGuide.SECTIONS.map((part) => part.title);
  assert.deepEqual(titles, [
    "Save point = commit", "Lines = parents", "Timeline = branch", "Now = HEAD", "Now on no branch = detached HEAD",
    "Timelines joining = merge commit", "Milestone = tag", "Shared archive = remote", "Last seen in the archive = remote-tracking branch",
    "Coming later: undoing and rewriting, in the same words",
  ]);
  assert.match(TimeGuide.INTRO, /\*\*the past never changes\.\*\*/);
});

test("detached HEAD has its own section, holding the detached rule moved out of Now = HEAD", () => {
  const find = (id) => TimeGuide.SECTIONS.find((part) => part.id === id);
  assert.ok(find("now").points.every((point) => !point.startsWith("Detached HEAD")));
  const [rule, ...others] = find("detached").points;
  assert.ok(rule.startsWith("Detached HEAD: HEAD names a commit directly, not a branch"));
  assert.deepEqual(others, []);
});

test("every section with a picture has a caption with its Git word in bold", () => {
  for (const part of TimeGuide.SECTIONS.filter((entry) => entry.mark)) assert.match(part.caption, /\*\*[^*]+\*\*/, part.title);
});

test("the button opens the guide in a dialog that starts on its close button", () => {
  const dialog = opened();
  assert.ok(dialog.open);
  assert.equal(document.activeElement, dialog.querySelector(".tt-guide-close"));
  assert.match(dialog.textContent, /How to read the map/);
  assert.equal(dialog.querySelectorAll("h3").length, TimeGuide.SECTIONS.length);
});

test("closing the guide removes it from the page", () => {
  opened();
  document.querySelector(".tt-guide-close").click();
  assert.equal(document.querySelector("dialog.tt-guide"), null);
});

test("Git's words and commands are shown as code and Git's words in captions in bold, with no markup left over", () => {
  const dialog = opened();
  const code = [...dialog.querySelectorAll("code")].map((node) => node.textContent);
  for (const word of ["git switch other", "origin/main", "git rebase"]) assert.ok(code.some((text) => text.includes(word)), word);
  assert.deepEqual(dialog.querySelector(".tt-guide-intro strong").textContent, "the past never changes.");
  assert.ok(!dialog.textContent.includes("`") && !dialog.textContent.includes("**"));
});

test("a section shows the repository after the change, drawn small, with the git command that made it", () => {
  opened();
  const branch = section("branch");
  const map = branch.querySelector(".tt-guide-figure .repo-map");
  assert.ok(map.querySelector('[data-label="branch:idea"]'));
  assert.equal(map.querySelector(".tt-key"), null, "a small map, without the key");
  assert.deepEqual([...branch.querySelectorAll(".tt-guide-figure figcaption code")].map((node) => node.textContent), ["$ git commit -m 'Sketch an idea'"]);
});

test("the archive's figure is the practice copy: named as GitHub, with no now mark, showing only the git command", () => {
  opened();
  const archive = section("archive");
  assert.match(archive.querySelector(".tt-guide-place").textContent, /GitHub \(the practice copy\)/);
  assert.equal(archive.querySelector(".tt-now"), null);
  assert.deepEqual([...archive.querySelectorAll(".tt-guide-figure figcaption code")].map((node) => node.textContent), ["$ git push"]);
});

test("a section's caption names the Git word in bold, and its checked text folds under More, word for word", () => {
  opened();
  const branch = section("branch");
  const part = TimeGuide.SECTIONS.find((entry) => entry.id === "branch");
  assert.equal(branch.querySelector(".tt-guide-caption strong").textContent, "branch");
  const more = branch.querySelector("details");
  assert.equal(more.open, false);
  assert.equal(more.querySelector("summary").textContent, "More");
  assert.equal(more.querySelector(".tt-guide-picture").textContent, plain(part.picture));
  assert.deepEqual([...more.querySelectorAll("li")].map((item) => item.textContent), part.points.map(plain));
});

test("a section with no figure, the preview or one not given, shows its caption and text only", () => {
  opened();
  for (const id of ["later", "tag"]) {
    assert.equal(section(id).querySelector(".tt-guide-figure"), null, id);
    assert.ok(section(id).querySelector(".tt-guide-caption"), id);
  }
});

test("a figure plays its change the first time it comes into view, from the drawing before", () => {
  const observers = observing();
  const { calls } = animating(() => opened({ reducedMotion: false }));
  const inBranch = (call) => section("branch").contains(call.node);
  assert.ok(calls.some(inBranch) && calls.every((call) => call.paused), "drawn as before, waiting");
  const watcher = observers.find((observer) => observer.nodes.includes(section("branch").querySelector(".tt-guide-figure")));
  watcher.callback([{ isIntersecting: true, target: watcher.nodes[0] }]);
  assert.ok(calls.filter(inBranch).every((call) => !call.paused), "plays once in view");
  assert.ok(calls.filter((call) => !inBranch(call)).every((call) => call.paused), "the others still wait");
  assert.ok(watcher.disconnected, "only the first time");
  delete global.IntersectionObserver;
});

test("without IntersectionObserver, the figures play as the guide opens", () => {
  const { calls } = animating(() => opened({ reducedMotion: false }));
  assert.ok(calls.length > 0 && calls.every((call) => !call.paused));
});

test("Play again draws the figure anew and plays its change again", () => {
  animating((calls) => {
    opened({ reducedMotion: false });
    const before = section("branch").querySelector(".repo-map");
    const played = calls.length;
    section("branch").querySelector(".tt-guide-replay").click();
    assert.notEqual(section("branch").querySelector(".repo-map"), before);
    assert.ok(calls.length > played);
  });
});

test("under reduced motion the figures are still and offer no Play again", () => {
  const { calls } = animating(() => opened({ reducedMotion: true }));
  assert.deepEqual(calls, []);
  assert.equal(document.querySelector(".tt-guide-replay"), null);
  assert.ok(section("branch").querySelector(".repo-map"));
});

test("the button says it is new until the guide has been opened once, in every key on the page", () => {
  const kept = storage();
  document.body.replaceChildren();
  const guide = TimeGuide.create({ storage: kept });
  const [first, second] = [guide.button(), guide.button()];
  document.body.append(first, second);
  assert.ok(first.classList.contains("is-new") && second.classList.contains("is-new"));
  first.click();
  assert.ok(!first.classList.contains("is-new") && !second.classList.contains("is-new"));
  assert.ok(!guide.button().classList.contains("is-new"));
  assert.ok(!TimeGuide.create({ storage: kept }).button().classList.contains("is-new"), "remembered for the next visit");
});

test("with storage blocked the guide still opens, and the mark simply shows again next time", () => {
  document.body.replaceChildren();
  const guide = TimeGuide.create({ storage: storage({ blocked: true }) });
  const button = guide.button();
  assert.ok(button.classList.contains("is-new"));
  button.click();
  assert.ok(document.querySelector("dialog.tt-guide").open);
  assert.ok(TimeGuide.create({ storage: storage({ blocked: true }) }).button().classList.contains("is-new"));
});
