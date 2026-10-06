"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { html } = require("./fakedom");
const { installBrowser, load, record } = require("./load");

installBrowser();
const { RepoMap } = load(["dom.js", "map.js"], ["RepoMap"]);

const full = (name) => name.padEnd(40, "0");

/* A snapshot from a compact description: commits newest first as [name, [parent names]]. */
function history({ commits, refs = [], head = commits.length ? commits[0][0] : null, branch = "main", files = [] }) {
  return {
    exists: true,
    bare: false,
    head: head && full(head),
    branch,
    commits: commits.map(([name, parents], index) => ({
      hash: full(name),
      short: full(name).slice(0, 7),
      parents: parents.map(full),
      subject: `Commit ${name}`,
      author: "Alex Kim",
      time: 1000 - index,
    })),
    refs: refs.map(([name, kind, target]) => ({ name, kind, target: full(target) })),
    files,
    operation: null,
    stash: 0,
    truncated: false,
  };
}

const lanesOf = (map) => Object.fromEntries(map.commits.map((commit) => [commit.hash.replace(/0+$/, ""), commit.lane]));
const rowsOf = (map) => map.commits.map((commit) => commit.hash.replace(/0+$/, ""));
const labelsAt = (map, name) => map.commits.find((commit) => commit.hash === full(name)).labels.map((label) => `${label.kind}:${label.text}${label.current ? "*" : ""}`);

test("a history on one branch is one lane, newest commit first", () => {
  const map = RepoMap.layout(history({ commits: [["c", ["b"]], ["b", ["a"]], ["a", []]], refs: [["main", "branch", "c"]] }));
  assert.deepEqual(rowsOf(map), ["c", "b", "a"]);
  assert.deepEqual(lanesOf(map), { c: 0, b: 0, a: 0 });
  assert.equal(map.lanes, 1);
  assert.deepEqual(map.edges.map((edge) => edge.kind), ["line", "line"]);
});

test("a branch gets its own lane and main keeps the first, even when HEAD is on the branch", () => {
  const map = RepoMap.layout(record("observation").project);
  const lanes = Object.values(lanesOf(map));
  const project = record("observation").project;
  const lane = (name) => map.commits.find((commit) => commit.hash === project.refs.find((ref) => ref.name === name).target).lane;
  assert.equal(lane("main"), 0);
  assert.equal(lane("feature"), 1);
  assert.equal(Math.max(...lanes), 1);
});

test("a fork leaves its lane at the commit it started from", () => {
  const map = RepoMap.layout(history({ commits: [["f", ["a"]], ["b", ["a"]], ["a", []]], refs: [["main", "branch", "b"], ["topic", "branch", "f"]] }));
  assert.deepEqual(lanesOf(map), { f: 1, b: 0, a: 0 });
  const fork = map.edges.find((edge) => edge.from === full("f"));
  assert.equal(fork.kind, "fork");
  assert.equal(fork.to, full("a"));
});

test("a merge draws an edge to each parent, and a merged branch keeps a lane after its name is deleted", () => {
  const map = RepoMap.layout(history({ commits: [["m", ["b", "f"]], ["f", ["a"]], ["b", ["a"]], ["a", []]], refs: [["main", "branch", "m"]] }));
  assert.deepEqual(lanesOf(map), { m: 0, f: 1, b: 0, a: 0 });
  const fromMerge = map.edges.filter((edge) => edge.from === full("m"));
  assert.deepEqual(fromMerge.map((edge) => [edge.kind, edge.to]), [["line", full("b")], ["merge", full("f")]]);
});

test("lanes are reused once a branch has been merged", () => {
  const commits = [["m2", ["c", "g"]], ["g", ["c"]], ["c", ["m1"]], ["m1", ["b", "f"]], ["f", ["b"]], ["b", ["a"]], ["a", []]];
  const map = RepoMap.layout(history({ commits, refs: [["main", "branch", "m2"]] }));
  assert.equal(map.lanes, 2);
  assert.deepEqual(lanesOf(map), { m2: 0, g: 1, c: 0, m1: 0, f: 1, b: 0, a: 0 });
});

test("children are drawn above their parents even when the commits arrive out of order", () => {
  const map = RepoMap.layout(history({ commits: [["a", []], ["c", ["b"]], ["b", ["a"]]], head: "c", refs: [["main", "branch", "c"]] }));
  assert.deepEqual(rowsOf(map), ["c", "b", "a"]);
});

