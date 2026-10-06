"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, record } = require("./load");

installBrowser();
const { RepoMap, TimeTheme, TimeGuide } = load(["dom.js", "map.js", "theme-time.js", "theme-time-guide.js"], ["RepoMap", "TimeTheme", "TimeGuide"]);
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
const legendText = (figure) => [...figure.querySelectorAll(".tt-legend li")].map((item) => item.textContent);

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
  const chips = [...figure.querySelectorAll(".map-label")].map((label) => label.textContent);
  for (const name of ["HEAD", "feature", "main", "origin/main", "v0.1"]) assert.ok(chips.includes(name), name);
});

test("each tab says which label it is and each line which two commits it joins, so a motion can find them", () => {
  const project = record("observation").project;
  const figure = RepoMap.render(project, { theme });
  const tabs = [...figure.querySelectorAll(".map-commits .map-label")].map((label) => label.getAttribute("data-label"));
  assert.deepEqual(tabs.sort(), ["branch:feature", "branch:main", "head", "remote:origin/main", "tag:v0.1"]);
  assert.equal(TimeTheme.tabKey({ kind: "head", text: "HEAD (detached)" }), "head");
  const lines = [...figure.querySelectorAll(".map-edges .tt-edge")].map((edge) => `${edge.getAttribute("data-from").slice(0, 7)}>${edge.getAttribute("data-to").slice(0, 7)}`);
  const parents = project.commits.flatMap((commit) => commit.parents.map((parent) => `${commit.short}>${parent.slice(0, 7)}`));
  assert.deepEqual(lines.sort(), parents.sort());
});

test("HEAD's commit wears the now mark, and no other commit does", () => {
  const figure = RepoMap.render(record("observation").project, { theme });
  assert.equal(figure.querySelectorAll(".map-commits .tt-now").length, 1);
  assert.ok(figure.querySelector(".map-commit.is-head .tt-now"));
});

test("the key says HEAD is now, the commit you are on, and the guide says the next commit attaches there", () => {
  const key = RepoMap.render(record("observation").project, { theme }).querySelector(".tt-key");
  assert.match(key.textContent, /HEAD = now: the commit you are on\./);
  assert.doesNotMatch(key.textContent, /next commit/, "the key stays one short line; the guide says the rest");
  const now = TimeGuide.SECTIONS.find((section) => section.title === "Now = HEAD");
  assert.ok(now.points.some((point) => point.startsWith("Your next commit attaches here")));
});

test("a detached HEAD is called detached in the key, with no branch", () => {
  const detached = { ...record("snapshots").one, branch: null };
  assert.match(RepoMap.render(detached, { theme }).querySelector(".tt-key").textContent, /HEAD = now: the commit you are on, with no branch \(detached HEAD\)\./);
});

test("the legend puts each metaphor next to its Git word", () => {
  const items = legendText(RepoMap.render(record("observation").project, { theme }));
  assert.deepEqual(items, [
    "save point = commit: a snapshot of every tracked file",
    "timeline = branch",
    "milestone = tag",
    "last seen in the archive = remote-tracking branch",
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

test("figures use a small map: the same save points, tabs and places at a smaller size, with no key", () => {
  const { small } = TimeTheme;
  const figure = RepoMap.render(MERGED, { theme: small });
  assert.equal(figure.querySelector(".tt-key"), null);
  assert.ok(figure.querySelector(".tt-now"));
  assert.ok(figure.querySelector('[data-label="branch:main"]'));
  assert.ok(small.sizes.row < theme.sizes.row);
  const place = (map) => map.commits.map((commit) => [commit.hash, commit.row, commit.lane]);
  assert.deepEqual(place(RepoMap.layout(MERGED, { theme: small })), place(RepoMap.layout(MERGED, { theme })));
});

test("figures can draw each commit as a closed box on its timeline, in the same places, growing in as a save point does", () => {
  const { boxes } = TimeTheme;
  const figure = RepoMap.render(MERGED, { theme: boxes });
  const commits = figure.querySelectorAll(".map-commit");
  assert.equal(commits.length, 4);
  for (const commit of commits) {
    const box = commit.querySelector(".tt-box");
    assert.ok(box && box.querySelector(".tt-save") && box.querySelector(".tt-core"), "a box with its lid, named as a save point's parts");
  }
  assert.ok(figure.querySelector(`[data-hash="${full("m")}"] .tt-box .tt-join`), "a merge commit's box has an outer frame");
  assert.ok(figure.querySelector(".map-commit.is-head .tt-now"), "HEAD's box sits in the now dial");
  assert.equal(figure.querySelector(".tt-key"), null);
  const place = (map) => map.commits.map((commit) => [commit.hash, commit.row, commit.lane]);
  assert.deepEqual(place(RepoMap.layout(MERGED, { theme: boxes })), place(RepoMap.layout(MERGED, { theme })));
});

test("the key draws each commit with the map's own shape", () => {
  const boxed = RepoMap.theme({ ...theme, shapes: { ...theme.shapes, commit: TimeTheme.boxes.shapes.commit } });
  const key = RepoMap.render(MERGED, { theme: boxed }).querySelector(".tt-key");
  assert.ok(key.querySelector(".tt-mark.is-now .tt-box"));
  assert.ok(key.querySelector(".tt-mark.is-commit .tt-box"));
  assert.ok(key.querySelector(".tt-mark.is-merge .tt-box .tt-join"));
  assert.equal(RepoMap.render(MERGED, { theme }).querySelector(".tt-key .tt-box"), null);
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

/* WCAG contrast of two #rrggbb colours. */
function contrast(one, other) {
  const luminance = (hex) => {
    const [r, g, b] = [1, 3, 5].map((at) => parseInt(hex.slice(at, at + 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const [light, dark] = [luminance(one), luminance(other)].sort((a, b) => b - a);
  return (light + 0.05) / (dark + 0.05);
}

test("the terminal's text colours stay readable on its warm background, light and dark", () => {
  const TEXT = ["foreground", "red", "green", "yellow", "blue", "magenta", "cyan", "white", "brightRed", "brightGreen", "brightYellow", "brightBlue", "brightMagenta", "brightCyan", "brightWhite"];
  for (const [name, look] of Object.entries(TimeTheme.terminal)) {
    for (const colour of TEXT) assert.ok(contrast(look[colour], look.background) >= 4.5, `${name} ${colour} ${contrast(look[colour], look.background).toFixed(2)}`);
    assert.ok(contrast(look.brightBlack, look.background) >= 3, `${name} brightBlack`);
    assert.ok(contrast(look.cursor, look.background) >= 3, `${name} cursor`);
  }
});

test("every picture the guide names has a small drawing, hidden from screen readers", () => {
  for (const name of TimeGuide.SECTIONS.map((section) => section.mark).filter(Boolean)) {
    const drawing = TimeTheme.mark(name);
    assert.equal(drawing.getAttribute("aria-hidden"), "true", name);
    assert.ok(drawing.children.length > 0, name);
  }
});
