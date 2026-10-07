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

test("the vault holds the history HEAD reaches, newest first, with HEAD, branches, remote branches and tags on their commits", () => {
  const project = snapshot({
    exists: true,
    head: "c3",
    branch: "main",
    commits: [commit("side", ["c1"]), commit("c3", ["c2"]), commit("c2", ["c1"]), commit("c1")],
    refs: [{ name: "main", kind: "branch", target: "c3" }, { name: "side", kind: "branch", target: "side" }, { name: "origin/main", kind: "remote", target: "c2" }, { name: "v1", kind: "tag", target: "c1" }],
  });
  const vault = Zones.read(observe(project)).vault;
  assert.deepEqual(vault.map((item) => item.hash), ["c3", "c2", "c1"]);
  assert.deepEqual(vault[0].labels, [{ text: "HEAD → main", kind: "head" }]);
  assert.deepEqual(vault[1].labels, [{ text: "origin/main", kind: "remote" }]);
  assert.deepEqual(vault[2].labels, [{ text: "v1", kind: "tag" }]);
  assert.equal(vault[0].subject, "commit c3");
  assert.equal(vault[0].short, "c3");
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
const capsule = (hash) => ({ hash, short: hash, subject: hash, author: "You", labels: [] });
const staged = (path, version = "v1") => ({ path, change: "added", version });

test("plain typing that changes nothing moves nothing", () => {
  assert.deepEqual(Zones.moves(model(), model(), []), { lit: [], flights: [], wake: [] });
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
  assert.deepEqual(moves, { lit: [], flights: [], wake: [] });
});

test("a change with no git typed (made outside the game's terminal) is drawn from the change alone", () => {
  const moves = Zones.moves(model({ dock: [] }), model({ dock: [staged("a.txt")] }), []);
  assert.deepEqual(moves.lit, ["add"]);
});

test("a mothership that appears wakes", () => {
  assert.deepEqual(Zones.moves(model(), model({ remote: [] }), ["remote"]).wake, ["remote"]);
});
