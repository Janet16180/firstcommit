"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { createClock, installBrowser, load, record } = require("./load");

const document = installBrowser();
const { ZonePanel } = load(["dom.js", "strings.js", "places.js", "art-pixels.js", "art-sprites.js", "typed.js", "zones.js", "zone-panel.js"], ["ZonePanel"]);

const observe = (project, github = null) => ({ ...record("observation"), project, github });
/* A repository that names the mothership `origin`, as a clone does. */
const named = (project) => ({ ...project, remotes: [{ name: "origin", url: "../github/project.git" }] });
/* The sample crew level: your clone, the stand-in GitHub and Alex's clone. */
const crewObservation = () => {
  const observation = record("press").observation;
  return { ...observation, project: named(observation.project) };
};
const zone = (panel, name) => panel.element.querySelector(`.zone[data-zone="${name}"]`);
/* The item with a fly-by key, found without a selector (a file name may hold any character). */
const keyed = (node, key) => [...node.querySelectorAll("[data-key]")].find((item) => item.dataset.key === key);
const texts = (node, selector) => [...node.querySelectorAll(selector)].map((item) => item.textContent);

test("the four zones are named in the design's order, the real git name first and the game's in brackets", () => {
  const panel = ZonePanel.create();
  assert.deepEqual(texts(panel.element, ".z-head h3"), ["Working folder (workshop)", "Staging area (cargo dock)", "Repository (vault)", "Remote (mothership)"]);
  assert.deepEqual(texts(panel.element, ".z-head small"), []);
  assert.equal(panel.element.getAttribute("aria-label"), "Your repository");
});

test("drawn arrows between the zones name the commands that move work along", () => {
  const panel = ZonePanel.create();
  assert.deepEqual(texts(panel.element, ".fl span"), ["git add", "git commit", "git push", "git pull"]);
  assert.deepEqual([...panel.element.querySelectorAll(".fl")].map((arrow) => arrow.dataset.arrow), ["add", "commit", "push", "pull"]);
  assert.equal(panel.element.querySelectorAll(".fl svg.art-icon").length, 4);
  assert.ok(panel.element.querySelector(".fl.is-back"));
});

test("a folder without a repository lights only the workshop, and the other zones say why they are off", () => {
  const panel = ZonePanel.create();
  panel.update(observe(record("snapshots").folder));
  assert.equal(zone(panel, "workshop").classList.contains("is-dormant"), false);
  for (const name of ["dock", "vault", "remote"]) assert.ok(zone(panel, name).classList.contains("is-dormant"), name);
  assert.match(zone(panel, "dock").textContent, /git init/);
  assert.deepEqual(texts(zone(panel, "workshop"), ".fname"), ["notes.txt"]);
  assert.equal(zone(panel, "workshop").querySelector(".file").dataset.state, "none");
  assert.equal(zone(panel, "workshop").querySelector(".z-count").textContent, "1");
  assert.equal(zone(panel, "dock").querySelector(".z-count").textContent, "–");
});

test("files show their state with a tag, and staged changes sit on the dock", () => {
  const panel = ZonePanel.create();
  panel.update(observe({ ...record("snapshots").one, files: record("files") }));
  const workshop = zone(panel, "workshop");
  const newFile = [...workshop.querySelectorAll(".file")].find((item) => item.textContent.startsWith("new.txt"));
  assert.equal(newFile.dataset.state, "new");
  assert.equal(newFile.querySelector(".ftag").textContent, "new");
  assert.deepEqual(texts(zone(panel, "dock"), ".fname"), ["added.txt", "staged.txt", "removed.txt", "staged-link"]);
  assert.equal(zone(panel, "dock").querySelector(".z-count").textContent, "4");
});

test("the vault lists HEAD's history as capsules with their labels and messages", () => {
  const panel = ZonePanel.create();
  panel.update(observe(record("observation").project));
  const vault = zone(panel, "vault");
  assert.equal(vault.querySelectorAll(".cap").length, Number(vault.querySelector(".z-count").textContent));
  assert.equal(vault.querySelector(".cap .chash").textContent, "547cd2b");
  assert.equal(vault.querySelector(".cap .ref").textContent, "HEAD → feature");
  assert.equal(vault.querySelector(".cap .cmsg").textContent, "Add a greeting to the readme");
});

