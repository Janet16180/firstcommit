"use strict";

/*
 * The game's API as the page uses it: one function per route of firstcommit/web/routes.py,
 * each checking that the reply has the shape of its record in firstcommit/game.py before the
 * page trusts it (Ring Zero audit JS-2). A reply of the wrong shape throws an Error naming the
 * route and the field, with no `status`; errors from the server keep client.js's `status`
 * (0 for no answer, else the HTTP status), so callers branch on the status, never on text.
 * Defines one global, createGameApi.
 */

/* exported createGameApi */

const createGameApi = (function () {
  const fail = (where, what) => {
    throw new Error(`${where} should be ${what}`);
  };
  const type = (name, what) => (value, where) => typeof value === name || fail(where, what);
  const text = type("string", "text");
  const number = (value, where) => Number.isFinite(value) || fail(where, "a number");
  const flag = type("boolean", "true or false");
  const nullable = (spec) => (value, where) => value === null || spec(value, where);
  const oneOf = (...choices) => (value, where) => choices.includes(value) || fail(where, `one of ${choices.join(", ")}`);
  const list = (spec) => (value, where) => {
    if (!Array.isArray(value)) fail(where, "a list");
    value.forEach((item, index) => spec(item, `${where}[${index}]`));
  };
  const isObject = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
  const record = (fields) => (value, where) => {
    if (!isObject(value)) fail(where, "an object");
    for (const [name, spec] of Object.entries(fields)) spec(value[name], `${where}.${name}`);
  };
  /* An object whose keys are ids and whose every value fits `spec`. */
  const mapping = (spec) => (value, where) => {
    if (!isObject(value)) fail(where, "an object");
    for (const [key, item] of Object.entries(value)) spec(item, `${where}.${key}`);
  };

  const SPANS = list(record({ text, code: flag }));
  const BLOCK_KINDS = {
    para: record({ spans: SPANS }),
    code: record({ text }),
    bullets: record({ items: list(SPANS) }),
  };
  const BLOCK = (value, where) => {
    record({ kind: oneOf(...Object.keys(BLOCK_KINDS)) })(value, where);
    BLOCK_KINDS[value.kind](value, where);
  };
  const BLOCKS = list(BLOCK);

  const COMMIT = record({ hash: text, short: text, parents: list(text), subject: text, author: text, time: number });
  const SNAPSHOT = record({
    exists: flag,
    bare: flag,
    head: nullable(text),
    branch: nullable(text),
    commits: list(COMMIT),
    refs: list(record({ name: text, kind: oneOf("branch", "remote", "tag"), target: text })),
    remotes: list(record({ name: text, url: text })),
    files: list(record({
      path: text,
      head: nullable(text),
      index: nullable(text),
      folder: nullable(text),
      head_mode: nullable(text),
      index_mode: nullable(text),
      folder_mode: nullable(text),
      ignored: flag,
      conflicted: flag,
      repository: flag,
      index_change: nullable(oneOf("added", "modified", "deleted", "typechange")),
      folder_change: nullable(oneOf("modified", "deleted", "typechange", "untracked", "ignored")),
    })),
    operation: nullable(text),
    stash: number,
    truncated: flag,
  });
  const ACTIVE = record({ level: text, step: number, steps: number, hints: number, hints_total: number, attempts: number, started: text, auto_check: flag, commands: number, stars: number, done: list(text) });
  const PAYOUT = record({ level: text, xp: number, first_time: flag, rank_before: text, rank_after: text });
  const LEVEL_SUMMARY = record({ id: text, title: text, difficulty: number, xp: number, command: text, stars: number, challenge: flag, done: flag, has_quest: flag });
  /* A finished level's command card (records.CommandCard). */
  const CARD = record({ level: text, command: text, text: BLOCKS });
  /* The scene pictures the artist has drawn, the moods Rama speaks in, the moments a reaction may
     play and the views of the ladder, in its order (records.Art, Mood, Moment and View). */
  const ART = oneOf("space", "timeline", "terminal", "planet", "flag", "zones", "conveyor", "capsule", "chain", "orbit", "rocket", "pull", "alarm", "fork", "merge", "collision", "blackbox", "meteor");
  const MOOD = oneOf("info", "ok", "warn", "err");
  const MOMENT = oneOf("secret-leak", "launch", "junk-flood", "force-break", "unreviewed-main", "search-beam");
  const VIEW = oneOf("station", "crew", "history", "sides", "blackbox", "board", "focus");
  /* What the save remembers as born: the views, the crew band and the black box's tape, which no
     level opens on (records.Seen). */
  const SEEN = oneOf("station", "crew", "history", "sides", "blackbox", "board", "focus", "band", "tape");

  const STATUS = record({
    xp: number,
    rank: record({ title: text, floor: number, next_title: nullable(text), next_at: nullable(number) }),
    chapters: list(record({ id: text, title: text, blurb: text, levels: list(LEVEL_SUMMARY), cards: number })),
    active: nullable(ACTIVE),
    last_payout: nullable(PAYOUT),
    cards_due: number,
    max_difficulty: number,
    collection: list(CARD),
    language: oneOf("en", "es"),
  });
  const LEVEL = record({
    id: text,
    chapter: text,
    chapter_title: text,
    title: text,
    difficulty: number,
    xp: number,
    command: text,
    par: number,
    scene: list(record({ art: ART, text: BLOCKS })),
    scene_seen: flag,
    view: VIEW,
    views_seen: list(SEEN),
    card: nullable(CARD),
    challenge: flag,
    briefing: BLOCKS,
    question: BLOCKS,
    placeholder: text,
    steps: list(record({ id: text, kind: oneOf("answer", "watch", "read", "choice"), text: BLOCKS, command: text, question: BLOCKS, placeholder: text, choices: list(record({ value: text, text: BLOCKS })), more: BLOCKS })),
    hints_total: number,
    hints: list(BLOCKS),
    debrief: nullable(BLOCKS),
  });
  const EVENTS = list(record({ kind: text, text: BLOCKS }));
  const STEP = record({ correct: flag, message: BLOCKS, step: number, quest_done: flag, done: list(text), lost: flag });
  const CHECK = record({ solved: flag, message: BLOCKS, payout: nullable(PAYOUT), debrief: nullable(BLOCKS), stars: number, new_card: nullable(CARD), lost: flag });
  const HINT = record({ hint: BLOCKS, used: number, total: number, cost: number });
  /* The playground's people and every id of its buttons (records.Who and playground.BUTTON_IDS; a
     Python test keeps them equal). */
  const WHO = oneOf("you", "alex");
  const BUTTON = oneOf("add:README.md", "add:notes.txt", "commit", "edit:README.md", "edit:notes.txt", "fetch", "keep-ours:README.md", "keep-ours:notes.txt", "keep-theirs:README.md", "keep-theirs:notes.txt", "merge-abort", "pull", "pull-no-rebase", "push", "status");
  /* Each person's bar, in bar order ({} without a playground). */
  const BARS = (value, where) => {
    mapping(list(record({ id: BUTTON, label: text, line: text, off: text })))(value, where);
    for (const person of Object.keys(value)) WHO(person, `${where}'s key`);
  };
  /* A conflicted file's two halves, as git's index stages hold them: a side's lines are null when it deleted the file. */
  const CONFLICT_SIDE = record({ label: text, author: text, lines: nullable(list(text)) });
  const CONFLICT = record({ path: text, you: CONFLICT_SIDE, them: CONFLICT_SIDE, base: nullable(list(text)) });
  /* One move of HEAD: the commit it left ("" for the first), the one it moved to, and git's note. */
  const REFLOG_ENTRY = record({ old: text, new: text, message: text });
  const OBSERVATION = record({ level: text, project: SNAPSHOT, github: nullable(SNAPSHOT), teammate: nullable(SNAPSHOT), events: EVENTS, teammate_events: EVENTS, buttons: BARS, commands: list(record({ line: text, status: number })), reactions: list(record({ line: text, mood: MOOD, text: BLOCKS, moment: nullable(MOMENT) })), conflicts: list(CONFLICT), reflog: list(REFLOG_ENTRY), ghosts: list(COMMIT) });
  const PRESSED = record({
    press: record({ person: WHO, button: BUTTON, command: text, status: number, output: text }),
    before: OBSERVATION,
    observation: OBSERVATION,
    explanation: nullable(BLOCKS),
    fix: nullable(BUTTON),
    fix_line: text,
  });
  const CARDS = record({
    cards: list(record({
      id: text,
      chapter: text,
      kind: oneOf("choice", "text", "predict"),
      level: number,
      level_name: text,
      prompt: BLOCKS,
      code: text,
      choices: list(record({ value: text, text: BLOCKS })),
      placeholder: text,
      pays: flag,
    })),
  });
  const CARD_RESULT = record({ correct: flag, answer: text, answer_text: BLOCKS, explain: BLOCKS, xp: number, streak: number, bonus: number });
  const NOTES = record({ chapter: text, title: text, notes: BLOCKS });
  const ABORTED = record({ level: nullable(text) });
  const NOTHING = record({});

  const query = (path, params) => {
    const pairs = Object.entries(params).filter(([, value]) => value !== null && value !== undefined);
    return pairs.length ? `${path}?${pairs.map(([name, value]) => `${name}=${encodeURIComponent(value)}`).join("&")}` : path;
  };

  /* `call` is client.js's api(path, body, timeoutMs). Starting a level builds its lab, so it may
     take longer than other calls. */
  return function gameApi(call, { startTimeoutMs = 120000 } = {}) {
    async function checked(spec, path, body, timeout) {
      const reply = await call(path, body, timeout);
      spec(reply, `the reply of ${path.split("?")[0]}`);
      return reply;
    }

    return {
      status: () => checked(STATUS, "/api/status"),
      level: (id) => checked(LEVEL, query("/api/level", { id })),
      start: (level) => checked(ACTIVE, "/api/start", { level }, startTimeoutMs),
      step: (answer) => checked(STEP, "/api/step", { answer }),
      check: (answer, auto) => checked(CHECK, "/api/check", { answer, auto }),
      hint: () => checked(HINT, "/api/hint", {}),
      observe: () => checked(OBSERVATION, "/api/observe"),
      abort: async () => (await checked(ABORTED, "/api/abort", {})).level,
      reset: () => checked(NOTHING, "/api/reset", { confirm: true }),
      cards: async (chapter, limit) => (await checked(CARDS, query("/api/cards", { chapter, limit }))).cards,
      card: (id, reply) => checked(CARD_RESULT, "/api/card", { id, reply }),
      notes: (chapter) => checked(NOTES, query("/api/notes", { chapter })),
      /* One person's playground button: the press, its explanation and the lab right after it. */
      press: (person, button) => checked(PRESSED, "/api/press", { person, button }),
      /* Marks a level's scene seen, so it does not play by itself again. */
      scene: (level) => checked(NOTHING, "/api/scene", { level }),
      /* Makes the game speak `language`; the records that follow come in it. */
      language: (language) => checked(NOTHING, "/api/language", { language }),
      /* Marks a view born, so its birth does not play again and its tab stays. */
      view: (view) => checked(NOTHING, "/api/view", { view }),
    };
  };
})();
