"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, record } = require("./load");

const document = installBrowser();
const { TimePlaces } = load(["dom.js", "map.js", "theme-time.js", "theme-time-motion.js", "theme-time-places.js"], ["TimePlaces"]);

const full = (name) => name.padEnd(40, "0");
const blob = (name) => name.padEnd(40, "b");

/* A file in the three areas: ids by short name, null where absent, and git status's two columns. */
function file(path, { head = null, index = null, folder = null, indexChange = null, folderChange = null } = {}) {
  const mode = (id) => (id === null ? null : "100644");
  return {
    path, head: head && blob(head), index: index && blob(index), folder: folder && blob(folder),
    head_mode: mode(head), index_mode: mode(index), folder_mode: mode(folder),
    ignored: false, conflicted: false, repository: false, index_change: indexChange, folder_change: folderChange,
  };
}

/* A snapshot: commits newest first as [name, [parents]], refs as [name, kind, target]. */
function repo({ commits = [], refs = [], files = [], bare = false, head = commits.length ? commits[0][0] : null }) {
  return {
    ...record("snapshots").one,
    exists: true,
    bare,
    head: bare || head === null ? null : full(head),
    branch: "main",
    commits: commits.map(([name, parents], index) => ({
      hash: full(name), short: full(name).slice(0, 7), parents: parents.map(full), subject: `Commit ${name}`, author: "Robin Park", time: 1000 - index,
    })),
    refs: refs.map(([name, kind, target]) => ({ name, kind, target: full(target) })),
    files,
  };
}

const kinds = (...names) => names.map((kind) => ({ kind, text: [] }));
const ONE = [["a", []]];
const TWO = [["b", ["a"]], ["a", []]];

const C = ["c", ["b"]];
const D = ["d", ["b"]];
const AMENDED = ["dd", ["b"]];
const MERGE = ["e", ["d", "c"]];
const REBASED_D = ["f", ["c"]];
const LOCAL_MERGE = ["ee", ["b", "dd"]];

/* Your repository with `main` and `origin/main`: c is a teammate's commit on GitHub, d is yours. */
const at = (commits, main, origin) => repo({ commits, refs: [["main", "branch", main], ["origin/main", "remote", origin]], head: main });
const START = at(TWO, "b", "b");
const FETCHED = at([C, ...TWO], "b", "c");
const PULLED = at([C, ...TWO], "c", "c");
const MINE = at([D, ...TWO], "d", "b");
const BOTH = at([C, D, ...TWO], "d", "c");
const MERGED = at([MERGE, C, D, ...TWO], "e", "c");
const REBASED = at([REBASED_D, C, ...TWO], "f", "c");
const PUSHED = at([D, ...TWO], "d", "d");

test("the arrows that light are the commands that match what just happened, in the order they run", () => {
  const cases = [
    ["git add", ["file-staged"], START, START, ["add"]],
    ["git commit", ["commit-created"], START, MINE, ["commit"]],
    ["git commit --amend", ["commit-replaced"], MINE, at([AMENDED, ...TWO], "dd", "b"), ["commit"]],
    ["git commit -a", ["file-staged", "commit-created"], START, MINE, ["add", "commit"]],
    ["a merge of a branch of yours", ["merge-commit-created"], START, at([LOCAL_MERGE, AMENDED, ...TWO], "ee", "b"), ["commit"]],
    ["git push", ["remote-updated", "push-received"], MINE, PUSHED, ["push"]],
    ["git commit, then git push", ["commit-created", "remote-updated", "push-received"], START, PUSHED, ["commit", "push"]],
    ["a refused push", [], MINE, MINE, []],
    ["git fetch", ["remote-updated"], START, FETCHED, ["fetch"]],
    ["git commit and git fetch together", ["commit-created", "remote-updated"], START, BOTH, ["commit", "fetch"]],
    ["a git pull that stops after the fetch because the branches diverged", ["remote-updated"], MINE, BOTH, ["fetch"]],
    ["git pull, a fast-forward", ["branch-moved", "remote-updated"], START, PULLED, ["fetch", "pull"]],
    ["git pull --no-rebase", ["merge-commit-created", "remote-updated", "file-changed"], MINE, MERGED, ["fetch", "pull"]],
    ["git pull --rebase", ["branch-moved", "remote-updated"], MINE, REBASED, ["fetch", "pull"]],
    ["git pull after a git fetch", ["branch-moved"], FETCHED, PULLED, ["pull"]],
    ["git merge origin/main after a git fetch", ["commit-created"], BOTH, MERGED, ["pull"]],
  ];
  for (const [what, events, before, after, lit] of cases) assert.deepEqual(TimePlaces.commands(kinds(...events), before, after), lit, what);
});

