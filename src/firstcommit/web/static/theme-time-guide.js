"use strict";

/*
 * "How to read the map": the time-travel map's full guide, opened from a button in the key under
 * every map. Each section pairs a picture with Git's rule, all built on one truth: the past never
 * changes. The text is checked claim by claim against git 2.43 (docs-draft/map-guide.md holds
 * the register). Words in backticks are shown as code. The button carries a "new" mark until the
 * guide has been opened once in this browser; if storage is blocked the mark shows again next
 * time. Needs dom.js. Defines one global, TimeGuide.
 */

/* global Dom */
/* exported TimeGuide */

const TimeGuide = (function () {
  const { el } = Dom;
  const SEEN = "firstcommit.mapGuideSeen";
  const TITLE = "How to read the map";

  const INTRO = "Your project's history is drawn here as timelines of save points. Read every picture with one rule in mind: the past never changes. Git never edits a commit. When history seems to change, Git has written new commits or moved a label, and the old commits are still exactly as they were.";

  const SECTIONS = [
    {
      title: "Save point = commit",
      mark: "commit",
      picture: "A ring with a solid core.",
      points: [
        "A commit is a snapshot of every tracked file, exactly as the staging area held it when you committed, not as your working folder looked at that moment.",
        "It also records who made it and when (an author and a committer, each with a date), your message, and its parent: the commit it was made on top of.",
        "Its name, the hash, is computed from all of that. The files take part through a chain of hashes: each file's content has a hash, each folder's list of names and hashes has a hash, and the commit records the hash of the top folder.",
        "So a commit seals everything about itself. Change one letter of one file, the message, a date or the parent, and the hash comes out different: that is a different commit. This is why a commit can never be edited, only replaced by a new one.",
        "The map shows the short hash: the first seven of its 40 characters (Git uses more when seven would not be enough to tell objects apart). Hover a save point to see its full hash, author and date.",
      ],
    },
    {
      title: "Lines = parents",
      mark: "line",
      picture: "The lines between save points.",
      points: [
        "Each line runs from a commit down to its parent. A commit is always drawn above its parents, so along one line, higher means newer.",
        "Across different lines, height says nothing about dates: the map orders commits by their parents, not by the clock.",
        "A short dashed line under the lowest save point means the history goes back further than the map draws.",
      ],
    },
    {
      title: "Timeline = branch",
      mark: "branch",
      picture: "A coloured line, with a tab naming it.",
      points: [
        "A branch is only a label: a name that points at one commit. Git stores it as a small file (or one line of a shared file, `packed-refs`) holding that commit's hash.",
        "The timeline is every commit you reach from the label by following parents, back to the first commit.",
        "When you commit, Git writes the new commit with the labelled commit as its parent, then moves the label onto the new commit. The label moves; commits never do.",
        "One commit can sit on several timelines at once: on every branch that reaches it.",
        "Deleting a branch removes the label, not its commits. Commits that no label reaches leave the map. Git keeps them for a while: its cleanup, `git gc`, deletes them only once nothing refers to them any more, not even the reflog, Git's record of where HEAD and the branches have been.",
      ],
    },
    {
      title: "Now = HEAD",
      mark: "now",
      picture: "The amber dial, and the HEAD tab pointing at it.",
      points: [
        "HEAD says where you are. Usually it names a branch (`HEAD -> main`), and the branch names the commit.",
        "Your next commit attaches here: its parent is HEAD's commit, and the branch HEAD names moves onto the new commit.",
        "`git switch other` moves \"now\" to another timeline: HEAD then names `other`, and Git updates your working folder and staging area to that branch's last commit. Uncommitted changes come along when they do not collide with it; when they would be overwritten, Git refuses to switch.",
        "Travelling changes no commit. Switching back and forth leaves every commit and every branch where it was; only HEAD moves.",
        "Detached HEAD: HEAD names a commit directly, with no branch. You are visiting an old save point without a label. You can commit there, but no branch holds those commits: when you leave, Git warns you, and only the reflog remembers them. `git switch -c <name>` gives them a label.",
      ],
    },
    {
      title: "Timelines joining = merge commit",
      mark: "merge",
      picture: "A save point with an outer ring, where two lines meet.",
      points: [
        "A merge commit is a commit with two parents (Git allows more). The first parent is the commit you were on; the second is the tip of the branch you merged in.",
        "Its snapshot combines the changes of both timelines. Neither timeline is altered: their commits keep their hashes.",
        "When your branch has no commits of its own since the other one split off, `git merge` makes no merge commit: it slides your label forward to the other tip. This is a fast-forward (ask for a merge commit anyway with `--no-ff`).",
      ],
    },
    {
      title: "Milestone = tag",
      mark: "tag",
      picture: "A pennant.",
      points: ["A tag is a label that stays put: new commits do not move it. Moving a tag on purpose takes `git tag -f`."],
    },
    {
      title: "Shared archive = remote",
      mark: "archive",
      picture: "The GitHub panel. In the game it is a practice copy on your machine that stands in for GitHub.",
      points: [
        "A remote is another repository that yours knows by a name. `git clone` names it `origin`; in the game you add it with `git remote add origin <path>`.",
        "`git push` sends the commits the archive is missing, then moves the archive's branch label. Git refuses a push that is not a fast-forward, one that would leave out commits the archive's branch already has, unless you force it.",
      ],
    },
    {
      title: "Last seen in the archive = remote-tracking branch",
      mark: "remote",
      picture: "The dashed tab `origin/main`.",
      points: [
        "`origin/main` is your repository's note of where `main` was in the archive the last time your repository talked to it. Git moves it when you fetch, pull (which fetches first) or push; it never moves on its own.",
        "When someone else pushes, the archive changes but your `origin/main` does not, until your next fetch. On the map, `origin/main` shows what you last saw, not what is there now.",
        "You do not commit on `origin/main`: `git switch origin/main` refuses, and `git switch --detach origin/main` visits it with a detached HEAD.",
      ],
    },
    {
      title: "Coming later: undoing and rewriting, in the same words",
      mark: null,
      picture: "A preview: later chapters teach these. The rule still holds: no commit is ever edited.",
      points: [
        "`git revert <commit>` adds a new save point whose changes cancel an old one. The old one stays on the timeline.",
        "`git reset <commit>` moves your branch's label, and HEAD with it, back to an earlier save point. The later commits are not edited: if no label reaches them they leave the map, and `git reflog` still lists them for a while. `--soft` leaves the staging area and the working folder as they are, `--mixed` (the default) resets the staging area, and `--hard` resets both.",
        "`git commit --amend` writes a new commit in place of the last one and moves the label to it. The old commit is still in the reflog.",
        "`git rebase` copies save points onto a new base. Each copy has a new parent, so it gets a new hash. The label moves to the copies; the originals stay exactly as they were until Git's cleanup removes them.",
        "This is why rewriting commits that others already have causes trouble: they still have the originals, and Git refuses to push the rewritten branch unless you force it.",
      ],
    },
  ];

  /* Text with `code` spans, as nodes. */
  const inline = (text) => text.split("`").map((part, index) => (index % 2 ? el("code", {}, part) : part));

  function browserStorage() {
    try {
      return window.localStorage;
    } catch (error) {
      return null; /* Storage is blocked: the "new" mark shows on every visit. */
    }
  }

  /* options: storage (like localStorage; blocked or absent is fine), drawMark(name) for the small
     picture beside a section's title, page (the document). */
  function create({ storage = browserStorage(), drawMark = () => null, page = document } = {}) {
    let seen = false;
    try {
      seen = storage.getItem(SEEN) === "yes";
    } catch (error) {
      seen = false; /* Storage is blocked or absent: show the mark. */
    }

    function remember() {
      seen = true;
      for (const node of page.querySelectorAll(".tt-guide-button.is-new")) node.classList.remove("is-new");
      try {
        storage.setItem(SEEN, "yes");
      } catch (error) {
        /* Storage is blocked: the mark shows again next visit. */
      }
    }

    function open() {
      remember();
      const close = el("button", { type: "button", class: "btn btn-ghost btn-small tt-guide-close", onclick: () => dialog.close() }, "Close");
      const dialog = el("dialog", { class: "dialog tt-guide", "aria-labelledby": "tt-guide-title" },
        el("header", { class: "tt-guide-head" }, el("h2", { id: "tt-guide-title" }, TITLE), close),
        el("p", { class: "tt-guide-intro" }, INTRO),
        SECTIONS.map((section) => el("section", { class: "tt-guide-part" },
          el("h3", {}, section.mark && drawMark(section.mark), section.title),
          el("p", { class: "tt-guide-picture" }, inline(section.picture)),
          el("ul", {}, section.points.map((point) => el("li", {}, inline(point)))),
        )),
      );
      dialog.addEventListener("close", () => dialog.remove());
      page.body.append(dialog);
      dialog.showModal();
      close.focus();
      return dialog;
    }

    function button() {
      return el("button", { type: "button", class: `tt-guide-button${seen ? "" : " is-new"}`, onclick: open },
        TITLE,
        el("span", { class: "tt-new" }, "new"),
      );
    }

    return { button, open };
  }

  return { create, SECTIONS, INTRO };
})();