test("the trunk names come first: master is lane 0 too, and a theme can name its own", () => {
  const snapshot = history({ commits: [["x", ["a"]], ["b", ["a"]], ["a", []]], refs: [["master", "branch", "b"], ["alpha", "branch", "x"]] });
  assert.deepEqual(lanesOf(RepoMap.layout(snapshot)), { x: 1, b: 0, a: 0 });
  const theme = RepoMap.theme({ trunk: ["alpha"] });
  assert.deepEqual(lanesOf(RepoMap.layout(snapshot, { theme })), { x: 0, b: 1, a: 0 });
});

test("a remote-tracking branch ahead of the local one gets a lane after the local branches", () => {
  const snapshot = history({
    commits: [["r", ["b"]], ["t", ["b"]], ["b", ["a"]], ["a", []]],
    head: "b",
    refs: [["main", "branch", "b"], ["topic", "branch", "t"], ["origin/main", "remote", "r"]],
  });
  assert.deepEqual(lanesOf(RepoMap.layout(snapshot)), { r: 2, t: 1, b: 0, a: 0 });
});

test("HEAD's commit carries the marker, then its branch, the other branches, remotes and tags", () => {
  const map = RepoMap.layout(
    history({
      commits: [["b", ["a"]], ["a", []]],
      refs: [["v1", "tag", "b"], ["origin/main", "remote", "b"], ["zeta", "branch", "b"], ["main", "branch", "b"]],
    }),
  );
  assert.deepEqual(labelsAt(map, "b"), ["head:HEAD", "branch:main*", "branch:zeta", "remote:origin/main", "tag:v1"]);
  assert.equal(map.commits[0].isHead, true);
  assert.equal(map.commits[1].isHead, false);
});

test("a detached HEAD says so and marks no branch as current", () => {
  const map = RepoMap.layout(history({ commits: [["b", ["a"]], ["a", []]], head: "a", branch: null, refs: [["main", "branch", "b"]] }));
  assert.deepEqual(labelsAt(map, "a"), ["head:HEAD (detached)"]);
  assert.deepEqual(labelsAt(map, "b"), ["branch:main"]);
});

test("a stand-in GitHub shows its branches without a you-are-here marker", () => {
  const map = RepoMap.layout(record("observation").github, { showHead: false });
  assert.ok(map.commits.every((commit) => !commit.isHead && commit.labels.every((label) => label.kind !== "head")));
  assert.deepEqual(map.commits[0].labels.map((label) => [label.text, label.current]), [["main", false]]);
});

test("a parent left out of a cut history gets a short dangling edge", () => {
  const snapshot = history({ commits: [["c", ["b"]], ["b", ["a"]]], refs: [["main", "branch", "c"]] });
  const map = RepoMap.layout({ ...snapshot, truncated: true });
  assert.deepEqual(map.edges.map((edge) => [edge.kind, edge.to]), [["line", full("b")], ["cut", full("a")]]);
});

test("commits missing from the previous snapshot are marked new, and nothing is new without one", () => {
  const snapshot = history({ commits: [["c", ["b"]], ["b", []]], refs: [["main", "branch", "c"]] });
  assert.deepEqual(RepoMap.layout(snapshot, { previous: new Set([full("b")]) }).commits.map((commit) => commit.isNew), [true, false]);
  assert.deepEqual(RepoMap.layout(snapshot).commits.map((commit) => commit.isNew), [false, false]);
});

test("each commit sits on its lane and row, and the picture is wide enough for every label", () => {
  const map = RepoMap.layout(record("observation").project);
  const { sizes } = RepoMap.DEFAULT_THEME;
  for (const commit of map.commits) {
    assert.equal(commit.x, sizes.pad + commit.lane * sizes.lane + sizes.lane / 2);
    assert.equal(commit.y, sizes.pad + commit.row * sizes.row + sizes.row / 2);
    assert.ok(commit.textEnd <= map.width);
  }
  assert.equal(map.height, 2 * sizes.pad + map.commits.length * sizes.row);
});

test("long subjects are shortened with an ellipsis", () => {
  const snapshot = history({ commits: [["a", []]], refs: [["main", "branch", "a"]] });
  snapshot.commits[0].subject = "x".repeat(200);
  const shown = RepoMap.layout(snapshot).commits[0].subject;
  assert.equal(shown.length, RepoMap.DEFAULT_THEME.sizes.subject);
  assert.ok(shown.endsWith("…"));
});

