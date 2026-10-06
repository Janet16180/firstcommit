"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, record } = require("./load");

const document = installBrowser();
const { TimeShare, TimePlaces } = load(["dom.js", "map.js", "theme-time.js", "theme-time-motion.js", "theme-time-places.js", "theme-time-share.js"], ["TimeShare", "TimePlaces"]);

const full = (name) => name.padEnd(40, "0");
const blob = (name) => name.padEnd(40, "b");

function file(path, { head = null, index = null, folder = null, indexChange = null, folderChange = null } = {}) {
  const mode = (id) => (id === null ? null : "100644");
  return {
    path, head: head && blob(head), index: index && blob(index), folder: folder && blob(folder),
    head_mode: mode(head), index_mode: mode(index), folder_mode: mode(folder),
    ignored: false, conflicted: false, repository: false, index_change: indexChange, folder_change: folderChange,
  };
}

function repo({ commits = [], refs = [], files = [], bare = false, head = commits.length ? commits[0][0] : null }) {
  return {
    ...record("snapshots").one,
    exists: true,
    bare,
    head: bare || head === null ? null : full(head),
    branch: "main",
    commits: commits.map(([name, parents], index) => ({
      hash: full(name), short: full(name).slice(0, 7), parents: parents.map(full), subject: `Commit ${name}`, author: "Robin Park", time: 1000 - index,
    })),
    refs: refs.map(([name, kind, target]) => ({ name, kind, target: full(target) })),
    files,
  };
}

const ONE = [["a", []]];
const TWO = [["b", ["a"]], ["a", []]];
const README = file("README.md", { head: "1", index: "1", folder: "1" });
const NOTES = file("notes.txt", { head: "2", index: "2", folder: "2" });
const clone = (commits, main, origin, files) => repo({ commits, refs: [["main", "branch", main], ["origin/main", "remote", origin]], head: main, files });
const hub = (commits) => repo({ commits, bare: true, refs: [["main", "branch", commits[0][0]]] });
const kinds = (...names) => names.map((kind) => ({ kind, text: [] }));
const none = { you: [], github: [], alex: [] };

const YOU_PUSHED = { you: clone(TWO, "b", "b", [README, NOTES]), github: hub(TWO), alex: clone(ONE, "a", "a", [README]) };
const ALEX_FETCHED = { ...YOU_PUSHED, alex: clone(TWO, "a", "b", [README]) };
const ALEX_PULLED = { ...YOU_PUSHED, alex: clone(TWO, "b", "b", [README, NOTES]) };
const THREE = [["c", ["b"]], ...TWO];
const ALEX_COMMITTED = { ...ALEX_PULLED, alex: clone(THREE, "c", "b", [README, file("notes.txt", { head: "3", index: "3", folder: "3" })]) };
const ALEX_PUSHED = { ...ALEX_COMMITTED, github: hub(THREE), alex: clone(THREE, "c", "c", ALEX_COMMITTED.alex.files) };
const DIVERGED = [["d", ["b"]], ...TWO];
const YOU_COMMITTED = { ...ALEX_PUSHED, you: clone(DIVERGED, "d", "b", [README, NOTES]) };
const YOU_STOPPED = { ...YOU_COMMITTED, you: clone([["d", ["b"]], ...THREE], "d", "c", [README, NOTES]) };
const STOPPED = "From /tmp/firstcommit-share/github/project\n   b000000..c000000  main       -> origin/main\nfatal: Need to specify how to reconcile divergent branches.\n";
const STEPS = {
  push: { id: "push", actor: "you", before: { ...YOU_PUSHED, you: clone(TWO, "b", "a", [README, NOTES]), github: hub(ONE) }, after: YOU_PUSHED, events: { ...none, you: kinds("remote-updated"), github: kinds("push-received") }, commands: ["git push"], transcript: [{ command: "git push", output: "", status: 0 }] },
  fetch: { id: "pull-fetch", actor: "alex", before: YOU_PUSHED, after: ALEX_FETCHED, events: { ...none, alex: kinds("remote-updated") }, commands: ["git pull"], transcript: [{ command: "git fetch", output: "", status: 0 }] },
  merge: { id: "pull-merge-half", actor: "alex", before: ALEX_FETCHED, after: ALEX_PULLED, events: { ...none, alex: kinds("branch-moved") }, commands: ["git pull"], transcript: [{ command: "git pull", output: "", status: 0 }] },
  alexCommit: { id: "alex-commit", actor: "alex", before: ALEX_PULLED, after: ALEX_COMMITTED, events: { ...none, alex: kinds("commit-created") }, commands: ["echo 'Bring the slides.' >> notes.txt", "git commit -am 'Ask for the slides'"], transcript: [] },
  alexPush: { id: "alex-push", actor: "alex", before: ALEX_COMMITTED, after: ALEX_PUSHED, events: { ...none, alex: kinds("remote-updated"), github: kinds("push-received") }, commands: ["git push"], transcript: [] },
  stops: { id: "pull-stops", actor: "you", before: YOU_COMMITTED, after: YOU_STOPPED, events: { ...none, you: kinds("remote-updated") }, commands: ["git pull"], transcript: [{ command: "git pull", output: STOPPED, status: 128 }] },
  refused: { id: "refused", actor: "you", before: YOU_PUSHED, after: YOU_PUSHED, events: none, commands: ["git push"], transcript: [{ command: "git push", output: " ! [rejected]        main -> main (fetch first)\n", status: 1 }] },
};

