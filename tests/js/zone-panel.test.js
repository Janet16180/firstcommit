"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { createClock, installBrowser, load, record } = require("./load");

installBrowser();
const { ZonePanel } = load(["dom.js", "art-pixels.js", "art-sprites.js", "typed.js", "zones.js", "zone-panel.js"], ["ZonePanel"]);

const observe = (project, github = null) => ({ ...record("observation"), project, github });
const zone = (panel, name) => panel.element.querySelector(`.zone[data-zone="${name}"]`);
/* The item with a fly-by key, found without a selector (a file name may hold any character). */
const keyed = (node, key) => [...node.querySelectorAll("[data-key]")].find((item) => item.dataset.key === key);
const texts = (node, selector) => [...node.querySelectorAll(selector)].map((item) => item.textContent);

test("the four zones are named in the design's order, with the git name under each", () => {
  const panel = ZonePanel.create();
  assert.deepEqual(texts(panel.element, ".z-head h3"), ["Workshop", "Cargo dock", "Vault", "Mothership"]);
  assert.deepEqual(texts(panel.element, ".z-head small"), ["working folder", "staging area", "local repository", "remote repository"]);
  assert.equal(panel.element.getAttribute("aria-label"), "Your repository");
});

test("drawn arrows between the zones name the commands that move work along", () => {
  const panel = ZonePanel.create();
  assert.deepEqual(texts(panel.element, ".fl span"), ["git add", "git commit", "git push", "git pull"]);
  assert.deepEqual([...panel.element.querySelectorAll(".fl")].map((arrow) => arrow.dataset.arrow), ["add", "commit", "push", "pull"]);
  assert.equal(panel.element.querySelectorAll(".fl svg.art-icon").length, 4);
  assert.ok(panel.element.querySelector(".fl.is-back"));
});

test("a folder without a repository lights only the workshop, and the other zones say why they are off", () => {
  const panel = ZonePanel.create();
  panel.update(observe(record("snapshots").folder));
  assert.equal(zone(panel, "workshop").classList.contains("is-dormant"), false);
  for (const name of ["dock", "vault", "remote"]) assert.ok(zone(panel, name).classList.contains("is-dormant"), name);
  assert.match(zone(panel, "dock").textContent, /git init/);
  assert.deepEqual(texts(zone(panel, "workshop"), ".fname"), ["notes.txt"]);
  assert.equal(zone(panel, "workshop").querySelector(".file").dataset.state, "none");
  assert.equal(zone(panel, "workshop").querySelector(".z-count").textContent, "1");
  assert.equal(zone(panel, "dock").querySelector(".z-count").textContent, "–");
});

test("files show their state with a tag, and staged changes sit on the dock", () => {
  const panel = ZonePanel.create();
  panel.update(observe({ ...record("snapshots").one, files: record("files") }));
  const workshop = zone(panel, "workshop");
  const newFile = [...workshop.querySelectorAll(".file")].find((item) => item.textContent.startsWith("new.txt"));
  assert.equal(newFile.dataset.state, "new");
  assert.equal(newFile.querySelector(".ftag").textContent, "new");
  assert.deepEqual(texts(zone(panel, "dock"), ".fname"), ["added.txt", "staged.txt", "removed.txt", "staged-link"]);
  assert.equal(zone(panel, "dock").querySelector(".z-count").textContent, "4");
});

test("the vault lists HEAD's history as capsules with their labels and messages", () => {
  const panel = ZonePanel.create();
  panel.update(observe(record("observation").project));
  const vault = zone(panel, "vault");
  assert.equal(vault.querySelectorAll(".cap").length, Number(vault.querySelector(".z-count").textContent));
  assert.equal(vault.querySelector(".cap .chash").textContent, "547cd2b");
  assert.equal(vault.querySelector(".cap .ref").textContent, "HEAD → feature");
  assert.equal(vault.querySelector(".cap .cmsg").textContent, "Add a greeting to the readme");
});

test("empty zones say what fills them", () => {
  const panel = ZonePanel.create();
  panel.update(observe(record("snapshots").one, record("snapshots").unborn));
  assert.match(zone(panel, "dock").querySelector(".zone-empty").textContent, /git add/);
  assert.match(zone(panel, "remote").querySelector(".zone-empty").textContent, /git push/);
  assert.equal(zone(panel, "remote").classList.contains("is-dormant"), false);
});

test("the legend names every state a file can show", () => {
  const panel = ZonePanel.create();
  assert.deepEqual(texts(panel.element, ".legend li"), ["no repository", "new (untracked)", "edited (modified)", "on the dock (staged)", "saved (committed)"]);
});