test("a new repository is a clone when it already has a remote-tracking branch, and nothing lights for git init", () => {
  const empty = { ...record("snapshots").empty };
  const cloned = repo({ commits: ONE, refs: [["main", "branch", "a"], ["origin/main", "remote", "a"]] });
  assert.deepEqual(TimePlaces.commands(kinds("repository-created"), empty, cloned), ["clone"]);
  assert.deepEqual(TimePlaces.commands(kinds("repository-created"), empty, repo({})), []);
});

const hub = (commits) => repo({ commits, bare: true, refs: [["main", "branch", commits[0][0]]] });
const README = (blobs) => file("README.md", { head: blobs, index: blobs, folder: blobs });

test("git add flies the file from the working folder to the staging area", () => {
  const before = { project: repo({ commits: ONE, files: [file("README.md", { head: "1", index: "1", folder: "2" }), file("notes.txt", { folder: "3" })] }), github: null };
  const after = { project: repo({ commits: ONE, files: [file("README.md", { head: "1", index: "2", folder: "2" }), file("notes.txt", { folder: "3" })] }), github: null };
  assert.deepEqual(TimePlaces.flights(before, after, ["add"]), [{ what: "file", id: "README.md", by: "add", path: ["folder", "index"] }]);
});

test("git commit flies a save point from the staging area into your repository", () => {
  const before = { project: START, github: hub(TWO) };
  const after = { project: MINE, github: hub(TWO) };
  assert.deepEqual(TimePlaces.flights(before, after, ["commit"]), [{ what: "commit", id: full("d"), by: "commit", path: ["index", "repository"] }]);
});

test("git push flies the commits GitHub was missing from your repository to GitHub", () => {
  const before = { project: MINE, github: hub(TWO) };
  const after = { project: PUSHED, github: hub([D, ...TWO]) };
  assert.deepEqual(TimePlaces.flights(before, after, ["push"]), [{ what: "commit", id: full("d"), by: "push", path: ["repository", "remote"] }]);
});

test("a commit pushed in the same batch flies twice: into your repository, then on to GitHub", () => {
  const before = { project: START, github: hub(TWO) };
  const after = { project: PUSHED, github: hub([D, ...TWO]) };
  assert.deepEqual(TimePlaces.flights(before, after, ["commit", "push"]), [
    { what: "commit", id: full("d"), by: "commit", path: ["index", "repository"] },
    { what: "commit", id: full("d"), by: "push", path: ["repository", "remote"] },
  ]);
});

test("git fetch flies the new commits from GitHub into your repository, and nothing to your files", () => {
  const before = { project: { ...START, files: [README("1")] }, github: hub([C, ...TWO]) };
  const after = { project: { ...FETCHED, files: [README("1")] }, github: hub([C, ...TWO]) };
  assert.deepEqual(TimePlaces.flights(before, after, ["fetch"]), [{ what: "commit", id: full("c"), by: "fetch", path: ["remote", "repository"] }]);
});

test("a commit of yours made alongside a fetch flies from the staging area; only GitHub's commits fly from GitHub", () => {
  const before = { project: START, github: hub([C, ...TWO]) };
  const after = { project: BOTH, github: hub([C, ...TWO]) };
  assert.deepEqual(TimePlaces.flights(before, after, ["commit", "fetch"]), [
    { what: "commit", id: full("d"), by: "commit", path: ["index", "repository"] },
    { what: "commit", id: full("c"), by: "fetch", path: ["remote", "repository"] },
  ]);
});

const PULL = {
  before: { project: { ...START, files: [README("1")] }, github: hub([C, ...TWO]) },
  after: { project: { ...PULLED, files: [README("2"), file("rules.md", { head: "4", index: "4", folder: "4" })] }, github: hub([C, ...TWO]) },
};