test("empty zones say what fills them", () => {
  const panel = ZonePanel.create();
  panel.update(observe(named(record("snapshots").one), record("snapshots").unborn));
  assert.match(zone(panel, "dock").querySelector(".zone-empty").textContent, /git add/);
  assert.match(zone(panel, "remote").querySelector(".zone-empty").textContent, /git push/);
  assert.equal(zone(panel, "remote").classList.contains("is-dormant"), false);
});

test("the legend names every state a file can show", () => {
  const panel = ZonePanel.create();
  assert.deepEqual(texts(panel.element, ".legend li"), ["no repository", "conflict (both sides changed it)", "new (untracked)", "edited (modified)", "on the dock (staged)", "saved (committed)"]);
});

test("an observation that changed nothing leaves the zones' nodes in place", () => {
  const panel = ZonePanel.create();
  panel.update(observe(record("observation").project));
  const first = zone(panel, "vault").querySelector(".cap");
  panel.update(observe(record("observation").project));
  assert.equal(zone(panel, "vault").querySelector(".cap"), first);
});

const typed = (...lines) => lines.map((line) => ({ line, status: 0 }));

test("typing git init wakes the dock and the vault for a moment", async () => {
  const clock = createClock();
  const panel = ZonePanel.create({ timers: clock });
  panel.update(observe(record("snapshots").folder));
  panel.update({ ...observe(record("snapshots").unborn), commands: typed("git init") });
  assert.ok(zone(panel, "dock").classList.contains("is-waking"));
  assert.ok(zone(panel, "vault").classList.contains("is-waking"));
  await clock.advance(1600);
  assert.equal(zone(panel, "dock").classList.contains("is-waking"), false);
});

test("staging a file with git add lights the add arrow, and every item carries the key it flies by", () => {
  const clock = createClock();
  const panel = ZonePanel.create({ timers: clock });
  const project = record("snapshots").one;
  panel.update(observe(project));
  const file = { ...project.files[0], index: "new-version", index_change: "modified" };
  panel.update({ ...observe({ ...project, files: [file] }), commands: typed("git add hello.txt") });
  assert.ok(panel.element.querySelector('.fl[data-arrow="add"]').classList.contains("is-lit"));
  assert.ok(keyed(zone(panel, "dock"), "dock:hello.txt"));
  assert.ok(keyed(zone(panel, "workshop"), "workshop:hello.txt"));
  assert.ok(keyed(zone(panel, "vault"), `vault:${project.head}`));
});

test("the first drawing animates nothing", () => {
  const panel = ZonePanel.create({ timers: createClock() });
  panel.update({ ...observe(record("snapshots").unborn), commands: typed("git init") });
  assert.equal(panel.element.querySelector(".is-lit, .is-waking"), null);
});

const capsuleCommit = (hash, parents = []) => ({ hash, short: hash, parents, subject: `commit ${hash}`, author: "You", time: 0 });

test("the vault draws two branches as two lanes, with the merge capsule marked and a line to each parent", () => {
  const project = {
    ...record("snapshots").one,
    head: "m",
    branch: "main",
    commits: [capsuleCommit("m", ["a2", "b1"]), capsuleCommit("b1", ["a1"]), capsuleCommit("a2", ["a1"]), capsuleCommit("a1")],
    refs: [{ name: "main", kind: "branch", target: "m" }, { name: "feature", kind: "branch", target: "b1" }],
  };
  const panel = ZonePanel.create();
  panel.update(observe(project));
  const vault = zone(panel, "vault");
  const merge = keyed(vault, "vault:m");
  assert.ok(merge.classList.contains("is-merge"));
  assert.equal(keyed(vault, "vault:b1").querySelector(".cblock").getAttribute("style"), "margin-left:16px");
  assert.equal(keyed(vault, "vault:a2").querySelector(".cblock").getAttribute("style"), "margin-left:0px");
  assert.equal(vault.querySelectorAll("svg.links path").length, 4);
  assert.deepEqual([...keyed(vault, "vault:b1").querySelectorAll(".ref")].map((ref) => ref.textContent), ["feature"]);
});

