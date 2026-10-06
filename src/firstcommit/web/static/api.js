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
  const record = (fields) => (value, where) => {
    if (value === null || typeof value !== "object" || Array.isArray(value)) fail(where, "an object");
    for (const [name, spec] of Object.entries(fields)) spec(value[name], `${where}.${name}`);
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

  const SNAPSHOT = record({
    exists: flag,
    bare: flag,
    head: nullable(text),
    branch: nullable(text),
    commits: list(record({ hash: text, short: text, parents: list(text), subject: text, author: text, time: number })),
    refs: list(record({ name: text, kind: oneOf("branch", "remote", "tag"), target: text })),
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
  const OBJECTS = list(record({ hash: text, type: text, size: number }));
  const ACTIVE = record({ level: text, step: number, steps: number, hints: number, hints_total: number, attempts: number, started: text, auto_check: flag });
  const PAYOUT = record({ level: text, xp: number, first_time: flag, rank_before: text, rank_after: text });
  const LEVEL_SUMMARY = record({ id: text, title: text, difficulty: number, xp: number, done: flag, has_lesson: flag, has_quest: flag });

  const STATUS = record({
    xp: number,
    rank: record({ title: text, floor: number, next_title: nullable(text), next_at: nullable(number) }),
    chapters: list(record({ id: text, title: text, levels: list(LEVEL_SUMMARY), cards: number })),
    active: nullable(ACTIVE),
    last_payout: nullable(PAYOUT),
    cards_due: number,
    max_difficulty: number,
  });
  const LEVEL = record({
    id: text,
    chapter: text,
    chapter_title: text,
    title: text,
    difficulty: number,
    xp: number,
    briefing: BLOCKS,
    question: BLOCKS,
    placeholder: text,
    steps: list(record({ id: text, kind: oneOf("answer", "watch", "read"), text: BLOCKS, command: text, question: BLOCKS, placeholder: text })),
    hints_total: number,
    has_lesson: flag,
    hints: list(BLOCKS),
    debrief: nullable(BLOCKS),
  });
  const LESSON = record({
    level: text,
    title: text,
    slides: list(record({
      id: text,
      title: text,
      text: BLOCKS,
      view: oneOf("map", "areas", "objects", "terminal", "none"),
      transcript: list(record({ command: text, output: text })),
      map: SNAPSHOT,
      objects: OBJECTS,
    })),
  });
  const STEP = record({ correct: flag, message: BLOCKS, step: number, quest_done: flag });
  const CHECK = record({ solved: flag, message: BLOCKS, payout: nullable(PAYOUT), debrief: nullable(BLOCKS) });
  const HINT = record({ hint: BLOCKS, used: number, total: number, cost: number });
  const OBSERVATION = record({ level: text, project: SNAPSHOT, github: nullable(SNAPSHOT), events: list(record({ kind: text, text: BLOCKS })) });
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
      lesson: (id) => checked(LESSON, query("/api/lesson", { id })),
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
    };
  };
})();
