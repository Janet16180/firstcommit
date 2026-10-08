"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, record } = require("./load");

installBrowser();
const { Zones } = load(["zones.js"], ["Zones"]);

const file = (path, fields = {}) => ({ path, head: null, index: null, folder: "f1", head_mode: null, index_mode: null, folder_mode: "100644", ignored: false, conflicted: false, repository: false, index_change: null, folder_change: null, ...fields });
const commit = (hash, parents = [], subject = `commit ${hash}`) => ({ hash, short: hash.slice(0, 7), parents, subject, author: "You", time: 0 });
const snapshot = (fields = {}) => ({ ...record("snapshots").empty, ...fields });
const observe = (project, github = null) => ({ ...record("observation"), project, github });

test("a folder without a repository shows its files in the workshop as files git does not know, and the other zones off", () => {
  const zones = Zones.read(observe(snapshot({ exists: false, files: [file("map.txt"), file("notes.txt")] })));
  assert.equal(zones.repository, false);
  assert.deepEqual(zones.workshop, [{ path: "map.txt", state: "none" }, { path: "notes.txt", state: "none" }]);
  assert.equal(zones.dock, null);
  assert.equal(zones.vault, null);
  assert.equal(zones.remote, null);
});

test("each file in the folder says whether it is new, edited, on the dock or saved", () => {
  const files = [
    file("new.txt", { folder_change: "untracked" }),
    file("edited.txt", { head: "a", index: "a", folder_change: "modified" }),
    file("link", { head: "a", index: "a", folder_change: "typechange" }),
    file("staged.txt", { head: "a", index: "f1", index_change: "modified" }),
    file("saved.txt", { head: "f1", index: "f1" }),
  ];
  const zones = Zones.read(observe(snapshot({ exists: true, files })));
  assert.deepEqual(zones.workshop.map((item) => item.state), ["new", "edited", "edited", "staged", "saved"]);
});

test("a file deleted from the folder shows as deleted, and ignored files and files only git holds stay out of the workshop", () => {
  const files = [
    file("gone.txt", { head: "a", index: "a", folder: null, folder_mode: null, folder_change: "deleted" }),
    file("build.log", { ignored: true, folder_change: "ignored" }),
    file("removed.txt", { head: "a", folder: null, folder_mode: null, index_change: "deleted" }),
  ];
  const zones = Zones.read(observe(snapshot({ exists: true, files })));
  assert.deepEqual(zones.workshop, [{ path: "gone.txt", state: "deleted" }]);
});

test("the dock holds every staged change with its kind, in the snapshot's order", () => {
  const zones = Zones.read(observe(snapshot({ exists: true, files: record("files") })));
  assert.deepEqual(zones.dock.map(({ path, change }) => ({ path, change })), [
    { path: "added.txt", change: "added" },
    { path: "staged.txt", change: "modified" },
    { path: "removed.txt", change: "deleted" },
    { path: "staged-link", change: "typechange" },
  ]);
  assert.equal(zones.dock[0].version, record("files")[0].index);
});

test("a repository before its first commit has an empty vault, and what was added waits on the dock", () => {
  const zones = Zones.read(observe(record("snapshots").unborn));
  assert.equal(zones.repository, true);
  assert.deepEqual(zones.dock.map((item) => item.path), ["hello.txt"]);
  assert.deepEqual(zones.vault, []);
});

test("the vault holds every commit of every branch, children before parents, with HEAD, branches, remote branches and tags on their commits", () => {
  const project = snapshot({
    exists: true,
    head: "c3",
    branch: "main",
    commits: [commit("side", ["c1"]), commit("c3", ["c2"]), commit("c2", ["c1"]), commit("c1")],
    refs: [{ name: "main", kind: "branch", target: "c3" }, { name: "side", kind: "branch", target: "side" }, { name: "origin/main", kind: "remote", target: "c2" }, { name: "v1", kind: "tag", target: "c1" }],
  });
  const vault = Zones.read(observe(project)).vault;
  assert.deepEqual(vault.map((item) => item.hash), ["side", "c3", "c2", "c1"]);
  const by = Object.fromEntries(vault.map((item) => [item.hash, item]));
  assert.deepEqual(by.c3.labels, [{ text: "HEAD → main", kind: "head" }]);
  assert.deepEqual(by.side.labels, [{ text: "side", kind: "branch" }]);
  assert.deepEqual(by.c2.labels, [{ text: "origin/main", kind: "remote" }]);
  assert.deepEqual(by.c1.labels, [{ text: "v1", kind: "tag" }]);
  assert.equal(by.c3.subject, "commit c3");
  assert.equal(by.c3.short, "c3");
});