test("an observation that changed nothing leaves the zones' nodes in place", () => {
  const panel = ZonePanel.create();
  panel.update(observe(record("observation").project));
  const first = zone(panel, "vault").querySelector(".cap");
  panel.update(observe(record("observation").project));
  assert.equal(zone(panel, "vault").querySelector(".cap"), first);
});

const typed = (...lines) => lines.map((line) => ({ line, status: 0 }));

test("typing git init wakes the dock and the vault for a moment", async () => {
  const clock = createClock();
  const panel = ZonePanel.create({ timers: clock });
  panel.update(observe(record("snapshots").folder));
  panel.update({ ...observe(record("snapshots").unborn), commands: typed("git init") });
  assert.ok(zone(panel, "dock").classList.contains("is-waking"));
  assert.ok(zone(panel, "vault").classList.contains("is-waking"));
  await clock.advance(1600);
  assert.equal(zone(panel, "dock").classList.contains("is-waking"), false);
});

test("staging a file with git add lights the add arrow, and every item carries the key it flies by", () => {
  const clock = createClock();
  const panel = ZonePanel.create({ timers: clock });
  const project = record("snapshots").one;
  panel.update(observe(project));
  const file = { ...project.files[0], index: "new-version", index_change: "modified" };
  panel.update({ ...observe({ ...project, files: [file] }), commands: typed("git add hello.txt") });
  assert.ok(panel.element.querySelector('.fl[data-arrow="add"]').classList.contains("is-lit"));
  assert.ok(keyed(zone(panel, "dock"), "dock:hello.txt"));
  assert.ok(keyed(zone(panel, "workshop"), "workshop:hello.txt"));
  assert.ok(keyed(zone(panel, "vault"), `vault:${project.head}`));
});

test("the first drawing animates nothing", () => {
  const panel = ZonePanel.create({ timers: createClock() });
  panel.update({ ...observe(record("snapshots").unborn), commands: typed("git init") });
  assert.equal(panel.element.querySelector(".is-lit, .is-waking"), null);
});

const capsuleCommit = (hash, parents = []) => ({ hash, short: hash, parents, subject: `commit ${hash}`, author: "You", time: 0 });

test("the vault draws two branches as two lanes, with the merge capsule marked and a line to each parent", () => {
  const project = {
    ...record("snapshots").one,
    head: "m",
    branch: "main",
    commits: [capsuleCommit("m", ["a2", "b1"]), capsuleCommit("b1", ["a1"]), capsuleCommit("a2", ["a1"]), capsuleCommit("a1")],
    refs: [{ name: "main", kind: "branch", target: "m" }, { name: "feature", kind: "branch", target: "b1" }],
  };
  const panel = ZonePanel.create();
  panel.update(observe(project));
  const vault = zone(panel, "vault");
  const merge = keyed(vault, "vault:m");
  assert.ok(merge.classList.contains("is-merge"));
  assert.equal(keyed(vault, "vault:b1").querySelector(".cblock").getAttribute("style"), "margin-left:16px");
  assert.equal(keyed(vault, "vault:a2").querySelector(".cblock").getAttribute("style"), "margin-left:0px");
  assert.equal(vault.querySelectorAll("svg.links path").length, 4);
  assert.deepEqual([...keyed(vault, "vault:b1").querySelectorAll(".ref")].map((ref) => ref.textContent), ["feature"]);
});

test("a single branch keeps one lane: every capsule in the first column, one line between each", () => {
  const panel = ZonePanel.create();
  const project = { ...record("snapshots").one, head: "c2", branch: "main", commits: [capsuleCommit("c2", ["c1"]), capsuleCommit("c1")], refs: [{ name: "main", kind: "branch", target: "c2" }] };
  panel.update(observe(project));
  const vault = zone(panel, "vault");
  assert.deepEqual([...vault.querySelectorAll(".cblock")].map((block) => block.getAttribute("style")), ["margin-left:0px", "margin-left:0px"]);
  assert.equal(vault.querySelectorAll("svg.links path").length, 1);
  assert.equal(vault.querySelector("svg.links").getAttribute("width"), "16");
});

test("the mothership draws what the stand-in GitHub holds, every branch included", () => {
  const github = { ...record("snapshots").one, bare: true, head: "g2", branch: "main", commits: [capsuleCommit("g2", ["g1"]), capsuleCommit("t1", ["g1"]), capsuleCommit("g1")], refs: [{ name: "main", kind: "branch", target: "g2" }, { name: "topic", kind: "branch", target: "t1" }] };
  const panel = ZonePanel.create();
  panel.update(observe(record("snapshots").one, github));
  assert.equal(zone(panel, "remote").querySelectorAll(".cap").length, 3);
  assert.ok(keyed(zone(panel, "remote"), "remote:t1"));
});
