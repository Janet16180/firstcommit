"use strict";

/*
 * What the level screen's four zones hold, read from one observation (firstcommit/game.py's
 * Observation): the workshop (the working folder), the cargo dock (the staging area), the vault
 * (the local repository's history) and the mothership (the level's GitHub). It only reads the
 * snapshots the server sent; nothing here runs or imitates git. Defines one global, Zones.
 *
 * read(observation) gives {repository, workshop, dock, vault, remote}:
 * - repository: whether the folder holds a repository;
 * - workshop: [{path, state}] for every file in the folder that git does not ignore, state one of
 *   "none" (no repository), "new", "edited", "deleted", "staged" or "saved";
 * - dock: [{path, change, version}] for every staged change (version: the staged content's hash,
 *   null for a deletion), or null without a repository;
 * - vault: the commits HEAD reaches, newest first, [{hash, short, subject, author, labels}], each
 *   label {text, kind} with kind "head", "branch", "remote" or "tag"; null without a repository;
 * - remote: the same for the level's GitHub, or null when the level has none.
 *
 * moves(before, after, typed) says how to animate the change between two such readings: the
 * arrows to light ("add", "commit", "push", "pull"), the items that fly ({from, to}, each
 * "<zone>:<path or hash>") and the zones that switch on. `typed` names the git commands that
 * succeeded meanwhile (typed.js): when there are any, only the moves they make are drawn; with
 * none, the change was made outside the game's terminal and is drawn as it is.
 */

/* exported Zones */

const Zones = (function () {
  const FOLDER_STATES = { untracked: "new", modified: "edited", typechange: "edited", deleted: "deleted" };

  function workshopState(file, repository) {
    let state = "saved";
    if (!repository) state = "none";
    else if (file.folder_change in FOLDER_STATES) state = FOLDER_STATES[file.folder_change];
    else if (file.index_change) state = "staged";
    return state;
  }

  const inWorkshop = (file) => !file.ignored && (file.folder !== null || file.folder_change === "deleted");

  /* The commits HEAD reaches, in the snapshot's order (newest first). */
  function history(snapshot) {
    const byHash = new Map(snapshot.commits.map((commit) => [commit.hash, commit]));
    const reached = new Set();
    const waiting = snapshot.head ? [snapshot.head] : [];
    while (waiting.length) {
      const hash = waiting.pop();
      if (reached.has(hash) || !byHash.has(hash)) continue;
      reached.add(hash);
      waiting.push(...byHash.get(hash).parents);
    }
    return snapshot.commits.filter((commit) => reached.has(commit.hash));
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

  const commits = (snapshot, showHead) => history(snapshot).map((commit) => ({
    hash: commit.hash,
    short: commit.short,
    subject: commit.subject,
    author: commit.author,
    labels: labels(snapshot, commit.hash, showHead),
  }));

  function read({ project, github }) {
    const repository = project.exists;
    return {
      repository,
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
    { kind: "pull", commands: ["pull", "fetch", "merge"], arrow: "pull", flights: (before, after) => added(after.vault, before.vault).filter((hash) => hashes(before.remote).has(hash)).map((hash) => [`remote:${hash}`, `vault:${hash}`]) },
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

  function moves(before, after, typed) {
    const allowed = (move) => typed.length === 0 || move.commands.some((command) => typed.includes(command));
    const made = MOVES.filter(allowed).map((move) => ({ ...move, pairs: move.flights(before, after) })).filter((move) => move.pairs.length);
    const flights = made.flatMap((move) => move.pairs.map(([from, to]) => ({ from, to })));
    const lit = [...new Set(made.map((move) => move.arrow).filter(Boolean))];
    const wake = [];
    if (!before.repository && after.repository) wake.push("dock", "vault");
    if (before.remote === null && after.remote !== null) wake.push("remote");
    return { lit, flights: [...new Map(flights.map((flight) => [`${flight.from}>${flight.to}`, flight])).values()], wake };
  }

  return { read, moves };
})();
