"use strict";

/*
 * Sample playground records, in the shapes agreed with the engine (docs/drafts/playground/plan.md,
 * E3), built from records.json's snapshots until the game's own records land there.
 */

const { record } = require("./load");

const hash = (name) => `${name}`.padEnd(40, "0");
const commit = (name, parents = [], author = "You") => ({ hash: hash(name), short: hash(name).slice(0, 7), parents: parents.map(hash), subject: `Commit ${name}`, author, time: 0 });
const ref = (name, at, kind = "branch") => ({ name, kind, target: hash(at) });
const file = (path, more = {}) => ({ path, head: "h", index: "h", folder: "h", head_mode: "100644", index_mode: "100644", folder_mode: "100644", ignored: false, conflicted: false, repository: true, index_change: null, folder_change: null, ...more });

/* a <- b <- c on main, bright-lights off c. */
function snapshot({ refs = [ref("main", "c"), ref("origin/main", "c", "remote"), ref("bright-lights", "l")], branch = "main", commits = null, files = [file("notes.txt")], operation = null } = {}) {
  return {
    ...record("snapshots").one,
    exists: true,
    head: (refs.find((r) => r.name === branch) || refs[0]).target,
    branch,
    commits: commits || [commit("l", ["c"]), commit("c", ["b"]), commit("b", ["a"]), commit("a")],
    refs,
    remotes: [{ name: "origin", url: "../github.com/moonbase/project.git" }],
    files,
    operation,
  };
}

const START_IDS = ["empty", "changes", "branches", "alex-ahead", "both", "conflict", "lost"];
const OPENS = { empty: "desk", changes: "desk", branches: "chain", "alex-ahead": "history", both: "history", conflict: "conflict", lost: "movelog" };
const USES = { changes: "Time travel", branches: "Name tags", "alex-ahead": "The mothership", both: "Collisions", conflict: "Collisions", lost: "Time travel" };

const starts = () => START_IDS.map((id) => ({
  id,
  title: `Start ${id}`,
  blurb: `What ${id} holds.`,
  uses: USES[id] || null,
  view: OPENS[id],
  alex: id === "alex-ahead" || id === "conflict",
  mothership: id !== "empty",
}));

/* GET /api/playground: the starts, the current one and its preferences. */
function playground({ start = "branches", started = "s1", prefs = {} } = {}) {
  const current = start ? { start, started } : null;
  const opening = start ? starts().find((item) => item.id === start) : null;
  return {
    starts: starts(),
    current,
    prefs: opening ? { view: opening.view, alex: opening.alex, whose: "you", ...prefs } : null,
  };
}

/* One person's side of the playground's lab. */
function person({ project = snapshot(), commands = [], reflog = [], ghosts = [], texts = [], graph = ["* ccccccc (HEAD -> main) Commit c"], conflicts = [], markers = [] } = {}) {
  return { project, commands, reflog, ghosts, texts, graph, conflicts, markers };
}

/* GET /api/playground/observe. */
function observation({ start = "branches", started = "s1", you = person(), alex = person({ project: snapshot({ refs: [ref("main", "c"), ref("origin/main", "c", "remote")] }) }), github = snapshot({ refs: [ref("main", "c")] }) } = {}) {
  return { start, started, github, you, alex };
}

/* checklist.txt with one conflict block, as the server parses it. */
const marked = (read = "r1") => ({
  path: "checklist.txt",
  read,
  parts: [
    { kind: "same", lines: ["LAUNCH CHECKLIST", "1. Seal the hatch"] },
    { kind: "block", you: ["4. Course: the Moon"], them: ["4. Course: Jupiter"], you_label: "HEAD", them_label: "94b6459f310f9ec74b15d5f70e207bdf95b25026" },
    { kind: "same", lines: ["5. Music: off"] },
  ],
});

module.exports = { hash, commit, ref, file, snapshot, starts, playground, person, observation, marked, START_IDS };
