"use strict";

/*
 * The captain's chart (docs/drafts/sector5/5-5): a challenge's target, drawn as the same chain
 * with each name where it should end up and HEAD riding the one it names. A name gets a tick
 * once yours sits on the same commit, and three counts under the chart say how far off you are:
 * names in place, HEAD in place, and names the chart does not have. They never say what to type.
 * The chart's commits are the level's own labels, since a lab's hashes change from one start to
 * the next; a name is in place when yours is on a commit with the same subject. Needs dom.js,
 * strings.js and chain.js. Defines one global, TargetChart.
 *
 * create() {element, update(project, target)}: target is LevelView.target, {commits: [{id,
 *   parents, subject}], names: {name: id}, head}.
 */

/* global Dom, Strings, Chain */
/* exported TargetChart */

const TargetChart = (function () {
  const { el } = Dom;
  const { t } = Strings;

  /* The chart as a snapshot of its own: the goal tree's commits, by their labels, and its names.
     A commit you have takes your commit's time, so the chart orders its lines as your chain does. */
  function charted(target, project) {
    const timeOf = (subject, at) => (project.commits.find((commit) => commit.subject === subject) || { time: target.commits.length - at }).time;
    const commits = target.commits.map((commit, at) => ({ hash: commit.id, short: "", parents: commit.parents, subject: commit.subject, author: "", time: timeOf(commit.subject, at) }));
    const refs = Object.entries(target.names).map(([name, id]) => ({ name, kind: name.includes("/") ? "remote" : "branch", target: id }));
    return { exists: true, bare: false, head: target.names[target.head], branch: target.head, commits, refs, remotes: [], files: [] };
  }

  function create() {
    const title = el("h4", { class: "target-title" });
    const chain = Chain.create();
    const counts = el("ul", { class: "target-checks" });
    const element = el("section", { class: "target" }, title, chain.element, counts);

    function update(project, target) {
      const subjectOf = (commits, hash, key) => (commits.find((commit) => commit[key] === hash) || {}).subject;
      const wanted = Object.entries(target.names);
      const placed = wanted.filter(([name, id]) => project.refs.some((ref) => ref.name === name && subjectOf(project.commits, ref.target, "hash") === subjectOf(target.commits, id, "id"))).map(([name]) => name);
      const extra = project.refs.filter((ref) => ref.kind === "branch" && !(ref.name in target.names)).length;
      title.textContent = t("target.title");
      chain.update({ project: charted(target, project), github: null, teammate: null, ghosts: [], show: { mothership: false, alex: false, ghosts: false }, look: [], walk: false, placed, legend: false });
      const check = (ok, text) => el("li", { class: ok ? "target-check is-ok" : "target-check" }, text);
      counts.replaceChildren(
        check(placed.length === wanted.length, t("target.names", { count: placed.length, total: wanted.length })),
        check(project.branch === target.head && placed.includes(target.head), t("target.head")),
        check(extra === 0, t("target.extra", { count: extra })));
    }

    return { element, update };
  }

  return { create };
})();