/* Draws a figure with `draw`, starts its motion with `start`, and records every animate() call. */
function animating(draw, start) {
  const calls = [];
  const figure = draw();
  document.body.replaceChildren(figure);
  const proto = Object.getPrototypeOf(figure);
  proto.animate = function (frames, timing) {
    const call = { node: this, frames, timing, onfinish: null };
    calls.push(call);
    return call;
  };
  proto.getTotalLength = () => 100;
  start(figure);
  delete proto.animate;
  delete proto.getTotalLength;
  return { figure, calls };
}

/* Renders a step's after state, plays the step, and records every animate() call. */
const played = (step, reduced = false) => animating(() => TimeShare.renderStep(step), (figure) => TimeShare.playStep(figure, step, reduced));

const person = (figure, who) => [...figure.querySelectorAll("[data-person]")].find((node) => node.getAttribute("data-person") === who);
const areas = (node) => [...node.querySelectorAll("[data-area]")].map((place) => place.getAttribute("data-area"));
const insideOf = (figure, who) => (call) => person(figure, who).contains(call.node);

test("the figure puts your computer, GitHub and Alex's computer side by side, each computer with its folder, open box and repository", () => {
  const figure = TimeShare.renderStep(STEPS.push);
  assert.deepEqual(areas(person(figure, "you")), ["folder", "index", "repository"]);
  assert.deepEqual(areas(person(figure, "alex")), ["folder", "index", "repository"]);
  assert.deepEqual(areas(figure.querySelector(".ts-github")), ["remote"]);
  assert.ok(person(figure, "alex").querySelector("svg.ts-person"), "Alex is drawn as a person");
  assert.match(person(figure, "alex").querySelector(".ts-name").textContent, /^Alex$/);
  assert.match(person(figure, "you").querySelector(".ts-name").textContent, /^You$/);
});

test("Alex's column is titled Alex's repository, and both repositories hold the commits, not only yours", () => {
  const figure = TimeShare.renderStep(STEPS.push);
  const titles = (who) => [...person(figure, who).querySelectorAll("h4")].map((node) => node.textContent);
  assert.deepEqual(titles("you"), ["Working folder", "Staging area", "Your repository"]);
  assert.deepEqual(titles("alex"), ["Working folder", "Staging area", "Alex's repository"]);
  const notes = [...figure.querySelectorAll('[data-area="repository"] .tt-place-note')].map((node) => node.textContent);
  assert.deepEqual(notes, ["closed boxes: the commits", "closed boxes: the commits"]);
});

test("every step's caption says what Alex can see", () => {
  const ids = ["create", "add", "commit", "push", "pull-fetch", "pull-merge-half", "alex-commit", "alex-push", "you-commit", "refused", "pull-stops", "pull-merge", "push-again"];
  assert.deepEqual(Object.keys(TimeShare.CAPTIONS), ids);
  for (const id of ids) assert.match(TimeShare.CAPTIONS[id], /Alex/, id);
});

