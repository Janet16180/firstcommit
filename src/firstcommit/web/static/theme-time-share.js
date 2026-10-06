"use strict";

/*
 * "Share a file with Alex": your computer, GitHub and Alex's computer side by side, in the four
 * places' pictures (pages, an open box, closed boxes on a timeline). Each computer stacks its
 * working folder, its open box and its repository, so a file you share travels down your side,
 * across GitHub and up Alex's. The figure plays one step at a time, each with one caption that
 * says what Alex can see: committing shares nothing, pushing puts the commit on GitHub, not on
 * Alex's computer, and only Alex's pull brings it there, first its fetch half, then its merge
 * half.
 *
 * A step is {id, actor ("you" or "alex"), commands, transcript, before, after, events}: real git,
 * a bare GitHub and two clones, a snapshot of each after every step (the generator records the
 * pull's two halves separately and checks they end where git pull does). lit(step) says which of
 * the actor's arrows light, from the actor's and GitHub's feed events; render(step) draws it;
 * play(figure, step) runs it with TimePlaces' motions inside the actor's computer. Every caption
 * goes to the fact-check (docs-draft/share.md). Needs dom.js, map.js, theme-time.js,
 * theme-time-motion.js and theme-time-places.js. Defines one global, TimeShare.
 */

/* global Dom, TimePlaces */
/* exported TimeShare */

