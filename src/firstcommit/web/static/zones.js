"use strict";

/*
 * What the level screen's four zones hold, read from one observation (firstcommit/game.py's
 * Observation): the workshop (the working folder), the cargo dock (the staging area), the vault
 * (the local repository's history) and the mothership (the level's GitHub). It only reads the
 * snapshots the server sent; nothing here runs or imitates git. Defines one global, Zones.
 *
 * read(observation) gives {repository, operation, workshop, dock, vault, remote}:
 * - repository: whether the folder holds a repository;
 * - operation: the merge, rebase, cherry-pick, revert or bisect in progress, or null;
 * - workshop: [{path, state}] for every file in the folder that git does not ignore, state one of
 *   "none" (no repository), "conflicted", "new", "edited", "deleted", "staged" or "saved";
 * - dock: [{path, change, version}] for every staged change (version: the staged content's hash,
 *   null for a deletion), or null without a repository;
 * - vault: every commit of every branch, children before parents, [{hash, short, subject, author,
 *   parents, lane, revert, labels}] (revert: the commit undoes another, by git's own message): `lane` is its column in the drawn graph (0 for the first line of
 *   history; a branch that splits off takes the next free one), each label {text, kind} with
 *   kind "head", "branch", "remote" or "tag"; null without a repository;
 * - remote: the same for the level's GitHub, or null when the level has none.
 *
 * moves(before, after, typed, refused) says how to animate the change between two such readings:
 * - lit: the arrows to light ("add", "commit", "push", "pull");
 * - flights: the items that fly, {from, to}, each a key: "<zone>:<path or hash>" for a file or
 *   a capsule, "<zone>-ref:<branch, or HEAD>" for a label (a label that moved slides);
 * - wake: the zones that switched on;
 * - fades: the capsules that left every branch (a reset); appears: those that came back or were
 *   made without flying in from anywhere;
 * - bounces: {from, to}, a capsule thrown at a zone that sends it back (a refused push);
 * - cracks: the files that just became conflicted; rises: the revert capsules just made (they rise
 *   in upside down, and are not in appears).
 * `typed` names the git commands that succeeded meanwhile and `refused` those that failed
 * (typed.js): when any succeeded, only the flights they make are drawn; with none, the change
 * was made outside the game's terminal and is drawn as it is.
 */

/* exported Zones */