test("git pull flies the new commits in, then the changed files from your repository through the staging area to the working folder", () => {
  assert.deepEqual(TimePlaces.flights(PULL.before, PULL.after, ["fetch", "pull"]), [
    { what: "commit", id: full("c"), by: "fetch", path: ["remote", "repository"] },
    { what: "file", id: "README.md", by: "pull", path: ["repository", "index", "folder"] },
    { what: "file", id: "rules.md", by: "pull", path: ["repository", "index", "folder"] },
  ]);
});

test("a merge commit is made in your repository: it does not fly from GitHub", () => {
  const before = { project: { ...MINE, files: [README("1")] }, github: hub([C, ...TWO]) };
  const after = { project: { ...MERGED, files: [README("2")] }, github: hub([C, ...TWO]) };
  assert.deepEqual(TimePlaces.flights(before, after, ["fetch", "pull"]).filter((flight) => flight.what === "commit"), [
    { what: "commit", id: full("c"), by: "fetch", path: ["remote", "repository"] },
  ]);
});

test("a pull after an earlier fetch brings no commits from GitHub, only the files out to the working folder", () => {
  const before = { project: { ...FETCHED, files: [README("1")] }, github: hub([C, ...TWO]) };
  const after = { project: { ...PULLED, files: [README("2")] }, github: hub([C, ...TWO]) };
  assert.deepEqual(TimePlaces.flights(before, after, ["pull"]), [{ what: "file", id: "README.md", by: "pull", path: ["repository", "index", "folder"] }]);
});

test("git clone flies the commits in from GitHub and the files out through the staging area to a new working folder", () => {
  const empty = { ...record("snapshots").empty };
  const before = { project: empty, github: hub(ONE) };
  const after = { project: repo({ commits: ONE, refs: [["main", "branch", "a"], ["origin/main", "remote", "a"]], files: [README("1")] }), github: hub(ONE) };
  assert.deepEqual(TimePlaces.flights(before, after, ["clone"]), [
    { what: "commit", id: full("a"), by: "clone", path: ["remote", "repository"] },
    { what: "file", id: "README.md", by: "clone", path: ["repository", "index", "folder"] },
  ]);
});

test("commits fly oldest first, so a parent lands before its child", () => {
  const empty = { ...record("snapshots").empty };
  const before = { project: empty, github: hub(TWO) };
  const after = { project: at(TWO, "b", "b"), github: hub(TWO) };
  const order = TimePlaces.flights(before, after, ["clone"]).map((flight) => flight.id);
  assert.deepEqual(order, [full("a"), full("b")]);
});

test("nothing flies when no arrow lit or there is no earlier drawing", () => {
  const state = { project: repo({ commits: ONE }), github: null };
  assert.deepEqual(TimePlaces.flights(state, state, []), []);
  assert.deepEqual(TimePlaces.flights(null, state, ["commit"]), []);
});

test("the figure shows the four places, every arrow with its Git word, and lights the ones that happened", () => {
  const observation = { project: repo({ commits: TWO, refs: [["main", "branch", "b"], ["origin/main", "remote", "a"]], files: [file("README.md", { head: "1", index: "2", folder: "2" })] }), github: repo({ commits: ONE, bare: true, refs: [["main", "branch", "a"]] }) };
  const figure = TimePlaces.render(observation, { commands: ["commit", "fetch"] });
  const titles = figure.querySelectorAll(".tt-place h4").map((title) => title.textContent);
  assert.deepEqual(titles, ["Working folder", "Staging area", "Your repository", "Remote repository"]);
  const arrows = figure.querySelectorAll(".tt-arrow").map((arrow) => arrow.getAttribute("data-command"));
  assert.deepEqual([...new Set(arrows)].sort(), ["add", "clone", "commit", "fetch", "pull", "push"]);
  assert.deepEqual(figure.querySelectorAll(".tt-arrow.is-active").map((arrow) => arrow.getAttribute("data-command")).sort(), ["commit", "fetch"]);
  const caption = figure.querySelector(".tt-places-caption").textContent;
  assert.match(caption, /commit saves the staging area as a new commit.*the staging area keeps its files/);
  assert.match(caption, /fetch downloads.*no branch of yours, no working file/);
});