test("a single branch is one lane", () => {
  const project = snapshot({ exists: true, head: "c3", branch: "main", commits: [commit("c3", ["c2"]), commit("c2", ["c1"]), commit("c1")], refs: [] });
  assert.deepEqual(Zones.read(observe(project)).vault.map((item) => item.lane), [0, 0, 0]);
});

test("two branches take two lanes, and a merge commit with two parents joins them", () => {
  const project = snapshot({
    exists: true,
    head: "m",
    branch: "main",
    commits: [commit("m", ["a2", "b1"]), commit("b1", ["a1"]), commit("a2", ["a1"]), commit("a1")],
    refs: [{ name: "main", kind: "branch", target: "m" }, { name: "feature", kind: "branch", target: "b1" }],
  });
  const vault = Zones.read(observe(project)).vault;
  const by = Object.fromEntries(vault.map((item) => [item.hash, item]));
  assert.deepEqual(vault.map((item) => item.hash), ["m", "b1", "a2", "a1"]);
  assert.equal(by.m.lane, 0);
  assert.deepEqual(by.m.parents, ["a2", "b1"]);
  assert.equal(by.a2.lane, 0);
  assert.equal(by.b1.lane, 1);
  assert.equal(by.a1.lane, 0);
});

test("children always come before their parents, whatever order the snapshot lists them in", () => {
  const project = snapshot({ exists: true, head: "c2", branch: "main", commits: [commit("c1"), commit("c2", ["c1"])], refs: [] });
  assert.deepEqual(Zones.read(observe(project)).vault.map((item) => item.hash), ["c2", "c1"]);
});

test("a detached HEAD is labelled on its own", () => {
  const project = snapshot({ exists: true, head: "c1", branch: null, commits: [commit("c1")], refs: [{ name: "main", kind: "branch", target: "c1" }] });
  assert.deepEqual(Zones.read(observe(project)).vault[0].labels, [{ text: "HEAD", kind: "head" }, { text: "main", kind: "branch" }]);
});

test("the mothership is the level's GitHub, with its history from its HEAD", () => {
  const github = snapshot({ exists: true, bare: true, head: "g2", branch: "main", commits: [commit("g2", ["g1"]), commit("g1")], refs: [{ name: "main", kind: "branch", target: "g2" }] });
  const zones = Zones.read(observe(snapshot({ exists: true }), github));
  assert.deepEqual(zones.remote.map((item) => item.hash), ["g2", "g1"]);
  assert.deepEqual(zones.remote[0].labels, [{ text: "main", kind: "branch" }]);
});

test("the authors of the commits are kept, so the page can name a teammate's", () => {
  const project = snapshot({ exists: true, head: "c1", branch: "main", commits: [{ ...commit("c1"), author: "Alex Kim" }], refs: [] });
  assert.equal(Zones.read(observe(project)).vault[0].author, "Alex Kim");
});

/* Zones before and after a change, from bare models. */
const model = (fields = {}) => ({ repository: true, workshop: [], dock: [], vault: [], remote: null, ...fields });
const capsule = (hash, { parents = [], labels = [], revert = false } = {}) => ({ hash, short: hash, subject: hash, author: "You", parents, lane: 0, revert, labels });
const head = (branch) => ({ text: `HEAD → ${branch}`, kind: "head" });
const branch = (name) => ({ text: name, kind: "branch" });
const staged = (path, version = "v1") => ({ path, change: "added", version });

const NOTHING = { lit: [], flights: [], wake: [], fades: [], appears: [], bounces: [], cracks: [], rises: [] };

test("plain typing that changes nothing moves nothing", () => {
  assert.deepEqual(Zones.moves(model(), model(), []), NOTHING);
});

test("git init wakes the dock and the vault", () => {
  assert.deepEqual(Zones.moves(model({ repository: false, dock: null, vault: null }), model(), ["init"]).wake, ["dock", "vault"]);
});

test("git add flies each newly staged file from the workshop to the dock and lights the add arrow", () => {
  const moves = Zones.moves(model({ dock: [staged("a.txt")] }), model({ dock: [staged("a.txt"), staged("map.txt")] }), ["add"]);
  assert.deepEqual(moves.flights, [{ from: "workshop:map.txt", to: "dock:map.txt" }]);
  assert.deepEqual(moves.lit, ["add"]);
});

test("a file staged again after an edit flies again", () => {
  const moves = Zones.moves(model({ dock: [staged("a.txt", "v1")] }), model({ dock: [staged("a.txt", "v2")] }), ["add"]);
  assert.deepEqual(moves.flights, [{ from: "workshop:a.txt", to: "dock:a.txt" }]);
});

test("unstaging flies a file back from the dock to the workshop", () => {
  const moves = Zones.moves(model({ dock: [staged("secret.txt")] }), model(), ["restore"]);
  assert.deepEqual(moves.flights, [{ from: "dock:secret.txt", to: "workshop:secret.txt" }]);
  assert.deepEqual(moves.lit, []);
});

