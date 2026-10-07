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
 * - dock: [{path, change}] for every staged change, or null without a repository;
 * - vault: the commits HEAD reaches, newest first, [{hash, short, subject, author, labels}], each
 *   label {text, kind} with kind "head", "branch", "remote" or "tag"; null without a repository;
 * - remote: the same for the level's GitHub, or null when the level has none.
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
      dock: repository ? project.files.filter((file) => file.index_change).map((file) => ({ path: file.path, change: file.index_change })) : null,
      vault: repository ? commits(project, true) : null,
      remote: github ? commits(github, false) : null,
    };
  }

  return { read };
})();
