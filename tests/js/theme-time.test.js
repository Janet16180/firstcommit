"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, record } = require("./load");

installBrowser();
const { RepoMap, TimeTheme } = load(["dom.js", "map.js", "theme-time.js"], ["RepoMap", "TimeTheme"]);
const theme = TimeTheme.map;

const full = (name) => name.padEnd(40, "0");

/* A snapshot on main from commits newest first, as [name, [parent names]]. */
function history(commits, refs = [["main", "branch", commits[0][0]]]) {
  return {
    ...record("snapshots").one,
    head: full(commits[0][0]),
    branch: "main",
    commits: commits.map(([name, parents], index) => ({
      hash: full(name), short: full(name).slice(0, 7), parents: parents.map(full), subject: `Commit ${name}`, author: "Alex Kim", time: 1000 - index,
    })),
    refs: refs.map(([name, kind, target]) => ({ name, kind, target: full(target) })),
  };
}

const MERGED = history([["m", ["c", "b"]], ["c", ["a"]], ["b", ["a"]], ["a", []]]);
const legendText = (figure) => figure.querySelectorAll(".tt-legend li").map((item) => item.textContent);

test("every save point still shows its commit's real short hash and subject, and its full hash in a tooltip", () => {
  const project = record("observation").project;
  const figure = RepoMap.render(project, { theme });
  for (const commit of project.commits) {
    assert.ok(figure.textContent.includes(commit.short), commit.short);
    assert.ok(figure.textContent.includes(commit.subject), commit.subject);
    assert.ok(figure.textContent.includes(commit.hash), commit.hash);
  }
});

test("branch, remote-tracking branch and tag names are drawn exactly as Git names them", () => {
  const figure = RepoMap.render(record("observation").project, { theme });
  const chips = figure.querySelectorAll(".map-label").map((label) => label.textContent);
  for (const name of ["HEAD", "feature", "main", "origin/main", "v0.1"]) assert.ok(chips.includes(name), name);
});

test("HEAD's commit wears the now mark, and no other commit does", () => {
  const figure = RepoMap.render(record("observation").project, { theme });
  assert.equal(figure.querySelectorAll(".map-commits .tt-now").length, 1);
  assert.ok(figure.querySelector(".map-commit.is-head .tt-now"));
});

test("the key says HEAD is now, the commit the next commit goes on top of", () => {
  const key = RepoMap.render(record("observation").project, { theme }).querySelector(".tt-key");
  assert.match(key.textContent, /HEAD = now/);
  assert.match(key.textContent, /commit you are on/);
  assert.match(key.textContent, /next commit/);
});

test("a detached HEAD is called detached in the key, with no branch", () => {
  const detached = { ...record("snapshots").one, branch: null };
  assert.match(RepoMap.render(detached, { theme }).querySelector(".tt-key").textContent, /no branch \(detached HEAD\)/);
});

test("the legend puts each metaphor next to its Git word", () => {
  const items = legendText(RepoMap.render(record("observation").project, { theme }));
  assert.deepEqual(items, [
    "save point = commit: a snapshot of every tracked file",
    "timeline = branch",
    "milestone = tag",
    "last seen in the shared archive = remote-tracking branch",
  ]);
});

test("the legend explains only what the map shows", () => {
  const one = RepoMap.layout(record("snapshots").one, { theme });
  assert.deepEqual(TimeTheme.legend(one), ["commit", "branch"]);
  assert.deepEqual(TimeTheme.legend(RepoMap.layout(MERGED, { theme })), ["commit", "branch", "merge"]);
  const detachedAlone = RepoMap.layout({ ...record("snapshots").one, branch: null, refs: [] }, { theme });
  assert.deepEqual(TimeTheme.legend(detachedAlone), ["commit"]);
});

test("a merge commit has its own mark and adds timelines joining to the legend", () => {
  const figure = RepoMap.render(MERGED, { theme });
  assert.equal(figure.querySelectorAll(".map-commits .tt-join").length, 1);
  assert.ok(figure.querySelector(".map-commit.is-merge .tt-join"));
  assert.ok(legendText(figure).includes("timelines joining = merge commit"));
});

test("the stand-in GitHub shows no now mark and no key", () => {
  const figure = RepoMap.render(record("observation").github, { theme, showHead: false });
  assert.equal(figure.querySelector(".tt-now"), null);
  assert.equal(figure.querySelector(".tt-key"), null);
});

test("the theme changes the look, never where a commit goes", () => {
  const project = record("observation").project;
  const place = (map) => map.commits.map((commit) => [commit.hash, commit.row, commit.lane]);
  assert.deepEqual(place(RepoMap.layout(project, { theme })), place(RepoMap.layout(project)));
});

test("the three areas keep the game's words", () => {
  assert.deepEqual(theme.words.areas, RepoMap.DEFAULT_THEME.words.areas);
  assert.deepEqual(theme.words.states, RepoMap.DEFAULT_THEME.words.states);
});

test("the panel titles keep Git's words next to the metaphor", () => {
  assert.match(TimeTheme.panel.project, /repository/);
  assert.match(TimeTheme.panel.github, /^GitHub/);
  assert.equal(TimeTheme.panel.areas, "The three areas");
  assert.equal(TimeTheme.panel.feed, "What just happened");
});

test("a branch without commits says the first commit starts its timeline", () => {
  assert.match(RepoMap.render(record("snapshots").unborn, { theme }).textContent, /main, which has no commits yet\. Your first commit starts its timeline\./);
});