test("git commit flies what was on the dock into the new capsule and lights the commit arrow", () => {
  const moves = Zones.moves(model({ dock: [staged("a.txt"), staged("b.txt")] }), model({ vault: [capsule("c1")] }), ["commit"]);
  assert.deepEqual(moves.flights, [{ from: "dock:a.txt", to: "vault:c1" }, { from: "dock:b.txt", to: "vault:c1" }]);
  assert.deepEqual(moves.lit, ["commit"]);
});

test("a push flies the new capsules to the mothership, and a pull brings them down", () => {
  const pushed = Zones.moves(model({ vault: [capsule("c1")], remote: [] }), model({ vault: [capsule("c1")], remote: [capsule("c1")] }), ["push"]);
  assert.deepEqual(pushed.flights, [{ from: "vault:c1", to: "remote:c1" }]);
  assert.deepEqual(pushed.lit, ["push"]);
  const pulled = Zones.moves(model({ vault: [], remote: [capsule("t1")] }), model({ vault: [capsule("t1")], remote: [capsule("t1")] }), ["pull"]);
  assert.deepEqual(pulled.flights, [{ from: "remote:t1", to: "vault:t1" }]);
  assert.deepEqual(pulled.lit, ["pull"]);
});

test("when git commands were typed, only the moves they make are drawn", () => {
  const moves = Zones.moves(model({ dock: [] }), model({ dock: [staged("a.txt")] }), ["status"]);
  assert.deepEqual(moves, NOTHING);
});

test("a change with no git typed (made outside the game's terminal) is drawn from the change alone", () => {
  const moves = Zones.moves(model({ dock: [] }), model({ dock: [staged("a.txt")] }), []);
  assert.deepEqual(moves.lit, ["add"]);
});

test("a mothership that appears wakes", () => {
  assert.deepEqual(Zones.moves(model(), model({ remote: [] }), ["remote"]).wake, ["remote"]);
});

test("a refused push bounces the HEAD capsule off the mothership and back, and lights nothing", () => {
  const vault = [capsule("c2", { labels: [head("main")] }), capsule("c1")];
  const moves = Zones.moves(model({ vault, remote: [capsule("c1")] }), model({ vault, remote: [capsule("c1")] }), [], ["push"]);
  assert.deepEqual(moves.bounces, [{ from: "vault:c2", to: "remote" }]);
  assert.deepEqual(moves.lit, []);
});

test("a clone copies the mothership's chain down into the vault", () => {
  const remote = [capsule("c2"), capsule("c1")];
  const moves = Zones.moves(model({ repository: false, vault: null, dock: null, remote }), model({ vault: [capsule("c2"), capsule("c1")], remote }), ["clone"]);
  assert.deepEqual(moves.flights, [{ from: "remote:c2", to: "vault:c2" }, { from: "remote:c1", to: "vault:c1" }]);
  assert.deepEqual(moves.appears, []);
});

test("a branch label that moved to another capsule slides there", () => {
  const before = model({ vault: [capsule("c2", { labels: [head("main")] }), capsule("c1", { labels: [branch("feature")] })] });
  const after = model({ vault: [capsule("c2", { labels: [head("main"), branch("feature")] }), capsule("c1")] });
  assert.deepEqual(Zones.moves(before, after, ["merge"]).flights, [{ from: "vault-ref:feature", to: "vault-ref:feature" }]);
});

test("a switch slides HEAD to the other branch", () => {
  const before = model({ vault: [capsule("b1", { labels: [branch("feature")] }), capsule("a1", { labels: [head("main")] })] });
  const after = model({ vault: [capsule("b1", { labels: [head("feature")] }), capsule("a1", { labels: [branch("main")] })] });
  const flights = Zones.moves(before, after, ["switch"]).flights;
  assert.ok(flights.some((flight) => flight.from === "vault-ref:HEAD" && flight.to === "vault-ref:HEAD"));
});

test("a merge joins both chains into the merge capsule", () => {
  const before = model({ vault: [capsule("b1", { labels: [branch("feature")] }), capsule("a2", { labels: [head("main")] }), capsule("a1")] });
  const after = model({ vault: [capsule("m", { parents: ["a2", "b1"], labels: [head("main")] }), capsule("b1"), capsule("a2"), capsule("a1")] });
  const flights = Zones.moves(before, after, ["merge"]).flights;
  assert.ok(flights.some((flight) => flight.from === "vault:a2" && flight.to === "vault:m"));
  assert.ok(flights.some((flight) => flight.from === "vault:b1" && flight.to === "vault:m"));
});