test("a single branch keeps one lane: every capsule in the first column, one line between each", () => {
  const panel = ZonePanel.create();
  const project = { ...record("snapshots").one, head: "c2", branch: "main", commits: [capsuleCommit("c2", ["c1"]), capsuleCommit("c1")], refs: [{ name: "main", kind: "branch", target: "c2" }] };
  panel.update(observe(project));
  const vault = zone(panel, "vault");
  assert.deepEqual([...vault.querySelectorAll(".cblock")].map((block) => block.getAttribute("style")), ["margin-left:0px", "margin-left:0px"]);
  assert.equal(vault.querySelectorAll("svg.links path").length, 1);
  assert.equal(vault.querySelector("svg.links").getAttribute("width"), "16");
});

test("the mothership draws what the stand-in GitHub holds, every branch included", () => {
  const github = { ...record("snapshots").one, bare: true, head: "g2", branch: "main", commits: [capsuleCommit("g2", ["g1"]), capsuleCommit("t1", ["g1"]), capsuleCommit("g1")], refs: [{ name: "main", kind: "branch", target: "g2" }, { name: "topic", kind: "branch", target: "t1" }] };
  const panel = ZonePanel.create();
  panel.update(observe(named(record("snapshots").one), github));
  assert.equal(zone(panel, "remote").querySelectorAll(".cap").length, 3);
  assert.ok(keyed(zone(panel, "remote"), "remote:t1"));
});

test("labels carry the key they slide by: HEAD for the head, else the branch's name", () => {
  const panel = ZonePanel.create();
  panel.update(observe(record("observation").project));
  const keys = [...zone(panel, "vault").querySelectorAll(".ref")].map((ref) => ref.dataset.key);
  assert.ok(keys.includes("vault-ref:HEAD"));
  assert.ok(keys.includes("vault-ref:main"));
  assert.ok(keys.includes("vault-ref:origin/main"));
});

test("a refused push still asks for the bounce though nothing changed, and leaves the zones' nodes in place", () => {
  const thrown = [];
  const panel = ZonePanel.create({ reducedMotion: false, timers: createClock() });
  const project = record("observation").project;
  const github = record("snapshots").one;
  panel.update(observe(project, github));
  const first = zone(panel, "vault").querySelector(".cap");
  first.animate = (frames) => thrown.push(frames);
  panel.update({ ...observe(project, github), commands: [{ line: "git push", status: 1 }] });
  assert.equal(zone(panel, "vault").querySelector(".cap"), first);
  assert.equal(thrown.length, 1);
});

test("a conflicted file shows the crack mark and its tag, and a paused merge is said over the vault", () => {
  const project = { ...record("snapshots").one, operation: "merge", files: [{ ...record("snapshots").one.files[0], conflicted: true, index_change: "modified" }] };
  const panel = ZonePanel.create();
  panel.update(observe(project));
  const chip = zone(panel, "workshop").querySelector(".file");
  assert.equal(chip.dataset.state, "conflicted");
  assert.ok(chip.querySelector("svg.art-icon--conflict"));
  assert.equal(chip.querySelector(".ftag").textContent, "conflict");
  const paused = zone(panel, "vault").querySelector(".z-op");
  assert.equal(paused.hidden, false);
  assert.equal(paused.textContent, "merge paused");
  assert.ok(paused.querySelector("svg.art-icon--merging"));
});

test("with no operation in progress nothing is said over the vault", () => {
  const panel = ZonePanel.create();
  panel.update(observe(record("snapshots").one));
  assert.equal(zone(panel, "vault").querySelector(".z-op").hidden, true);
});

test("a revert capsule's block is the capsule upside down, and a fresh one rises in", () => {
  const clock = createClock();
  const panel = ZonePanel.create({ reducedMotion: false, timers: clock });
  const one = record("snapshots").one;
  panel.update(observe(one));
  const revert = { ...capsuleCommit("r1", [one.head]), subject: 'Revert "First commit"' };
  panel.update({ ...observe({ ...one, head: "r1", commits: [revert, ...one.commits] }), commands: [{ line: "git revert HEAD", status: 0 }] });
  const row = keyed(zone(panel, "vault"), "vault:r1");
  assert.ok(row.querySelector(".cblock.is-revert svg.art-icon--inverted"));
  assert.ok(row.classList.contains("art-rise-inverted"));
});