const TimeShare = (function () {
  const { el, svg } = Dom;
  const { filePlace, repositoryPlace, arrow, pair, inline } = TimePlaces.parts;

  const PEOPLE = { you: { name: "You", owner: null }, alex: { name: "Alex", owner: "Alex" } };
  const GITHUB = "GitHub (the practice copy)";

  /* One caption per step, each saying what Alex can see. */
  const CAPTIONS = {
    create: "You made `notes.txt`. It is only in your working folder: Alex can't see it.",
    add: "`git add` put a copy of `notes.txt` in your open box, the staging area. Alex still can't see it.",
    commit: "`git commit` closed the box and set it on your timeline: a commit in your repository. Alex still can't see it: committing shares nothing, it saves on your computer only.",
    push: "`git push` carried the box to GitHub, and GitHub's `main` moved onto it. Alex still doesn't have it: it is on GitHub, not on Alex's computer.",
    "pull-fetch": "Alex runs `git pull`. First its fetch half: the box arrives in Alex's repository and Alex's `origin/main` moves onto it. Alex's working folder hasn't changed yet.",
    "pull-merge-half": "Then its merge half: Alex's `main` moves onto the box, and `notes.txt` appears in Alex's staging area and working folder. Now Alex's files have it too.",
    "alex-commit": "Alex adds a line to `notes.txt` and commits: a new box on Alex's timeline, in Alex's repository only. GitHub and your computer don't have it.",
    "alex-push": "Alex's `git push` carries the box to GitHub, and GitHub's `main` moves onto it. Alex has the new line; your computer still has the old `notes.txt`.",
    "you-commit": "You commit a change of your own, to `README.md`. Alex can't see it, and you don't have Alex's new line yet.",
    refused: "Your `git push` is refused: GitHub has Alex's commit, which your repository doesn't. Nothing moves, on your computer or on GitHub, and Alex still can't see your commit.",
    "pull-stops": "Your `git pull` fetches Alex's commit: the box arrives in your repository and your `origin/main` moves onto it. Then it stops: both sides have new commits, and since no setting (`pull.rebase` or `pull.ff`) says how to join them, git asks you to choose: `--no-rebase` merges, `--rebase` rebases. Your `main` and your files don't change, and Alex still can't see your commit.",
    "pull-merge": "`git pull --no-rebase` merges Alex's commit with yours (`--no-edit` takes git's own merge message instead of opening an editor): a merge commit joins the two timelines, and your `notes.txt` gets Alex's line. Alex can't see your commit yet.",
    "push-again": "Now `git push` works: GitHub gets your commit and the merge commit, and its `main` moves onto them. Alex will have them after the next `git pull`.",
  };

  /* The actor's arrows a step lights, from the actor's feed events and GitHub's. */
  const lit = (step) => TimePlaces.commands([...step.events[step.actor], ...step.events.github], step.before[step.actor], step.after[step.actor]);

  /* A person, drawn small in the theme's ink: a head and shoulders. */
  const figureOf = () => svg("svg", { class: "ts-person", viewBox: "0 0 32 32", width: 30, height: 30, "aria-hidden": "true", focusable: "false" },
    svg("circle", { cx: 16, cy: 10, r: 6 }),
    svg("path", { d: "M5,30 C5,21 10,18 16,18 C22,18 27,21 27,30 Z" }),
  );

  /* One person's computer: who, then the working folder, the open box and the repository, with
     the arrows between them and the pair across to GitHub. */
  function computer(who, snapshot, commands) {
    const { name, owner } = PEOPLE[who];
    const merge = TimePlaces.ARROWS.pull.path;
    return el("div", { class: `ts-computer is-${who}`, "data-person": who, role: "group", "aria-label": `${name === "You" ? "Your" : `${name}'s`} computer` },
      el("div", { class: "ts-who" }, figureOf(), el("span", { class: "ts-name" }, name)),
      filePlace("folder", snapshot.files),
      pair(1, arrow("add", commands, undefined, owner), arrow("pull", commands, merge.slice(1), owner)),
      filePlace("index", snapshot.files),
      pair(2, arrow("commit", commands, undefined, owner), arrow("pull", commands, merge.slice(0, 2), owner)),
      repositoryPlace("repository", snapshot, true),
      pair(3, arrow("push", commands, undefined, owner), arrow("fetch", commands, undefined, owner)),
    );
  }

  /* What the person who ran the step typed, and git's own words when it refused. */
  function said(step) {
    const refused = step.transcript.filter((line) => line.status !== 0);
    return [
      el("p", { class: "ts-command" }, el("span", { class: "ts-actor" }, `${PEOPLE[step.actor].name}:`), step.commands.map((command) => el("code", {}, `$ ${command}`))),
      refused.length > 0 && el("pre", { class: "ts-output" }, refused.map((line) => line.output).join("")),
    ];
  }

  /* The step's state `at` ("after" by default, lit and captioned; "before" plain). */
  function render(step, { at = "after" } = {}) {
    const state = step[at];
    const commands = at === "after" ? lit(step) : [];
    const lights = (who) => (who === step.actor ? commands : []);
    return el("figure", { class: "ts-share", "aria-label": "You, GitHub and Alex" },
      el("div", { class: "ts-grid" },
        computer("you", state.you, lights("you")),
        el("div", { class: "ts-github", role: "group", "aria-label": GITHUB }, el("div", { class: "ts-who" }, el("span", { class: "ts-name" }, GITHUB)), repositoryPlace("remote", state.github, false)),
        computer("alex", state.alex, lights("alex")),
      ),
      said(step),
      at === "after" && el("figcaption", { class: "ts-caption" }, inline(CAPTIONS[step.id])),
    );
  }

  /* Plays a step on the figure render(step) drew, inside the actor's computer and GitHub; returns
     the animations started. */
  function play(figure, step, reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const mine = [...figure.querySelectorAll("[data-person]")].find((node) => node.getAttribute("data-person") === step.actor);
    const github = figure.querySelector(".ts-github");
    const lookup = {
      place: (area) => (area === "remote" ? github : mine).querySelector(`[data-area="${area}"]`),
      arrows: (name) => [...mine.querySelectorAll(".tt-arrow")].filter((node) => node.getAttribute("data-command") === name),
    };
    const view = (state) => ({ project: state[step.actor], github: state.github });
    return TimePlaces.play(figure, { before: view(step.before), after: view(step.after), commands: lit(step) }, reduced, lookup);
  }

  return { CAPTIONS, lit, render, play };
})();
