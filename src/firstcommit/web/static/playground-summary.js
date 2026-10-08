"use strict";

/*
 * The playground's picture folded into one line, as a phone shows it above the terminal
 * (docs/drafts/playground/plan.md): the view's name, whose repository it is while Alex is shown,
 * where HEAD is, how the branch stands against its origin/ bookmark, and how many files are
 * changed and not committed. It reads one snapshot and runs nothing. Needs strings.js. Defines
 * one global, PlaygroundSummary.
 *
 * line({view, whose, project}) the line: `view` a playground view, `whose` "you" or "alex" while
 *   Alex is shown (null otherwise), `project` the snapshot of that person's repository.
 */

/* global Strings */
/* exported PlaygroundSummary */

const PlaygroundSummary = (function () {
  const { t } = Strings;

  /* The commits `from` reaches, itself included. */
  function reached(byHash, from) {
    const seen = new Set();
    const queue = [from];
    while (queue.length) {
      const hash = queue.pop();
      if (seen.has(hash) || !byHash.has(hash)) continue;
      seen.add(hash);
      queue.push(...byHash.get(hash).parents);
    }
    return seen;
  }

  /* How HEAD's branch stands against origin/<branch>, or null without that bookmark. */
  function standing(project) {
    const tip = (name) => (project.refs.find((ref) => ref.name === name) || {}).target;
    const upstream = `origin/${project.branch}`;
    const mine = tip(project.branch);
    const theirs = tip(upstream);
    if (!mine || !theirs) return null;
    const byHash = new Map(project.commits.map((commit) => [commit.hash, commit]));
    const ours = reached(byHash, mine);
    const bookmark = reached(byHash, theirs);
    const ahead = [...ours].filter((hash) => !bookmark.has(hash)).length;
    const behind = [...bookmark].filter((hash) => !ours.has(hash)).length;
    const params = { branch: project.branch, upstream, ahead, behind, count: ahead || behind };
    let key = "pg.sum.even";
    if (ahead && behind) key = "pg.sum.diverged";
    else if (ahead) key = "pg.sum.ahead";
    else if (behind) key = "pg.sum.behind";
    return t(key, params);
  }

  function where(project) {
    const changed = project.files.filter((file) => !file.ignored && (file.index_change || file.folder_change)).length;
    const head = project.branch ? t("pg.sum.head", { branch: project.branch }) : t("pg.sum.detached", { short: project.head.slice(0, 7) });
    return [
      head,
      project.commits.length ? standing(project) : t("pg.sum.nocommits"),
      changed && t("pg.sum.changed", { count: changed }),
      project.operation && t("pg.sum.operation", { operation: project.operation }),
    ].filter(Boolean).join(" · ");
  }

  function line({ view, whose, project }) {
    const state = project.exists ? where(project) : t("pg.sum.norepo");
    const about = whose ? `${t(`pg.whose.${whose}`)}: ${state}` : state;
    return `${t(`pg.view.${view}`)} · ${about}`;
  }

  return { line };
})();