test("a file that just became conflicted cracks", () => {
  const clock = createClock();
  const panel = ZonePanel.create({ reducedMotion: false, timers: clock });
  const one = record("snapshots").one;
  panel.update(observe(one));
  panel.update({ ...observe({ ...one, operation: "merge", files: [{ ...one.files[0], conflicted: true, index_change: "modified" }] }), commands: [{ line: "git merge topic", status: 1 }] });
  assert.ok(keyed(zone(panel, "workshop"), `workshop:${one.files[0].path}`).classList.contains("art-crack"));
});

test("with a teammate the zones show two stations, yours and Alex's, with the mothership between and above them", () => {
  const panel = ZonePanel.create();
  const observation = crewObservation();
  panel.update(observation);
  assert.ok(panel.element.classList.contains("is-crew"));
  const stations = [...panel.element.querySelectorAll(".station")];
  assert.deepEqual(stations.map((node) => node.dataset.station), ["you", "alex"]);
  assert.deepEqual(stations.map((node) => node.querySelector(".art-station-name").textContent), ["Your base", "Alex's base"]);
  assert.deepEqual([...stations[0].querySelectorAll(".zone")].map((node) => node.dataset.zone), ["workshop", "dock", "vault"]);
  assert.deepEqual([...stations[1].querySelectorAll(".zone")].map((node) => node.dataset.zone), ["crew-vault", "crew-dock", "crew-workshop"]);
  assert.ok(panel.element.querySelector(".crew-sky .zone[data-zone=remote]"));
  assert.ok(keyed(zone(panel, "crew-vault"), `crew-vault:${observation.teammate.commits[0].hash}`));
  assert.ok(panel.element.querySelector('.fl[data-arrow="crew-push"]'));
});

test("a level without a teammate keeps the four zones in one row, with no stations", () => {
  const panel = ZonePanel.create();
  panel.update(record("observation"));
  assert.equal(panel.element.classList.contains("is-crew"), false);
  assert.equal(panel.element.querySelector(".station"), null);
  assert.equal(panel.element.querySelectorAll(".viz-row .zone").length, 4);
});

test("a teammate's push lights their own push arrow", () => {
  const clock = createClock();
  const panel = ZonePanel.create({ timers: clock });
  const after = crewObservation();
  const pushed = after.github.commits[0].hash;
  const older = after.github.commits[1].hash;
  const before = { ...after, github: { ...after.github, head: older, commits: after.github.commits.slice(1), refs: after.github.refs.map((ref) => ({ ...ref, target: older })) } };
  panel.update(before);
  panel.update(after);
  assert.ok(panel.element.querySelector('.fl[data-arrow="crew-push"]').classList.contains("is-lit"));
  assert.ok(keyed(zone(panel, "remote"), `remote:${pushed}`));
});

test("in the crew view capsule rows are taller, so a capsule's labels fit under its hash, and the lines follow them", () => {
  const crew = ZonePanel.create();
  crew.update(crewObservation());
  const caps = zone(crew, "crew-vault").querySelector(".caps");
  assert.match(caps.getAttribute("style"), /--row:72px/);
  assert.equal(caps.querySelector("svg.links").getAttribute("height"), "144");
  const solo = ZonePanel.create();
  solo.update(record("observation"));
  assert.match(zone(solo, "vault").querySelector(".caps").getAttribute("style"), /--row:40px/);
});

test("a capsule with many labels shows the first two and folds the rest into a count that names them", () => {
  const project = record("snapshots").one;
  const extra = ["survey", "origin/main", "origin/survey"].map((name) => ({ name, kind: name.startsWith("origin/") ? "remote" : "branch", target: project.head }));
  const panel = ZonePanel.create();
  panel.update(observe({ ...project, refs: [...project.refs, ...extra] }));
  const head = keyed(zone(panel, "vault"), `vault:${project.head}`);
  assert.equal([...head.querySelectorAll(".ref")].filter((node) => !node.classList.contains("ref-more")).length, 2);
  const more = head.querySelector(".ref-more");
  assert.equal(more.textContent, "+2");
  assert.equal(more.getAttribute("title").split(", ").length, 2);
});

test("each station wears the artist's frame and its name tab with the station's icon", () => {
  const panel = ZonePanel.create();
  panel.update(crewObservation());
  for (const who of ["you", "alex"]) {
    const station = panel.element.querySelector(`.station[data-station="${who}"]`);
    assert.ok(station.classList.contains("art-station") && station.classList.contains(`art-station--${who}`), who);
    assert.ok(station.querySelector(".art-station-name svg.art-icon"), who);
  }
});