test("the map shows each commit's short hash and subject, with its full hash in a tooltip", () => {
  const project = record("observation").project;
  const figure = RepoMap.render(project);
  const text = figure.textContent;
  for (const commit of project.commits) {
    assert.ok(text.includes(commit.short), commit.short);
    assert.ok(text.includes(commit.subject), commit.subject);
    assert.ok(text.includes(commit.hash), commit.hash);
  }
  assert.ok(figure.querySelector("svg[role=\"img\"]").getAttribute("aria-label").includes("HEAD"));
});

test("a key under the graph says the ringed commit is where the player is", () => {
  assert.match(RepoMap.render(record("observation").project).querySelector(".map-key").textContent, /HEAD: you are here/);
  const detached = { ...record("snapshots").one, branch: null };
  assert.match(RepoMap.render(detached).querySelector(".map-key").textContent, /detached/);
  assert.equal(RepoMap.render(record("observation").github, { showHead: false }).querySelector(".map-key"), null);
});

test("a folder without a repository and a branch without commits each say so", () => {
  assert.match(RepoMap.render(record("snapshots").empty).textContent, /No repository/);
  assert.match(RepoMap.render(record("snapshots").unborn).textContent, /main.*no commits yet/);
  assert.equal(RepoMap.render(record("snapshots").empty).querySelector("svg"), null);
});

test("an operation in progress, stashed changes and a cut history are noted", () => {
  const snapshot = { ...record("snapshots").one, operation: "merge", stash: 2, truncated: true };
  const notes = RepoMap.notes(snapshot);
  assert.equal(notes.length, 3);
  assert.match(notes[0], /merge/);
  assert.match(notes[1], /2/);
  assert.match(RepoMap.render(snapshot).textContent, /merge/);
});

test("a theme changes the colours, words and shapes without touching the layout", () => {
  const snapshot = record("snapshots").one;
  const theme = RepoMap.theme({
    colors: { lanes: ["tomato"] },
    words: { here: "Here you are" },
    shapes: { commit: ({ x, y, color }) => RepoMap.svg("rect", { class: "station", x, y, width: 4, height: 4, fill: color }) },
  });
  const figure = RepoMap.render(snapshot, { theme });
  assert.ok(figure.querySelector("rect.station"));
  assert.ok(html(figure).includes("tomato"));
  assert.ok(figure.querySelector(".map-key").textContent.includes("Here you are"));
  assert.equal(RepoMap.theme({}).words.here, RepoMap.DEFAULT_THEME.words.here);
  assert.deepEqual(RepoMap.layout(snapshot, { theme }).commits.map((commit) => commit.lane), [0]);
});

test("a file's state in each area comes from comparing its blob ids", () => {
  const rows = Object.fromEntries(RepoMap.areaRows(record("observation").project.files).map((row) => [row.path, row]));
  const states = (path) => ["folder", "index", "head"].map((area) => rows[path][area] && rows[path][area].state);
  assert.deepEqual(states("README.md"), ["same", "staged", "committed"]);
  assert.deepEqual(states("notes.txt"), ["changed", "same", "committed"]);
  assert.deepEqual(states("todo.txt"), ["untracked", null, null]);
  assert.deepEqual(states("build.log"), ["ignored", null, null]);
  assert.deepEqual(states("old.txt"), [null, "removed", "committed"]);
});

test("new, deleted and conflicted files have their own states", () => {
  const files = [
    { path: "new.txt", head: null, index: "b1", folder: "b1", ignored: false, conflicted: false },
    { path: "gone.txt", head: "b2", index: "b2", folder: null, ignored: false, conflicted: false },
    { path: "both.txt", head: "b3", index: null, folder: "b4", ignored: false, conflicted: true },
  ];
  const rows = RepoMap.areaRows(files);
  assert.deepEqual(rows.map((row) => [row.folder && row.folder.state, row.index && row.index.state]), [
    ["same", "new"],
    ["deleted", "same"],
    ["conflicted", "conflicted"],
  ]);
  assert.equal(rows[0].changed, true);
  assert.equal(rows[1].changed, true);
});

test("a file that is the same in all three areas is unchanged", () => {
  const [row] = RepoMap.areaRows([{ path: "a.txt", head: "b1", index: "b1", folder: "b1", ignored: false, conflicted: false }]);
  assert.equal(row.changed, false);
});