test("a pull's sentence tells its fetch half, so the fetch sentence is not repeated", () => {
  const figure = TimePlaces.render(PULL.after, { commands: ["fetch", "pull"] });
  const caption = figure.querySelector(".tt-places-caption").textContent;
  assert.match(caption, /^pull is a fetch, then a merge/);
  assert.doesNotMatch(caption, /fetch downloads/);
});

test("each place shows the player's real files and commits, origin/main included", () => {
  const observation = { project: repo({ commits: TWO, refs: [["main", "branch", "b"], ["origin/main", "remote", "a"]], files: [file("README.md", { head: "1", index: "2", folder: "3" }), file("notes.txt", { folder: "4" })] }), github: repo({ commits: ONE, bare: true, refs: [["main", "branch", "a"]] }) };
  const figure = TimePlaces.render(observation, {});
  const paths = (area) => figure.querySelectorAll(`[data-area="${area}"] [data-path]`).map((row) => row.getAttribute("data-path"));
  assert.deepEqual(paths("folder"), ["README.md", "notes.txt"]);
  assert.deepEqual(paths("index"), ["README.md"]);
  const repository = figure.querySelector('[data-area="repository"]');
  assert.ok(repository.querySelector(`[data-hash="${full("b")}"]`));
  assert.ok(repository.querySelector('[data-label="remote:origin/main"]'));
  assert.ok(figure.querySelector('[data-area="remote"]').querySelector(`[data-hash="${full("a")}"]`));
  assert.equal(figure.querySelector(".tt-places-caption"), null);
});

test("without a remote, GitHub's place says so instead of drawing an empty graph", () => {
  const figure = TimePlaces.render({ project: repo({ commits: ONE }), github: null }, {});
  assert.match(figure.querySelector('[data-area="remote"]').textContent, /No remote yet/);
});

test("each arrow says where the work goes: pull's merge half runs from your repository through the staging area", () => {
  const figure = TimePlaces.render({ project: repo({ commits: ONE }), github: hub(ONE) }, {});
  const said = (name) => figure.querySelectorAll(".tt-arrow").find((arrow) => arrow.getAttribute("data-command") === name && arrow.getAttribute("aria-label")).getAttribute("aria-label");
  assert.equal(said("add"), "add: from the working folder to the staging area");
  assert.equal(said("push"), "push: from your repository to the remote repository");
  assert.equal(said("pull"), "pull = fetch + merge: from your repository, through the staging area, to the working folder");
  assert.equal(said("clone"), "clone (once): from the remote repository, through your repository and the staging area, to the working folder");
});

test("each arrow points the way the work moves: towards GitHub for add, commit and push, back for fetch, pull and clone", () => {
  const figure = TimePlaces.render({ project: repo({ commits: ONE }), github: hub(ONE) }, {});
  const back = figure.querySelectorAll(".tt-arrow.is-back").map((arrow) => arrow.getAttribute("data-command"));
  assert.deepEqual(back.sort(), ["clone", "fetch", "pull", "pull"]);
});

/* Renders `after`, plays the transition from `before`, and records every animate() call. */
function played(before, after, lit, reduced = false) {
  const calls = [];
  const figure = TimePlaces.render(after, { commands: lit });
  document.body.replaceChildren(figure);
  const proto = Object.getPrototypeOf(figure);
  proto.animate = function (frames, timing) {
    const call = { node: this, frames, timing, onfinish: null };
    calls.push(call);
    return call;
  };
  proto.getTotalLength = () => 100;
  const animations = TimePlaces.play(figure, { before, after, commands: lit }, reduced);
  delete proto.animate;
  delete proto.getTotalLength;
  return { figure, calls, animations };
}

const PUSH = {
  before: { project: repo({ commits: TWO, refs: [["main", "branch", "b"], ["origin/main", "remote", "a"]] }), github: repo({ commits: ONE, bare: true, refs: [["main", "branch", "a"]] }) },
  after: { project: repo({ commits: TWO, refs: [["main", "branch", "b"], ["origin/main", "remote", "b"]] }), github: repo({ commits: TWO, bare: true, refs: [["main", "branch", "b"]] }) },
};
const end = (call) => (call.timing.delay || 0) + call.timing.duration;
const isFlyer = (call) => (call.node.getAttribute("class") || "").includes("tt-flyer");
const rowIn = (figure, area, path) => figure.querySelectorAll(`[data-area="${area}"] [data-path]`).find((node) => node.getAttribute("data-path") === path);
const shaftOf = (figure, name) => figure.querySelectorAll(".tt-arrow").find((arrow) => arrow.getAttribute("data-command") === name).querySelector(".tt-arrow-shaft");