test("capsules that left the branches fade off, and capsules that come back appear", () => {
  const three = [capsule("c3"), capsule("c2"), capsule("c1")];
  const one = [capsule("c1")];
  assert.deepEqual(Zones.moves(model({ vault: three }), model({ vault: one }), ["reset"]).fades, ["vault:c3", "vault:c2"]);
  assert.deepEqual(Zones.moves(model({ vault: one }), model({ vault: three }), ["reset"]).appears, ["vault:c3", "vault:c2"]);
});

test("a conflicted file is marked in the workshop, before any other state, and a merge in progress is said", () => {
  const files = [file("map.txt", { head: "a", index: "b", conflicted: true, index_change: "modified", folder_change: "modified" })];
  const zones = Zones.read(observe(snapshot({ exists: true, files, operation: "merge" })));
  assert.deepEqual(zones.workshop, [{ path: "map.txt", state: "conflicted" }]);
  assert.equal(zones.operation, "merge");
  assert.equal(Zones.read(observe(snapshot({ exists: true }))).operation, null);
});

test("a commit with git's revert message is marked as a revert", () => {
  const project = snapshot({ exists: true, head: "r", branch: "main", commits: [commit("r", ["c1"], 'Revert "Add the bad route"'), commit("c1")], refs: [] });
  assert.deepEqual(Zones.read(observe(project)).vault.map((item) => item.revert), [true, false]);
});

test("a file that just became conflicted cracks", () => {
  const was = model({ workshop: [{ path: "map.txt", state: "staged" }] });
  const now = model({ workshop: [{ path: "map.txt", state: "conflicted" }] });
  assert.deepEqual(Zones.moves(was, now, ["merge"]).cracks, ["workshop:map.txt"]);
  assert.deepEqual(Zones.moves(now, now, ["status"]).cracks, []);
});

test("a revert capsule rises in instead of simply appearing", () => {
  const moves = Zones.moves(model({ vault: [capsule("c1")] }), model({ vault: [capsule("r", { revert: true }), capsule("c1")] }), ["revert"]);
  assert.deepEqual(moves.rises, ["vault:r"]);
  assert.deepEqual(moves.appears, []);
});

/* A crew level: your station, the mothership, and Alex's station (their clone of the playground). */
const station = (vault, fields = {}) => ({ repository: true, workshop: [], dock: [], vault, ...fields });

test("a teammate's clone is read as their own station, with its workshop, dock and vault", () => {
  const zones = Zones.read(record("press").observation);
  assert.deepEqual(zones.crew.vault.map((item) => item.short), ["21e6785", "de4c885"]);
  assert.deepEqual(zones.crew.workshop.map((item) => item.path), ["README.md", "notes.txt"]);
  assert.deepEqual(zones.crew.dock, []);
  assert.equal(Zones.read(record("observation")).crew, null);
});

test("a teammate's push flies the new capsule from their station up to the mothership, whatever you typed", () => {
  const before = model({ vault: [capsule("s1")], remote: [capsule("s1")], crew: station([capsule("a1"), capsule("s1")]) });
  const after = model({ vault: [capsule("s1")], remote: [capsule("a1"), capsule("s1")], crew: station([capsule("a1"), capsule("s1")]) });
  const moves = Zones.moves(before, after, ["status"]);
  assert.deepEqual(moves.flights, [{ from: "crew-vault:a1", to: "remote:a1" }]);
  assert.deepEqual(moves.lit, ["crew-push"]);
});

test("a capsule the mothership got lands at the teammate's station when they pull", () => {
  const before = model({ vault: [capsule("y1")], remote: [capsule("y1")], crew: station([]) });
  const after = model({ vault: [capsule("y1")], remote: [capsule("y1")], crew: station([capsule("y1")]) });
  assert.deepEqual(Zones.moves(before, after, []).flights, [{ from: "remote:y1", to: "crew-vault:y1" }]);
});

test("your push flies only capsules your own vault holds", () => {
  const before = model({ vault: [capsule("y1")], remote: [], crew: station([capsule("a1")]) });
  const after = model({ vault: [capsule("y1")], remote: [capsule("y1"), capsule("a1")], crew: station([capsule("a1")]) });
  const flights = Zones.moves(before, after, ["push"]).flights;
  assert.ok(flights.some((flight) => flight.from === "vault:y1" && flight.to === "remote:y1"));
  assert.ok(!flights.some((flight) => flight.from === "vault:a1"));
});

test("the mothership is named once the repository knows origin, and naming it wakes the mothership", () => {
  const github = snapshot({ exists: true, bare: true });
  assert.equal(Zones.read(observe(snapshot({ exists: true, remotes: [] }), github)).named, false);
  assert.equal(Zones.read(observe(snapshot({ exists: true, remotes: [{ name: "origin", url: "../github/project.git" }] }), github)).named, true);
  assert.deepEqual(Zones.moves(model({ remote: [], named: false }), model({ remote: [], named: true }), ["remote"]).wake, ["remote"]);
});