test("a capsule flying up to the mothership, or down from it, in the crew view trails a flame", () => {
  const proto = Object.getPrototypeOf(document.createElement("div"));
  const sized = proto.getBoundingClientRect;
  proto.getBoundingClientRect = () => ({ x: 0, y: 0, top: 0, left: 0, width: 10, height: 10, right: 10, bottom: 10 });
  proto.animate = () => ({ finished: new Promise(() => {}) });
  /* A shallow copy is enough here: the test looks only at the flying copy's classes. */
  proto.cloneNode = function () {
    const copy = document.createElement(this.tagName.toLowerCase());
    copy.setAttribute("class", this.getAttribute("class") || "");
    return copy;
  };
  try {
    const panel = ZonePanel.create({ reducedMotion: false, timers: createClock() });
    const after = crewObservation();
    const older = after.github.commits[1].hash;
    panel.update({ ...after, github: { ...after.github, head: older, commits: after.github.commits.slice(1), refs: after.github.refs.map((ref) => ({ ...ref, target: older })) } });
    panel.update(after);
    const capsules = [...document.body.querySelectorAll(".ghost")].filter((ghost) => ghost.classList.contains("cap"));
    assert.ok(capsules.length > 0);
    assert.ok(capsules.every((ghost) => ghost.classList.contains("art-crew-flight")));
  } finally {
    proto.getBoundingClientRect = sized;
    delete proto.animate;
    delete proto.cloneNode;
    for (const ghost of document.body.querySelectorAll(".ghost")) ghost.remove();
  }
});

test("Alex's station is a smaller mirror of yours: its vault faces the mothership, its arrows point back", () => {
  const panel = ZonePanel.create();
  panel.update(crewObservation());
  const alex = panel.element.querySelector('.station[data-station="alex"]');
  assert.ok(alex.classList.contains("is-mirror"));
  assert.equal(panel.element.querySelector('.station[data-station="you"]').classList.contains("is-mirror"), false);
  assert.ok([...alex.querySelectorAll(".flow")].every((node) => node.classList.contains("is-mirror")));
});

test("a mothership the repository has not named yet says how to name it, and where it lives", () => {
  const panel = ZonePanel.create();
  const project = { ...record("snapshots").one, remotes: [] };
  panel.update(observe(project, { ...record("snapshots").empty, exists: true, bare: true }));
  const remote = zone(panel, "remote");
  assert.ok(remote.classList.contains("is-dormant"));
  assert.match(remote.textContent, /Not named yet: git remote add\./);
  assert.match(remote.textContent, /At work, the same address looks like/);
  panel.update(observe({ ...project, remotes: [{ name: "origin", url: "../github/project.git" }] }, { ...record("snapshots").empty, exists: true, bare: true }));
  assert.equal(zone(panel, "remote").classList.contains("is-dormant"), false);
  assert.doesNotMatch(zone(panel, "remote").textContent, /Not named yet/);
});

test("ignored files stay in the workshop, greyed, one chip per folder that says they are still on your disk; the badge counts what git sees", () => {
  const panel = ZonePanel.create();
  const one = record("snapshots").one;
  const ignored = [1, 2, 3].map((run) => ({ ...one.files[0], path: `sim-output/run-00${run}.log`, head: null, index: null, ignored: true, index_change: null, folder_change: "ignored" }));
  panel.update(observe({ ...one, files: [...one.files, ...ignored] }));
  const workshop = zone(panel, "workshop");
  const chip = workshop.querySelector(".file.is-ignored");
  assert.ok(chip.classList.contains("art-ignore-field"));
  assert.equal(chip.querySelector(".fname").textContent, "sim-output/");
  assert.equal(chip.querySelector(".ftag").textContent, "3 ignored, still on your disk");
  assert.equal(workshop.querySelector(".z-count").textContent, String(one.files.length));
});

test("a workshop holding only ignored files says it is empty, and still shows them", () => {
  const panel = ZonePanel.create();
  const one = record("snapshots").one;
  const ignored = { ...one.files[0], path: "build.log", head: null, index: null, ignored: true, index_change: null, folder_change: "ignored" };
  panel.update(observe({ ...one, files: [ignored] }));
  const workshop = zone(panel, "workshop");
  assert.ok(workshop.querySelector(".zone-empty"));
  assert.equal(workshop.querySelector(".file.is-ignored .fname").textContent, "build.log");
  assert.equal(workshop.querySelector(".file.is-ignored .ftag").textContent, "ignored, still on your disk");
  assert.equal(workshop.querySelector(".z-count").textContent, "0");
});