test("under reduced motion nothing moves: the lit arrow and its sentence say what happened", () => {
  const { figure, calls, animations } = played(PUSH.before, PUSH.after, ["push"], true);
  assert.deepEqual(calls, []);
  assert.deepEqual(animations, []);
  assert.equal(figure.querySelector(".tt-flyer"), null);
  assert.ok(figure.querySelector(".tt-arrow.is-push.is-active"));
});

test("a push flies the new commit, with its short hash, from your repository to GitHub", () => {
  const { figure, calls } = played(PUSH.before, PUSH.after, ["push"]);
  const flyers = figure.querySelectorAll(".tt-flyer.is-commit");
  assert.equal(flyers.length, 1);
  assert.match(flyers[0].textContent, /b000000/);
  assert.ok(calls.some((call) => call.node === flyers[0]));
});

test("GitHub's branch and your origin/main move only once the commit has landed", () => {
  const { calls } = played(PUSH.before, PUSH.after, ["push"]);
  const flight = calls.find(isFlyer);
  const slides = calls.filter((call) => call.node.getAttribute("data-label") === "branch:main" || call.node.getAttribute("data-label") === "remote:origin/main");
  assert.ok(slides.length >= 2, "GitHub's main and your origin/main both slide");
  for (const slide of slides) assert.ok(slide.timing.delay >= (flight.timing.delay || 0) + flight.timing.duration * 0.6, JSON.stringify(slide.timing));
});

test("the lit arrow draws itself as the command runs", () => {
  const { figure, calls } = played(PUSH.before, PUSH.after, ["push"]);
  const shaft = figure.querySelector(".tt-arrow.is-active .tt-arrow-shaft");
  assert.ok(calls.some((call) => call.node === shaft));
});

test("an add flies the file, by name, from the working folder to its row in the staging area, which lights as it lands", () => {
  const before = { project: repo({ commits: ONE, files: [file("README.md", { head: "1", index: "1", folder: "2" })] }), github: null };
  const after = { project: repo({ commits: ONE, files: [file("README.md", { head: "1", index: "2", folder: "2" })] }), github: null };
  const { figure, calls } = played(before, after, ["add"]);
  const flyer = figure.querySelector(".tt-flyer.is-file");
  assert.match(flyer.textContent, /README\.md/);
  const row = rowIn(figure, "index", "README.md");
  const pulse = calls.find((call) => call.node === row && "backgroundColor" in call.frames[0]);
  assert.equal(pulse.frames[0].backgroundColor, "transparent", "the row is not lit before the file lands");
  assert.notEqual(pulse.timing.fill, "backwards");
});

test("flyers are removed once they land", () => {
  const { figure, calls } = played(PUSH.before, PUSH.after, ["push"]);
  const flyer = figure.querySelector(".tt-flyer");
  calls.find((call) => call.node === flyer).onfinish();
  assert.equal(figure.querySelector(".tt-flyer"), null);
});

test("each flight travels along the lit arrow: its path passes through a point on that arrow", () => {
  const { figure, calls } = played(PUSH.before, PUSH.after, ["push"]);
  const flight = calls.find((call) => call.node === figure.querySelector(".tt-flyer"));
  assert.ok(flight.frames.some((frame) => frame.offset === 0.5), JSON.stringify(flight.frames));
});

test("a flight keeps time with its path: it eases along each leg, so it passes its middle place at the halfway time", () => {
  const { calls } = played(PULL.before, PULL.after, ["fetch", "pull"]);
  for (const flight of calls.filter(isFlyer)) {
    assert.equal(flight.timing.easing, "linear", JSON.stringify(flight.timing));
    assert.ok(flight.frames.slice(1, -1).every((frame) => frame.easing), JSON.stringify(flight.frames));
  }
});