const Zones = (function () {
  const FOLDER_STATES = { untracked: "new", modified: "edited", typechange: "edited", deleted: "deleted" };

  function workshopState(file, repository) {
    let state = "saved";
    if (!repository) state = "none";
    else if (file.conflicted) state = "conflicted";
    else if (file.folder_change in FOLDER_STATES) state = FOLDER_STATES[file.folder_change];
    else if (file.index_change) state = "staged";
    return state;
  }

  const inWorkshop = (file) => !file.ignored && (file.folder !== null || file.folder_change === "deleted");

  /* The commits with every child before its parents, otherwise in the snapshot's order. */
  function topological(list) {
    const known = new Set(list.map((commit) => commit.hash));
    const children = new Map(list.map((commit) => [commit.hash, 0]));
    for (const commit of list) for (const parent of commit.parents) if (known.has(parent)) children.set(parent, children.get(parent) + 1);
    const ordered = [];
    const left = [...list];
    while (left.length) {
      const next = left.findIndex((commit) => children.get(commit.hash) === 0);
      const [commit] = left.splice(next < 0 ? 0 : next, 1);
      ordered.push(commit);
      for (const parent of commit.parents) if (known.has(parent)) children.set(parent, children.get(parent) - 1);
    }
    return ordered;
  }

  /* Each commit's lane: it takes the lane that waits for it (the leftmost), else the first free
     one; its first parent then waits in that lane, and any other parent in a free one. */
  function lanes(ordered) {
    const waiting = [];
    return ordered.map((commit) => {
      let lane = waiting.indexOf(commit.hash);
      if (lane < 0) lane = waiting.includes(null) ? waiting.indexOf(null) : waiting.length;
      waiting.forEach((hash, index) => {
        if (hash === commit.hash) waiting[index] = null;
      });
      const [first = null, ...others] = commit.parents;
      waiting[lane] = first;
      for (const parent of others.filter((hash) => !waiting.includes(hash))) {
        const free = waiting.indexOf(null);
        waiting[free < 0 ? waiting.length : free] = parent;
      }
      while (waiting.length && waiting[waiting.length - 1] === null) waiting.pop();
      return lane;
    });
  }

  /* The labels on one commit: HEAD (with its branch) first, then the other refs in the snapshot's order. */
  function labels(snapshot, hash, showHead) {
    const onHead = showHead && snapshot.head === hash;
    const head = onHead ? [{ text: snapshot.branch ? `HEAD → ${snapshot.branch}` : "HEAD", kind: "head" }] : [];
    const refs = snapshot.refs
      .filter((ref) => ref.target === hash && !(onHead && ref.kind === "branch" && ref.name === snapshot.branch))
      .map((ref) => ({ text: ref.name, kind: ref.kind }));
    return [...head, ...refs];
  }

  function commits(snapshot, showHead) {
    const ordered = topological(snapshot.commits);
    const placed = lanes(ordered);
    return ordered.map((commit, index) => ({
      hash: commit.hash,
      short: commit.short,
      subject: commit.subject,
      author: commit.author,
      parents: commit.parents,
      lane: placed[index],
      revert: commit.subject.startsWith("Revert \""),
      labels: labels(snapshot, commit.hash, showHead),
    }));
  }

  function read({ project, github }) {
    const repository = project.exists;
    return {
      repository,
      operation: project.operation,
      workshop: project.files.filter(inWorkshop).map((file) => ({ path: file.path, state: workshopState(file, repository) })),
      dock: repository ? project.files.filter((file) => file.index_change).map((file) => ({ path: file.path, change: file.index_change, version: file.index })) : null,
      vault: repository ? commits(project, true) : null,
      remote: github ? commits(github, false) : null,
    };
  }

  /* Each kind of move: the git commands that make it, its arrow, and its flights between two readings. */
  const MOVES = [
    { kind: "add", commands: ["add", "commit", "stage"], arrow: "add", flights: (before, after) => newOnDock(before, after).map((path) => [`workshop:${path}`, `dock:${path}`]) },
    { kind: "unstage", commands: ["restore", "reset", "rm"], arrow: null, flights: (before, after) => leftDock(before, after).map((path) => [`dock:${path}`, `workshop:${path}`]) },
    { kind: "commit", commands: ["commit", "merge", "cherry-pick", "revert"], arrow: "commit", flights: (before, after) => sealed(before, after) },
    { kind: "push", commands: ["push"], arrow: "push", flights: (before, after) => added(after.remote, before.remote).map((hash) => [`vault:${hash}`, `remote:${hash}`]) },
    { kind: "pull", commands: ["pull", "fetch", "merge", "clone"], arrow: "pull", flights: (before, after) => added(after.vault, before.vault).filter((hash) => hashes(before.remote).has(hash)).map((hash) => [`remote:${hash}`, `vault:${hash}`]) },
    { kind: "merge", commands: ["merge", "pull"], arrow: null, flights: (before, after) => joined(before, after) },
    { kind: "slide", commands: null, arrow: null, flights: (before, after) => [...slid(before, after, "vault"), ...slid(before, after, "remote")] },
  ];

  const hashes = (list) => new Set((list || []).map((commit) => commit.hash));
  /* The commits of `now` that `was` did not have. */
  const added = (now, was) => (now || []).map((commit) => commit.hash).filter((hash) => !hashes(was).has(hash));
  const docked = (zones) => new Set((zones.dock || []).map((item) => `${item.path}\0${item.version}`));
  const newOnDock = (before, after) => (after.dock || []).filter((item) => !docked(before).has(`${item.path}\0${item.version}`)).map((item) => item.path);
  const leftDock = (before, after) => (before.dock || []).filter((item) => !(after.dock || []).some((now) => now.path === item.path)).map((item) => item.path);

  /* What was on the dock flies into the newest new commit of the vault, if any (one made here, not pulled). */
  function sealed(before, after) {
    const fresh = added(after.vault, before.vault).filter((hash) => !hashes(before.remote).has(hash));
    return fresh.length ? (before.dock || []).map((item) => [`dock:${item.path}`, `vault:${fresh[0]}`]) : [];
  }

  /* A new merge capsule draws a line in from each of its parents. */
  function joined(before, after) {
    const fresh = new Set(added(after.vault, before.vault));
    const had = hashes(before.vault);
    return (after.vault || []).filter((commit) => fresh.has(commit.hash) && commit.parents.length > 1)
      .flatMap((commit) => commit.parents.filter((parent) => had.has(parent)).map((parent) => [`vault:${parent}`, `vault:${commit.hash}`]));
  }

  /* Where each label sits in a zone: its key (a branch's name, or HEAD) and its capsule. */
  function labelled(list) {
    const at = new Map();
    for (const commit of list || []) for (const label of commit.labels) at.set(label.kind === "head" ? "HEAD" : label.text, commit.hash);
    return at;
  }

  /* The labels of a zone that now sit on another capsule. */
  function slid(before, after, zone) {
    const was = labelled(before[zone]);
    return [...labelled(after[zone])].filter(([key, hash]) => was.has(key) && was.get(key) !== hash).map(([key]) => [`${zone}-ref:${key}`, `${zone}-ref:${key}`]);
  }

  /* A refused push throws the HEAD capsule at the mothership, which sends it back. */
  function bounced(after, refused) {
    const top = (after.vault || []).find((commit) => commit.labels.some((label) => label.kind === "head"));
    return refused.includes("push") && top && after.remote !== null ? [{ from: `vault:${top.hash}`, to: "remote" }] : [];
  }

  /* The workshop's files that just became conflicted. */
  function cracked(before, after) {
    const was = new Set(before.workshop.filter((file) => file.state === "conflicted").map((file) => file.path));
    return after.workshop.filter((file) => file.state === "conflicted" && !was.has(file.path)).map((file) => `workshop:${file.path}`);
  }

  function moves(before, after, typed, refused = []) {
    const allowed = (move) => typed.length === 0 || move.commands === null || move.commands.some((command) => typed.includes(command));
    const made = MOVES.filter(allowed).map((move) => ({ ...move, pairs: move.flights(before, after) })).filter((move) => move.pairs.length);
    const flights = made.flatMap((move) => move.pairs.map(([from, to]) => ({ from, to })));
    const lit = [...new Set(made.map((move) => move.arrow).filter(Boolean))];
    const wake = [];
    if (!before.repository && after.repository) wake.push("dock", "vault");
    if (before.remote === null && after.remote !== null) wake.push("remote");
    const landed = new Set(flights.map((flight) => flight.to));
    const zones = ["vault", "remote"];
    const fades = zones.flatMap((zone) => added(before[zone], after[zone]).map((hash) => `${zone}:${hash}`));
    const reverts = new Set(zones.flatMap((zone) => (after[zone] || []).filter((commit) => commit.revert).map((commit) => `${zone}:${commit.hash}`)));
    const fresh = zones.flatMap((zone) => (before[zone] ? added(after[zone], before[zone]) : []).map((hash) => `${zone}:${hash}`)).filter((key) => !landed.has(key));
    const unique = [...new Map(flights.map((flight) => [`${flight.from}>${flight.to}`, flight])).values()];
    return { lit, flights: unique, wake, fades, appears: fresh.filter((key) => !reverts.has(key)), bounces: bounced(after, refused), cracks: cracked(before, after), rises: fresh.filter((key) => reverts.has(key)) };
  }

  return { read, moves };
})();