test("the places Git keeps, the dock, the vault and the mothership, are grouped and named as the black box; the workshop stays outside", () => {
  const panel = ZonePanel.create();
  const kept = panel.element.querySelector(".viz-row .viz-kept");
  assert.ok(kept.classList.contains("art-blackbox"));
  assert.deepEqual([...kept.querySelectorAll(".zone")].map((node) => node.dataset.zone), ["dock", "vault", "remote"]);
  assert.equal(kept.querySelector(".viz-kept-name").textContent, "Black box: what Git keeps");
  assert.equal(zone(panel, "workshop").closest(".viz-kept"), null);
  assert.deepEqual(texts(panel.element, ".z-head h3"), ["Working folder (workshop)", "Staging area (cargo dock)", "Repository (vault)", "Remote (mothership)"]);
});

test("with a teammate, the panel can keep to your row of four, the black box group in it, and give the stations back", () => {
  const panel = ZonePanel.create();
  panel.update(crewObservation());
  panel.mode("row");
  assert.equal(panel.element.querySelector(".station"), null);
  assert.ok(!panel.element.classList.contains("is-crew"));
  assert.deepEqual([...panel.element.querySelectorAll(".viz-kept .zone")].map((node) => node.dataset.zone), ["dock", "vault", "remote"]);
  assert.ok(zone(panel, "vault").querySelector(".cap"));
  panel.update(crewObservation());
  assert.equal(panel.element.querySelector(".station"), null);
  panel.mode("zones");
  assert.deepEqual([...panel.element.querySelectorAll(".station")].map((node) => node.dataset.station), ["you", "alex"]);
});

test("keeping to your row, the panel lets Alex's push go by without the arrows it does not show", () => {
  const panel = ZonePanel.create({ reducedMotion: true, timers: createClock() });
  const before = crewObservation();
  panel.update(before);
  panel.mode("row");
  const tip = before.teammate.commits[0];
  const pushed = { ...tip, hash: "f".repeat(40), short: "fffffff", parents: [tip.hash], subject: "Alex's fix" };
  const after = structuredClone(before);
  after.teammate.commits = [pushed, ...after.teammate.commits];
  after.teammate.refs = after.teammate.refs.map((ref) => (ref.target === tip.hash ? { ...ref, target: pushed.hash } : ref));
  after.github.commits = [pushed, ...after.github.commits];
  after.github.refs = after.github.refs.map((ref) => (ref.target === tip.hash ? { ...ref, target: pushed.hash } : ref));
  panel.update(after);
  assert.ok(keyed(zone(panel, "remote"), `remote:${pushed.hash}`));
});

/* The sample crew level's vault holds its first commit; the mothership holds it and Alex's next one. */
const rowsOf = (panel, name) => [...zone(panel, name).querySelector(".caps").children].filter((row) => !row.classList.contains("links")).map((row) => (row.classList.contains("cap-gap") ? "gap" : row.dataset.key.split(":")[1].slice(0, 7)));

test("history's chart keeps to your row and lines up the vault and the mothership by commit, a gap where a side lacks one", () => {
  const panel = ZonePanel.create();
  panel.update(crewObservation());
  panel.mode("chart");
  assert.equal(panel.element.querySelector(".station"), null);
  assert.ok(panel.element.classList.contains("is-chart"));
  assert.deepEqual(rowsOf(panel, "vault"), ["gap", "de4c885"]);
  assert.deepEqual(rowsOf(panel, "remote"), ["21e6785", "de4c885"]);
  assert.match(zone(panel, "vault").querySelector(".caps").getAttribute("style"), /--row:40px/);
  panel.mode("zones");
  assert.ok(!panel.element.classList.contains("is-chart"));
  assert.deepEqual(rowsOf(panel, "vault"), ["de4c885"]);
});