test("the commit's caption says plainly that committing shares nothing", () => {
  assert.match(TimeShare.CAPTIONS.commit, /shares nothing/);
});

test("the merge half's caption says Alex's files have it now, since the fetch half already brought the commit", () => {
  assert.match(TimeShare.CAPTIONS["pull-merge-half"], /Now Alex's files have it too\.$/);
});

test("your merge's caption names the command that merged, and the step before says a plain git pull stops", () => {
  assert.match(TimeShare.CAPTIONS["pull-stops"], /^Your `git pull` fetches Alex's commit/);
  assert.match(TimeShare.CAPTIONS["pull-stops"], /Then it stops/);
  assert.match(TimeShare.CAPTIONS["pull-merge"], /^`git pull --no-rebase` merges/);
  assert.match(TimeShare.CAPTIONS["pull-merge"], /`--no-edit` takes git's own merge message instead of opening an editor/);
});

test("Alex's commit and Alex's push are two steps, each lighting its own arrow", () => {
  assert.deepEqual(TimeShare.lit(STEPS.alexCommit), ["commit"]);
  assert.deepEqual(TimeShare.lit(STEPS.alexPush), ["push"]);
});

test("a plain git pull that stops shows git's own words, and lights only its fetch half", () => {
  const { figure, calls } = played(STEPS.stops);
  assert.deepEqual(TimeShare.lit(STEPS.stops), ["fetch"]);
  assert.match(figure.querySelector(".ts-output").textContent, /Need to specify how to reconcile divergent branches/);
  assert.match(figure.querySelector(".ts-command").textContent, /^You:\$ git pull$/);
  const yours = (area) => person(figure, "you").querySelector(`[data-area="${area}"]`);
  assert.deepEqual(calls.filter((call) => yours("folder").contains(call.node) || yours("index").contains(call.node)), []);
  assert.equal(figure.querySelectorAll(".tt-flyer.is-commit").length, 1);
});

test("a step lights the arrows of the person who ran it, from their own events and GitHub's", () => {
  assert.deepEqual(TimeShare.lit(STEPS.push), ["push"]);
  assert.deepEqual(TimeShare.lit(STEPS.fetch), ["fetch"]);
  assert.deepEqual(TimeShare.lit(STEPS.merge), ["pull"]);
  assert.deepEqual(TimeShare.lit(STEPS.refused), []);
});

test("only the arrows of the person who ran the step light up, with the step's caption under the figure", () => {
  const figure = TimeShare.renderStep(STEPS.fetch);
  const active = (who) => [...person(figure, who).querySelectorAll(".tt-arrow.is-active")].map((arrow) => arrow.getAttribute("data-command"));
  assert.deepEqual(active("alex"), ["fetch"]);
  assert.deepEqual(active("you"), []);
  assert.equal(figure.querySelector(".ts-caption").textContent, TimeShare.CAPTIONS["pull-fetch"].replaceAll("`", ""));
  assert.match(figure.querySelector(".ts-command").textContent, /Alex.*\$ git pull/);
});

test("each arrow says aloud whose places it joins", () => {
  const figure = TimeShare.renderStep(STEPS.push);
  const said = (who, name) => [...person(figure, who).querySelectorAll(".tt-arrow")].find((arrow) => arrow.getAttribute("data-command") === name && arrow.getAttribute("aria-label")).getAttribute("aria-label");
  assert.equal(said("you", "push"), "push: from your repository to the remote repository");
  assert.equal(said("alex", "fetch"), "fetch: from the remote repository to Alex's repository");
  assert.equal(said("alex", "add"), "add: from Alex's working folder to Alex's staging area");
});

test("your push flies your box to GitHub, and nothing on Alex's computer moves", () => {
  const { figure, calls } = played(STEPS.push);
  assert.equal(figure.querySelectorAll(".tt-flyer.is-commit").length, 1);
  assert.ok(calls.some((call) => figure.querySelector(".ts-github").contains(call.node)), "GitHub's branch moves");
  assert.deepEqual(calls.filter(insideOf(figure, "alex")), []);
});

test("the fetch half of Alex's pull brings the box into Alex's repository and leaves Alex's folder as it was", () => {
  const { figure, calls } = played(STEPS.fetch);
  assert.equal(figure.querySelectorAll(".tt-flyer.is-commit").length, 1);
  const alexFolder = person(figure, "alex").querySelector('[data-area="folder"]');
  assert.deepEqual(calls.filter((call) => alexFolder.contains(call.node)), []);
  assert.ok(calls.some((call) => person(figure, "alex").querySelector('[data-area="repository"]').contains(call.node)), "Alex's origin/main moves");
  assert.deepEqual(calls.filter(insideOf(figure, "you")), []);
});

test("the merge half brings the page through Alex's open box into Alex's folder", () => {
  const { figure, calls } = played(STEPS.merge);
  const flyer = figure.querySelector(".tt-flyer.is-file");
  assert.match(flyer.textContent, /notes\.txt/);
  const page = [...person(figure, "alex").querySelector('[data-area="folder"]').querySelectorAll("[data-path]")].find((node) => node.getAttribute("data-path") === "notes.txt");
  assert.ok(calls.some((call) => call.node === page && call.frames[0].opacity === 0), "the page appears in Alex's folder as it arrives");
});

test("a refused push shows git's own words, and nothing moves anywhere", () => {
  const { figure, calls } = played(STEPS.refused);
  assert.match(figure.querySelector(".ts-output").textContent, /\[rejected\]/);
  assert.deepEqual(calls, []);
  assert.equal(figure.querySelector(".tt-flyer"), null);
});

test("the figure's motions take their pace from the four places' shared timing, and follow it when it changes", () => {
  const { flight, arrow } = TimePlaces.TIMING;
  const was = { ...flight, arrow };
  try {
    Object.assign(flight, { delay: 1001, duration: 1002 });
    TimePlaces.TIMING.arrow = 1003;
    const { figure, calls } = played(STEPS.push);
    const flyer = calls.find((call) => call.node === figure.querySelector(".tt-flyer"));
    assert.deepEqual([flyer.timing.delay, flyer.timing.duration], [1001, 1002]);
    const shaft = calls.find((call) => call.node.getAttribute("class") === "tt-arrow-shaft");
    assert.equal(shaft.timing.duration, 1003);
  } finally {
    Object.assign(flight, { delay: was.delay, duration: was.duration });
    TimePlaces.TIMING.arrow = was.arrow;
  }
});

test("under reduced motion nothing moves, and the caption still says what happened", () => {
  const { figure, calls } = played(STEPS.push, true);
  assert.deepEqual(calls, []);
  assert.ok(figure.querySelector(".ts-caption").textContent.length > 0);
});

/* The playground: the game's real record of Alex pressing "git push", and the observation just
   before it, when GitHub and Alex's origin/main were still on the pushed commit's parent. */
const PRESS = record("press");
function beforePush(observation) {
  const before = structuredClone(observation);
  const [pushed, ...older] = before.github.commits;
  const parent = pushed.parents[0];
  before.github = { ...before.github, head: parent, commits: older, refs: before.github.refs.map((ref) => ({ ...ref, target: parent })) };
  before.teammate.refs = before.teammate.refs.map((ref) => (ref.kind === "remote" ? { ...ref, target: parent } : ref));
  return { ...before, events: [], teammate_events: [] };
}
const AFTER = PRESS.observation;
const BEFORE = beforePush(AFTER);
const hashes = (snapshot) => snapshot.commits.map((commit) => commit.hash);

test("the live figure draws you, GitHub and Alex from the game's observation, with no caption and no step", () => {
  const state = TimeShare.observed(AFTER);
  assert.deepEqual([state.you, state.github, state.alex], [AFTER.project, AFTER.github, AFTER.teammate]);
  const figure = TimeShare.render(state);
  assert.deepEqual(areas(person(figure, "you")), ["folder", "index", "repository"]);
  assert.deepEqual(areas(person(figure, "alex")), ["folder", "index", "repository"]);
  assert.deepEqual(areas(figure.querySelector(".ts-github")), ["remote"]);
  assert.equal(person(figure, "alex").querySelectorAll("h4")[2].textContent, "Alex's repository");
  assert.equal(figure.querySelector(".ts-caption"), null);
  assert.equal(figure.querySelector(".ts-command"), null);
  assert.equal(figure.querySelectorAll(".tt-arrow.is-active").length, 0);
});

test("a press lights the arrows of the person who pressed, from their events and GitHub's", () => {
  assert.equal(PRESS.press.person, "alex");
  const commands = TimeShare.pressed(BEFORE, AFTER, "alex");
  assert.deepEqual(commands, ["push"]);
  const figure = TimeShare.render(TimeShare.observed(AFTER), { person: "alex", commands });
  const active = (who) => [...person(figure, who).querySelectorAll(".tt-arrow.is-active")].map((arrow) => arrow.getAttribute("data-command"));
  assert.deepEqual(active("alex"), ["push"]);
  assert.deepEqual(active("you"), []);
});

test("Alex's pressed push flies Alex's box to GitHub, and nothing on your computer moves", () => {
  const [before, after] = [TimeShare.observed(BEFORE), TimeShare.observed(AFTER)];
  const commands = TimeShare.pressed(BEFORE, AFTER, "alex");
  const { figure, calls } = animating(() => TimeShare.render(after, { person: "alex", commands }), (drawn) => TimeShare.play(drawn, before, after, "alex", commands, false));
  const flyers = [...figure.querySelectorAll(".tt-flyer.is-commit")];
  assert.equal(flyers.length, 1);
  assert.match(flyers[0].textContent, new RegExp(hashes(AFTER.github)[0].slice(0, 7)));
  assert.ok(calls.some((call) => figure.querySelector(".ts-github").contains(call.node)), "GitHub's main moves");
  assert.deepEqual(calls.filter(insideOf(figure, "you")), []);
});

test("a press git refused moves nothing, since nothing changed", () => {
  const still = TimeShare.observed(AFTER);
  const { calls } = animating(() => TimeShare.render(still, { person: "you", commands: [] }), (drawn) => TimeShare.play(drawn, still, still, "you", [], false));
  assert.deepEqual(calls, []);
});

test("each person's computer has an empty slot under it for that person's buttons, and GitHub has none", () => {
  const figure = TimeShare.render(TimeShare.observed(AFTER));
  for (const who of ["you", "alex"]) {
    const slots = [...person(figure, who).querySelectorAll("[data-slot]")];
    assert.deepEqual(slots.map((slot) => slot.getAttribute("data-slot")), [who]);
    assert.equal(slots[0].children.length, 0);
  }
  assert.equal(figure.querySelector(".ts-github [data-slot]"), null);
});

test("the person switch only chooses whose slot a narrow screen shows", () => {
  const figure = TimeShare.render(TimeShare.observed(AFTER), { shown: "you" });
  const drawn = figure.querySelector(".ts-grid");
  const choice = (who) => [...figure.querySelectorAll(".ts-switch button")].find((button) => button.getAttribute("data-show") === who);
  assert.equal(figure.getAttribute("data-shown"), "you");
  assert.deepEqual(["you", "alex"].map((who) => choice(who).getAttribute("aria-pressed")), ["true", "false"]);
  choice("alex").click();
  assert.equal(figure.getAttribute("data-shown"), "alex");
  assert.deepEqual(["you", "alex"].map((who) => choice(who).getAttribute("aria-pressed")), ["false", "true"]);
  assert.equal(figure.querySelector(".ts-grid"), drawn, "the figure is not drawn again");
  assert.equal(TimeShare.render(TimeShare.observed(AFTER), { shown: "alex" }).getAttribute("data-shown"), "alex");
});

test("a timeline drawn smaller to fit its place keeps at least four fifths of its size, in the walkthrough and the playground", () => {
  for (const figure of [TimeShare.render(TimeShare.observed(AFTER)), TimeShare.renderStep(STEPS.push)]) {
    const graphs = [...figure.querySelectorAll("svg.map-graph")];
    assert.equal(graphs.length, 3);
    for (const graph of graphs) assert.equal(graph.style.minWidth, `${Math.round(0.8 * Number(graph.getAttribute("width")))}px`);
  }
});