test("a pull plays its halves in turn: the files leave your repository only once the fetched commits have arrived", () => {
  const { figure, calls } = played(PULL.before, PULL.after, ["fetch", "pull"]);
  const flights = calls.filter(isFlyer);
  const commit = flights.find((call) => call.node.getAttribute("class").includes("is-commit"));
  const files = flights.filter((call) => call.node.getAttribute("class").includes("is-file"));
  assert.equal(files.length, 2);
  for (const flight of files) assert.ok(flight.timing.delay >= commit.timing.delay + commit.timing.duration * 0.88, JSON.stringify(flight.timing));
  const draw = (name) => calls.find((call) => call.node === shaftOf(figure, name));
  assert.ok(draw("fetch") && draw("pull"), "both halves' arrows draw");
  assert.ok((draw("pull").timing.delay || 0) > (draw("fetch").timing.delay || 0), "the merge half's arrow draws second");
});

test("what a flight brings shows only as it arrives: a new row appears, a known row changes its content, the staging area before the working folder", () => {
  const { figure, calls } = played(PULL.before, PULL.after, ["fetch", "pull"]);
  const flight = calls.find((call) => isFlyer(call) && call.node.textContent === "rules.md");
  /* A lone keyframe without an offset is the end of an animation, so "starts hidden" needs offset 0. */
  const hidden = (call) => call.frames[0].opacity === 0 && call.frames[0].offset === 0;
  const appear = (area) => calls.find((call) => call.node === rowIn(figure, area, "rules.md") && hidden(call));
  for (const area of ["index", "folder"]) {
    assert.ok(appear(area) && appear(area).timing.delay > flight.timing.delay, `rules.md appears in ${area} as it arrives`);
    assert.equal(appear(area).timing.fill, "backwards", `rules.md is hidden in ${area} until then`);
    const known = rowIn(figure, area, "README.md");
    assert.ok(calls.some((call) => call.node.parentNode === known && call.node.tagName.toLowerCase() === "code" && hidden(call)), `README.md's new id in ${area}`);
  }
  assert.ok(appear("index").timing.delay < appear("folder").timing.delay, "the staging area updates on the way to the working folder");
});

test("a flight takes 520 ms from place to place, slow enough to follow", () => {
  const flight = played(PUSH.before, PUSH.after, ["push"]).calls.find(isFlyer);
  assert.equal(flight.timing.duration, 520);
});

test("a single command's motion is over within a second and a quarter, and a whole pull within 1.75 seconds", () => {
  for (const call of played(PUSH.before, PUSH.after, ["push"]).calls) assert.ok(end(call) <= 1250, JSON.stringify(call.timing));
  for (const call of played(PULL.before, PULL.after, ["fetch", "pull"]).calls) assert.ok(end(call) <= 1750, JSON.stringify(call.timing));
});

const shortOf = (name) => blob(name).slice(0, 7);
const wordsOf = (node) => (node.querySelector("em") || { textContent: "" }).textContent;

test("each file is a page with its name, the short id of its content, and the change git status lists for it there", () => {
  const files = [file("README.md", { head: "1", index: "2", folder: "3", indexChange: "modified", folderChange: "modified" }), file("notes.txt", { folder: "4", folderChange: "untracked" })];
  const figure = TimePlaces.render({ project: repo({ commits: ONE, files }), github: null }, {});
  const readme = { folder: rowIn(figure, "folder", "README.md"), index: rowIn(figure, "index", "README.md") };
  assert.equal(readme.folder.querySelector(".tt-page-name").textContent, "README.md");
  assert.equal(readme.folder.querySelector("code").textContent, shortOf("3"));
  assert.equal(readme.index.querySelector("code").textContent, shortOf("2"), "a modified file shows another id in the open box");
  assert.equal(readme.folder.querySelector("code").getAttribute("title"), blob("3"));
  assert.equal(wordsOf(readme.folder), "modified, not staged");
  assert.equal(wordsOf(readme.index), "modified, staged");
  assert.equal(wordsOf(rowIn(figure, "folder", "notes.txt")), "untracked");
  assert.equal(rowIn(figure, "index", "notes.txt"), undefined, "an untracked file is in no box");
});