test("in the chart a commit both sides hold is marked shared on each side and tethered across, once", () => {
  const panel = ZonePanel.create();
  panel.update(crewObservation());
  panel.mode("chart");
  const shared = (name) => [...zone(panel, name).querySelectorAll(".cap.is-shared")].map((row) => row.dataset.key.split(":")[1].slice(0, 7));
  assert.deepEqual(shared("vault"), ["de4c885"]);
  assert.deepEqual(shared("remote"), ["de4c885"]);
  const tethers = [...panel.element.querySelectorAll("svg.tethers line")];
  assert.deepEqual(tethers.map((line) => line.dataset.hash.slice(0, 7)), ["de4c885"]);
  panel.mode("zones");
  assert.equal(panel.element.querySelectorAll(".cap.is-shared, svg.tethers line").length, 0);
});

test("the chart says a paused merge over the whole chart, not inside the vault, so both sides' rows stay level", () => {
  const project = { ...record("snapshots").one, operation: "merge", files: [{ ...record("snapshots").one.files[0], conflicted: true, index_change: "modified" }] };
  const panel = ZonePanel.create();
  panel.update(observe(project));
  const banner = panel.element.querySelector(".viz-op");
  assert.equal(banner.hidden, true);
  panel.mode("chart");
  assert.equal(banner.hidden, false);
  assert.equal(banner.textContent, "merge paused");
  assert.ok(banner.querySelector("svg.art-icon--merging"));
  assert.equal(zone(panel, "vault").querySelector(".z-op").hidden, true);
  panel.mode("zones");
  assert.equal(banner.hidden, true);
  assert.equal(zone(panel, "vault").querySelector(".z-op").hidden, false);
});

test("a push in the chart flies the capsule across to its own row on the mothership", () => {
  const proto = Object.getPrototypeOf(document.createElement("div"));
  const sized = proto.getBoundingClientRect;
  proto.getBoundingClientRect = () => ({ x: 0, y: 0, top: 0, left: 0, width: 10, height: 10, right: 10, bottom: 10 });
  proto.animate = () => ({ finished: new Promise(() => {}) });
  /* A shallow copy is enough here: the test looks only at which item flies. */
  proto.cloneNode = function () {
    const copy = document.createElement(this.tagName.toLowerCase());
    copy.setAttribute("data-key", this.dataset.key);
    return copy;
  };
  try {
    const panel = ZonePanel.create({ reducedMotion: false, timers: createClock() });
    const project = { ...named(record("snapshots").one), head: "c2", branch: "main", commits: [capsuleCommit("c2", ["c1"]), capsuleCommit("c1")], refs: [{ name: "main", kind: "branch", target: "c2" }] };
    const github = { ...record("snapshots").one, bare: true, head: "c1", branch: "main", commits: [capsuleCommit("c1")], refs: [{ name: "main", kind: "branch", target: "c1" }] };
    panel.update(observe(project, github));
    panel.mode("chart");
    assert.deepEqual(rowsOf(panel, "remote"), ["gap", "c1"]);
    panel.update({ ...observe(project, { ...github, head: "c2", commits: project.commits, refs: project.refs }), commands: [{ line: "git push", status: 0 }] });
    assert.deepEqual(rowsOf(panel, "remote"), ["c2", "c1"]);
    const flown = [...document.body.querySelectorAll(".ghost")].map((ghost) => ghost.dataset.key).filter((key) => !key.includes("-ref:"));
    assert.deepEqual(flown, ["vault:c2"]);
  } finally {
    proto.getBoundingClientRect = sized;
    delete proto.animate;
    delete proto.cloneNode;
    for (const ghost of document.body.querySelectorAll(".ghost")) ghost.remove();
  }
});

test("under the chart a key says what the tethers mean, once there is one to see", () => {
  const panel = ZonePanel.create();
  const key = panel.element.querySelector(".chart-key");
  assert.equal(key.textContent, "Dashed line: the same commit, in your vault and on the mothership.");
  assert.ok(key.querySelector(".chart-key-tether"));
  panel.update(observe(record("observation").project));
  panel.mode("chart");
  assert.equal(key.hidden, true);
  panel.update(crewObservation());
  assert.equal(key.hidden, false);
});

test("in a level with no mothership the chart is your vault alone; a mothership not named yet stays on it", () => {
  const panel = ZonePanel.create();
  panel.update(observe(record("observation").project));
  panel.mode("chart");
  assert.ok(panel.element.classList.contains("no-mothership"));
  panel.update(observe(record("observation").project, record("snapshots").one));
  assert.ok(!panel.element.classList.contains("no-mothership"));
});