test("the same blob always gets the same colour", () => {
  const hue = RepoMap.blobHue("ce013625030ba8dba906f756967f9e9ca394464a");
  assert.equal(hue, RepoMap.blobHue("ce013625030ba8dba906f756967f9e9ca394464a"));
  assert.ok(hue >= 0 && hue < 360);
  assert.notEqual(hue, RepoMap.blobHue("e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"));
});

test("the areas strip shows every file with its short blob id in each area", () => {
  const files = record("observation").project.files;
  const strip = RepoMap.renderAreas(files);
  for (const file of files) assert.ok(strip.textContent.includes(file.path), file.path);
  assert.ok(strip.textContent.includes(files[0].index.slice(0, 7)));
  assert.match(strip.textContent, /Working folder.*Staging area.*Last commit/);
});

test("unchanged files fold into one line when there are many", () => {
  const files = Array.from({ length: 20 }, (_, index) => ({ path: `f${index}.txt`, head: "b", index: "b", folder: "b", ignored: false, conflicted: false }));
  files.push({ path: "changed.txt", head: "b", index: "b", folder: "c", ignored: false, conflicted: false });
  const strip = RepoMap.renderAreas(files);
  assert.ok(strip.textContent.includes("changed.txt"));
  assert.ok(!strip.textContent.includes("f3.txt"));
  assert.match(strip.textContent, /20 unchanged files/);
});

test("an empty folder says there are no files yet", () => {
  assert.match(RepoMap.renderAreas([]).textContent, /No files/);
});

test("the object list shows each object's type, hash and size, marking new ones", () => {
  const objects = record("lesson").slides[2].objects;
  const list = RepoMap.renderObjects(objects, { previous: new Set([objects[0].hash]) });
  for (const object of objects) {
    assert.ok(list.textContent.includes(object.hash));
    assert.ok(list.textContent.includes(object.type));
  }
  assert.equal(list.querySelectorAll(".is-new").length, objects.length - 1);
});

const entry = (path, fields) => ({ path, head: null, index: null, folder: null, head_mode: null, index_mode: null, folder_mode: null, ignored: false, conflicted: false, repository: false, ...fields });

test("a change of mode alone is a change, and the area that has a special mode says which", () => {
  const madeExecutable = entry("run.sh", { head: "b1", index: "b1", folder: "b1", head_mode: "100644", index_mode: "100644", folder_mode: "100755" });
  const staged = entry("run.sh", { head: "b1", index: "b1", folder: "b1", head_mode: "100644", index_mode: "100755", folder_mode: "100755" });
  const [folderOnly] = RepoMap.areaRows([madeExecutable]);
  assert.deepEqual([folderOnly.folder.state, folderOnly.index.state, folderOnly.changed], ["changed", "same", true]);
  assert.deepEqual([folderOnly.folder.mark, folderOnly.index.mark], ["executable", null]);
  const [stagedRow] = RepoMap.areaRows([staged]);
  assert.deepEqual([stagedRow.folder.state, stagedRow.index.state], ["same", "staged"]);
  assert.match(RepoMap.renderAreas([madeExecutable]).textContent, /executable/);
});

test("a repository inside the working folder is one row, marked as a repository, even before its first commit", () => {
  const nested = entry("vendor", { folder: "c1", folder_mode: "160000", repository: true });
  const empty = entry("tools", { repository: true });
  const rows = RepoMap.areaRows([nested, empty]);
  assert.deepEqual(rows.map((row) => [row.repository, row.folder && row.folder.state]), [[true, "untracked"], [true, "untracked"]]);
  const strip = RepoMap.renderAreas([nested, empty]);
  assert.equal(strip.querySelectorAll(".areas-row.is-repository").length, 2);
  assert.match(strip.textContent, /vendor.*repository/);
});

test("a long file name is shortened on its own, so the repository mark beside it stays readable", () => {
  const path = "third_party/a-very-long-vendored-library-name";
  const row = RepoMap.renderAreas([entry(path, { folder: "c1", folder_mode: "160000", repository: true })]).querySelector(".is-repository");
  const name = row.querySelector(".areas-name");
  assert.equal(name.textContent, path);
  assert.equal(name.getAttribute("title"), path);
  assert.equal(name.contains(row.querySelector(".areas-repo")), false);
});