test("the staging area is an open box that holds every tracked file, not only the changed ones", () => {
  const files = [file("README.md", { head: "1", index: "1", folder: "1" }), file("rules.md", { head: "5", index: "6", folder: "6", indexChange: "modified" })];
  const figure = TimePlaces.render({ project: repo({ commits: ONE, files }), github: null }, {});
  const box = figure.querySelector('[data-area="index"] .tt-open-box');
  assert.deepEqual(box.querySelectorAll("[data-path]").map((node) => node.getAttribute("data-path")), ["README.md", "rules.md"]);
});

test("a file deleted from the working folder is a missing page there, while the open box still holds it", () => {
  const files = [file("old.txt", { head: "5", index: "5", folderChange: "deleted" })];
  const figure = TimePlaces.render({ project: repo({ commits: ONE, files }), github: null }, {});
  const gone = rowIn(figure, "folder", "old.txt");
  assert.ok(gone.classList.contains("is-missing"));
  assert.equal(gone.querySelector("code"), null);
  assert.equal(wordsOf(gone), "deleted, not staged");
  assert.equal(rowIn(figure, "index", "old.txt").querySelector("code").textContent, shortOf("5"));
});

test("your repository and GitHub draw each commit as a closed box on its timeline, labelled with its short hash", () => {
  const figure = TimePlaces.render({ project: at(TWO, "b", "a"), github: hub(ONE) }, {});
  const repository = figure.querySelector('[data-area="repository"]');
  assert.equal(repository.querySelectorAll(".tt-box").length, 2);
  assert.deepEqual(repository.querySelectorAll(".map-hash").map((node) => node.textContent), [full("b").slice(0, 7), full("a").slice(0, 7)]);
  assert.equal(figure.querySelector('[data-area="remote"]').querySelectorAll(".tt-box").length, 1);
});

const COMMIT = {
  before: { project: { ...START, files: [README("1"), file("rules.md", { head: "5", index: "6", folder: "6", indexChange: "modified" })] }, github: hub(TWO) },
  after: { project: { ...MINE, files: [README("1"), file("rules.md", { head: "6", index: "6", folder: "6" })] }, github: hub(TWO) },
};

test("git commit closes a copy of the open box, holding every tracked file, and the open box keeps its pages", () => {
  const { figure, calls } = played(COMMIT.before, COMMIT.after, ["commit"]);
  const flyer = figure.querySelector(".tt-flyer.is-commit");
  assert.match(flyer.textContent, new RegExp(full("d").slice(0, 7)));
  assert.equal(flyer.querySelectorAll(".tt-flyer-pages .tt-page-icon").length, 2, "both tracked files go into the commit, the unchanged one too");
  const flaps = calls.filter((call) => flyer.contains(call.node) && call.node.getAttribute("class").includes("tt-flap"));
  assert.equal(flaps.length, 2, "the box closes as it leaves");
  assert.deepEqual(figure.querySelector('[data-area="index"] .tt-open-box').querySelectorAll("[data-path]").map((node) => node.getAttribute("data-path")), ["README.md", "rules.md"]);
});

test("a page that changes shows its old id fading out as the new one fades in, when the copy arrives", () => {
  const before = { project: repo({ commits: ONE, files: [file("README.md", { head: "1", index: "1", folder: "2", folderChange: "modified" })] }), github: null };
  const after = { project: repo({ commits: ONE, files: [file("README.md", { head: "1", index: "2", folder: "2", indexChange: "modified" })] }), github: null };
  const { figure, calls } = played(before, after, ["add"]);
  const flight = calls.find(isFlyer);
  const box = rowIn(figure, "index", "README.md");
  const was = box.querySelector(".tt-page-was");
  assert.equal(was.querySelector("code").textContent, shortOf("1"));
  const out = calls.find((call) => call.node === was);
  assert.deepEqual(out.frames.map((frame) => frame.opacity), [1, 0]);
  assert.ok(out.timing.delay > flight.timing.delay);
  const fresh = calls.find((call) => call.node === box.querySelector("code.tt-page-id") && call.frames[0].opacity === 0);
  assert.equal(fresh.timing.delay, out.timing.delay, "the new id fades in as the old one fades out");
  const words = calls.find((call) => call.node === box.querySelector("em") && call.frames[0].opacity === 0);
  assert.equal(words.timing.delay, out.timing.delay, "git's words for the new content come with it");
  out.onfinish();
  assert.equal(box.querySelector(".tt-page-was"), null, "the old id is gone once faded");
});

