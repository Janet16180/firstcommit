"use strict";

/*
 * Lookups on the dashboard (firstcommit/game.py's Status) that several views show. They only
 * read what the server sent: no XP or rank is computed here. Defines one global, Progress.
 */

/* exported Progress */

const Progress = (function () {
  const allLevels = (chapters) => chapters.flatMap((chapter) => chapter.levels.map((level) => ({ ...level, chapter })));

  /* The level to suggest: the first one not done after `afterId` in map order, else from the
     start of the map, never `afterId` itself; null when there is none. */
  function nextLevel(chapters, afterId = null) {
    const levels = allLevels(chapters);
    const after = levels.findIndex((level) => level.id === afterId);
    const ordered = [...levels.slice(after + 1), ...levels.slice(0, after + 1)];
    return ordered.find((level) => !level.done && level.id !== afterId) || null;
  }

  /* The level to start with: the first in play order while no level is finished, else null. */
  function startLevel(chapters) {
    const levels = allLevels(chapters);
    return levels.some((level) => level.done) ? null : levels[0] || null;
  }

  /* A level and its chapter, or null. */
  const findLevel = (chapters, id) => allLevels(chapters).find((level) => level.id === id) || null;

  /* How far the player is from this rank's floor to the next rank, and the XP still needed. */
  function rankProgress(status) {
    const { rank, xp } = status;
    if (rank.next_at === null) return { fraction: 1, toNext: null };
    return { fraction: (xp - rank.floor) / (rank.next_at - rank.floor), toNext: rank.next_at - xp };
  }

  return { nextLevel, startLevel, findLevel, rankProgress };
})();
