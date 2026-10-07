"use strict";

/*
 * Every word of the infographics, in one place so it can be fact-checked and translated: the
 * commands the game teaches, grouped by what they do; Git's four places and the commands that
 * move work between them; a file's states and what moves a file from one to the next. Each
 * space word sits next to the real Git term. Each item says what unlocks it: a level finished
 * ({level: id}) or a whole chapter finished ({chapter: id}). Data only. Defines one global,
 * InfographicText.
 */

/* exported InfographicText */

const InfographicText = Object.freeze({
  title: "Field guide",
  lede: "Everything the missions have taught you, in three pictures. What you have not learned yet stays locked.",
  locked: "Not learned yet",

  commands: {
    title: "Every command, by what it does",
    groups: [
      {
        title: "Look around",
        commands: [
          { command: "ls", what: "Lists the files in the current folder; ls -a lists the hidden ones too.", unlock: { level: "liftoff-aboard" } },
          { command: "git status", what: "Says which files are untracked, modified or staged, and which branch you are on.", unlock: { level: "liftoff-aboard" } },
          { command: "git diff", what: "Shows the lines you changed and have not staged; git diff --staged shows what is staged.", unlock: { chapter: "vault" } },
          { command: "git log", what: "Lists the commits, newest first, with their hash, author and message.", unlock: { chapter: "vault" } },
        ],
      },
      {
        title: "Start a repository",
        commands: [
          { command: "git init", what: "Makes the current folder a repository: Git creates the hidden .git folder.", unlock: { level: "liftoff-flag" } },
          { command: "git clone <url>", what: "Copies a remote repository, its whole history included, into a new folder.", unlock: { chapter: "branch" } },
        ],
      },
      {
        title: "Stage and commit",
        commands: [
          { command: "git add <file>", what: "Copies a file, as it is now, from the working folder into the staging area.", unlock: { level: "cargo-first" } },
          { command: "git rm --cached <file>", what: "Takes a file out of the staging area and leaves it in the working folder.", unlock: { chapter: "cargo" } },
          { command: "git restore --staged <file>", what: "Unstages a file: the staging area gets back the version of the last commit.", unlock: { chapter: "cargo" } },
          { command: "git commit -m \"<message>\"", what: "Saves the staging area as a new commit in your local repository.", unlock: { chapter: "vault" } },
        ],
      },
      {
        title: "Share with the remote",
        commands: [
          { command: "git remote add origin <url>", what: "Gives a remote repository's address a short name, usually origin. Nothing is sent.", unlock: { chapter: "mothership" } },
          { command: "git push", what: "Sends your branch's new commits to the remote repository.", unlock: { chapter: "mothership" } },
          { command: "git fetch", what: "Downloads the remote's new commits and updates origin/main; your branch and files stay as they are.", unlock: { chapter: "mothership" } },
          { command: "git pull", what: "A fetch, then a merge of the remote's branch into yours: your files update too.", unlock: { chapter: "mothership" } },
        ],
      },
      {
        title: "Branches and merges",
        commands: [
          { command: "git switch -c <branch>", what: "Creates a branch, a movable label on a commit, and switches to it.", unlock: { chapter: "branch" } },
          { command: "git switch <branch>", what: "Moves HEAD to another branch; the working folder takes that branch's files.", unlock: { chapter: "branch" } },
          { command: "git merge <branch>", what: "Joins another branch's history into yours, with a merge commit when both moved on.", unlock: { chapter: "conflict" } },
          { command: "git merge --abort", what: "Stops a merge in progress and puts everything back as it was before it.", unlock: { chapter: "conflict" } },
        ],
      },
      {
        title: "Undo",
        commands: [
          { command: "git restore <file>", what: "Replaces the working copy with the staged or committed version. Unsaved lines are gone for good.", unlock: { chapter: "undo" } },
          { command: "git revert <commit>", what: "Adds a new commit that undoes an earlier one, safe for history others already have.", unlock: { chapter: "undo" } },
          { command: "git reset <commit>", what: "Moves the current branch's label back to an earlier commit.", unlock: { chapter: "undo" } },
          { command: "git reflog", what: "Lists where HEAD has been, so a commit no branch points to can be found again.", unlock: { chapter: "undo" } },
        ],
      },
    ],
  },

  places: {
    title: "Git's four places",
    places: [
      { id: "workshop", space: "Workshop", git: "working folder", what: "Your files as you edit them. Git watches but does not save them.", unlock: { level: "liftoff-aboard" } },
      { id: "dock", space: "Cargo dock", git: "staging area", what: "The files you chose for your next commit, as they were when you added them.", unlock: { level: "cargo-first" } },
      { id: "vault", space: "Vault", git: "local repository", what: "Every commit you made, on this computer only, in the hidden .git folder.", unlock: { level: "liftoff-flag" } },
      { id: "mothership", space: "Mothership", git: "remote repository", what: "A copy of the repository on a server, such as GitHub, shared with your team.", unlock: { chapter: "mothership" } },
    ],
    moves: [
      { from: "workshop", to: "dock", command: "git add", unlock: { level: "cargo-first" } },
      { from: "dock", to: "workshop", command: "git restore --staged", unlock: { chapter: "cargo" } },
      { from: "dock", to: "vault", command: "git commit", unlock: { chapter: "vault" } },
      { from: "vault", to: "workshop", command: "git switch, git restore", unlock: { chapter: "branch" } },
      { from: "vault", to: "mothership", command: "git push", unlock: { chapter: "mothership" } },
      { from: "mothership", to: "vault", command: "git fetch", unlock: { chapter: "mothership" } },
      { from: "mothership", to: "workshop", command: "git pull (fetch, then merge)", unlock: { chapter: "mothership" } },
    ],
  },

  states: {
    title: "A file's states",
    states: [
      { id: "untracked", name: "untracked", space: "new in the workshop", what: "In the working folder, in no commit and not staged. Git does not follow it yet.", unlock: { level: "cargo-first" } },
      { id: "staged", name: "staged", space: "on the dock", what: "Its current version is in the staging area, ready for the next commit.", unlock: { level: "cargo-first" } },
      { id: "committed", name: "committed", space: "sealed in the vault", what: "Saved in a commit, and the working copy matches it: nothing to do.", unlock: { chapter: "vault" } },
      { id: "modified", name: "modified", space: "edited in the workshop", what: "Changed in the working folder since its last commit, and not staged.", unlock: { chapter: "vault" } },
    ],
    moves: [
      { from: "untracked", to: "staged", how: "git add", unlock: { level: "cargo-first" } },
      { from: "staged", to: "untracked", how: "git rm --cached (before the file's first commit)", unlock: { chapter: "cargo" } },
      { from: "staged", to: "committed", how: "git commit", unlock: { chapter: "vault" } },
      { from: "committed", to: "modified", how: "edit the file", unlock: { chapter: "vault" } },
      { from: "modified", to: "staged", how: "git add", unlock: { chapter: "vault" } },
      { from: "staged", to: "modified", how: "git restore --staged", unlock: { chapter: "cargo" } },
      { from: "modified", to: "committed", how: "git restore (drops the edit)", unlock: { chapter: "undo" } },
    ],
  },
});