test("pull's merge half is drawn beside commit and add, so its arrow runs where its pages go", () => {
  const figure = TimePlaces.render(PULL.after, { commands: ["fetch", "pull"] });
  const parts = figure.querySelectorAll(".tt-arrow.is-pull");
  assert.equal(parts.length, 2);
  const beside = (name) => parts.find((part) => part.parentNode.querySelector(`.tt-arrow.is-${name}`));
  assert.ok(beside("commit"), "from your repository to the staging area, beside commit");
  assert.ok(beside("add"), "from the staging area to the working folder, beside add");
  assert.ok(parts.every((part) => part.classList.contains("is-back") && part.classList.contains("is-active")));
  assert.ok(beside("commit").getAttribute("aria-label"), "said once, by the first part");
  assert.equal(beside("add").getAttribute("aria-hidden"), "true");
});

test("both parts of pull's arrow draw as its merge half starts", () => {
  const { figure, calls } = played(PULL.before, PULL.after, ["fetch", "pull"]);
  for (const part of figure.querySelectorAll(".tt-arrow.is-pull")) assert.ok(calls.some((call) => call.node === part.querySelector(".tt-arrow-shaft")));
});

test("a command's motion stays within about two seconds, however many files it moves, a clone being the longest", () => {
  const many = Array.from({ length: 12 }, (_, index) => `file${index}.md`);
  const before = { project: { ...START, files: many.map((name) => file(name, { head: "1", index: "1", folder: "1" })) }, github: hub([C, ...TWO]) };
  const after = { project: { ...PULLED, files: many.map((name) => file(name, { head: "2", index: "2", folder: "2" })) }, github: hub([C, ...TWO]) };
  for (const call of played(before, after, ["fetch", "pull"]).calls) assert.ok(end(call) <= 1850, JSON.stringify(call.timing));
  for (const call of played({ project: repo({}), github: after.github }, after, ["clone"]).calls) assert.ok(end(call) <= 2050, JSON.stringify(call.timing));
});

test("an empty GitHub says it has no commits yet, not that you are on its branch", () => {
  const figure = TimePlaces.render({ project: repo({}), github: repo({ bare: true }) }, {});
  const remote = figure.querySelector('[data-area="remote"]').textContent;
  assert.match(remote, /No commits yet/);
  assert.doesNotMatch(remote, /You are on/);
});

test("pull's two parts each show the short word, and say the whole name aloud once", () => {
  const figure = TimePlaces.render(PULL.after, { commands: ["fetch", "pull"] });
  const parts = figure.querySelectorAll(".tt-arrow.is-pull");
  assert.deepEqual(parts.map((part) => part.querySelector(".tt-arrow-label").textContent), ["pull", "pull"]);
  assert.equal(parts.filter((part) => part.getAttribute("aria-label")).length, 1);
});

test("the staging area and your repository each say what their boxes are", () => {
  const figure = TimePlaces.render({ project: at(TWO, "b", "b"), github: hub(TWO) }, {});
  const note = (area) => figure.querySelector(`[data-area="${area}"] .tt-place-note`).textContent;
  assert.equal(note("index"), "open box: the next commit");
  assert.equal(note("repository"), "closed boxes: your commits");
  assert.equal(figure.querySelector('[data-area="folder"] .tt-place-note'), null);
});

test("a page changed in the working folder, with no command moving it, changes where it lies, and a new file's page appears", () => {
  const before = { project: repo({ commits: ONE, files: [README("1")] }), github: null };
  const after = { project: repo({ commits: ONE, files: [file("README.md", { head: "1", index: "1", folder: "2", folderChange: "modified" }), file("notes.txt", { folder: "3", folderChange: "untracked" })] }), github: null };
  const { figure, calls } = played(before, after, []);
  assert.equal(figure.querySelector(".tt-flyer"), null);
  assert.equal(rowIn(figure, "folder", "README.md").querySelector(".tt-page-was code").textContent, shortOf("1"));
  assert.ok(calls.some((call) => call.node === rowIn(figure, "folder", "notes.txt") && call.frames[0].opacity === 0));
});
