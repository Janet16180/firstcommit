"use strict";

/*
 * The captain's chart (docs/drafts/sector5/5-5): a challenge's target, drawn as the same chain
 * with each name where it should end up and HEAD riding the one it names. A name gets a tick
 * once yours sits on the same commit, and three counts under the chart say how far off you are:
 * names in place, HEAD in place, and names the chart does not have. They never say what to type.
 * Commits are matched by subject, since a lab's hashes change from one start to the next.
 * Needs dom.js, strings.js and chain.js. Defines one global, TargetChart.
 *
 * create() {element, update(project, target)}: target = {names: [{name, subject}], head}.
 */

/* global Dom, Strings, Chain */
/* exported TargetChart */

const TargetChart = (function () {
  const { el } = Dom;
  const { t } = Strings;

  /* The chart as a snapshot of its own: the project's commits, the chart's names on them. */
  function charted(project, target) {
    const bySubject = (subject) => project.commits.find((commit) => commit.subject === subject);
    const refs = target.names.filter(({ subject }) => bySubject(subject)).map(({ name, subject }) => ({ name, kind: name.includes("/") ? "remote" : "branch", target: bySubject(subject).hash }));
    const head = refs.find((ref) => ref.name === target.head);
    return { ...project, refs, branch: target.head, head: head ? head.target : null };
  }

  function create() {
    const title = el("h4", { class: "target-title" });
    const chain = Chain.create();
    const counts = el("ul", { class: "target-checks" });
    const element = el("section", { class: "target" }, title, chain.element, counts);

    function update(project, target) {
      const chart = charted(project, target);
      const subjectOf = (hash) => (project.commits.find((commit) => commit.hash === hash) || {}).subject;
      const placed = target.names.filter(({ name, subject }) => project.refs.some((ref) => ref.name === name && subjectOf(ref.target) === subject)).map(({ name }) => name);
      const wanted = new Set(target.names.map(({ name }) => name));
      const extra = project.refs.filter((ref) => ref.kind === "branch" && !wanted.has(ref.name)).length;
      const headOk = project.branch === target.head;
      title.textContent = t("target.title");
      chain.update({ project: chart, github: null, teammate: null, ghosts: [], show: { mothership: false, alex: false, ghosts: false }, look: [], walk: false, placed, legend: false });
      const check = (ok, text) => el("li", { class: ok ? "target-check is-ok" : "target-check" }, text);
      counts.replaceChildren(
        check(placed.length === target.names.length, t("target.names", { count: placed.length, total: target.names.length })),
        check(headOk, t("target.head")),
        check(extra === 0, t("target.extra", { count: extra })));
    }

    return { element, update };
  }

  return { create };
})();
