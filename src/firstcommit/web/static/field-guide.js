"use strict";

/*
 * The field guide, from the map or over a level: three infographics drawn by the artist
 * (art-infographics.js) from the words of infographic-text.js: Git's four places and the commands
 * between them, a file's states, and every command the game teaches; then a merge conflict, step
 * by step (guide-conflict.js). Clicking a command opens its card (guide-card.js, words from
 * guide-text.js, git's output from guide-git.js) in a modal dialog of its own: Escape or Close
 * shuts the card alone and gives the focus back to the command. Everything is readable from the
 * start; what a sector still ahead teaches is tagged with that sector ("coming up in sector 5",
 * or "coming up later" for one the map does not list yet), so progress still shows. An item is
 * taught once enough levels of its chapter are done (firstcommit/game.py's Status). The words
 * are the page's language. Needs dom.js, strings.js, art-sprites.js, art-infographics.js,
 * infographic-text.js and the guide-*.js modules. Defines one global, FieldGuide.
 *
 * create(ctx, {onClose}) {element}: the guide for ctx.status(); with onClose, as an overlay over a
 *                       level, its head offers Close (which calls it) instead of the way to the map.
 * taught(status, taught) whether an item's lesson ({chapter, levels}) is done.
 */

/* global Dom, Strings, ArtSprites, ArtInfographics, InfographicText, GuideText, GuideGit, GuideCard, GuideConflict */
/* exported FieldGuide */

const FieldGuide = (function () {
  const { el } = Dom;

  /* Whether `taught` ({chapter, levels}) is met in `status`: that many of the chapter's levels
     done, in any order, or all of them when `levels` is left out; a chapter with no levels yet
     has taught nothing. */
  function taught(status, { chapter: id, levels }) {
    const chapter = status.chapters.find((item) => item.id === id);
    if (!chapter || chapter.levels.length === 0) return false;
    const done = chapter.levels.filter((level) => level.done).length;
    return done >= (levels ?? chapter.levels.length);
  }

  /* The text in one language: each {en, es} pair becomes its string in `language`. */
  function localized(value, language) {
    if (typeof value !== "object" || value === null) return value;
    if (Array.isArray(value)) return value.map((item) => localized(item, language));
    if ("en" in value) return value[language];
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, localized(item, language)]));
  }

  /* The items with their `taught` replaced by `tag`: null once taught, else the sector ahead that teaches it. */
  function tagged(status, text, list) {
    return list.map(({ taught: lesson, ...item }) => {
      const sector = status.chapters.findIndex((chapter) => chapter.id === lesson.chapter) + 1;
      const ahead = sector ? text.upcoming.replace("{sector}", String(sector)) : text.later;
      return { ...item, tag: taught(status, lesson) ? null : ahead };
    });
  }

  function head(text, onClose) {
    const away = onClose
      ? el("button", { type: "button", class: "btn guide-close", onclick: onClose }, ArtSprites.icon("back"), Strings.t("guide.close"))
      : el("a", { class: "btn", href: "#/" }, ArtSprites.icon("back"), Strings.t("guide.map"));
    return el("header", { class: "guide-head" }, away, el("div", {}, el("h1", {}, text.title), el("p", {}, text.lede)));
  }

  /* A place's label: its real Git name first, the game's name after it in parentheses. */
  const placeLabel = (place) => `${place.name} (${place.space.toLowerCase()})`;
  const PICTURE_PLACES = { folder: "workshop", staging: "dock", vault: "vault", remote: "mothership" };

  /* Where the game teaches a command: "Sector 2, mission 3: <title>" for the first mission of
     the taught chapter whose command label is one of `lessons`, else "Sector 2: <chapter>",
     else a sector the map does not list yet. */
  function whereTaught(status, words, chapterId, lessons) {
    const sector = status.chapters.findIndex((chapter) => chapter.id === chapterId);
    if (sector < 0 || status.chapters[sector].levels.length === 0) return words.taughtLater;
    const chapter = status.chapters[sector];
    const mission = chapter.levels.findIndex((item) => lessons.includes(item.command));
    const fill = (text, values) => Object.entries(values).reduce((done, [key, value]) => done.replace(`{${key}}`, String(value)), text);
    if (mission < 0) return fill(words.taughtIn, { sector: sector + 1, title: chapter.title });
    return fill(words.taughtAt, { sector: sector + 1, mission: mission + 1, title: chapter.levels[mission].title });
  }

  /* A card with what real git printed put in from GuideGit: its transcripts, its frames' and
     sections' (named by `run`), and the message git prepares for a merge (`message: true`). */
  function withGit(card) {
    const framed = (item) => ({ ...item, run: item.run && GuideGit.runs[item.run], message: item.message && GuideGit.mergeMessage });
    return {
      ...card,
      runs: card.runs.map((name) => GuideGit.runs[name]),
      picture: card.picture && card.picture.frames ? { ...card.picture, frames: card.picture.frames.map(framed) } : card.picture,
      sections: (card.sections || []).map((section) => ({ ...framed(section), frames: section.frames.map(framed) })),
    };
  }

  /* The cards' modal dialog, one per guide: open(command, opener) shows that command's card and
     gives the focus back to `opener` when it closes. Its cancel and close stay its own, so a
     guide that is itself a dialog over a level stays open. */
  function cardDialog({ status, text, guideText, commandItems, chapterOf, conflict }) {
    const pictures = { ...guideText.pictures, places: Object.fromEntries(Object.entries(PICTURE_PLACES).map(([key, id]) => [key, placeLabel(text.places.places.find((place) => place.id === id))])) };
    const words = { card: guideText.card, pictures };
    const body = el("div", { class: "guide-card-body" });
    let opener = null;
    const dialog = el("dialog", {
      class: "guide-card-dialog",
      oncancel: (event) => event.stopPropagation(),
      onclose: (event) => {
        event.stopPropagation();
        opener?.focus();
      },
    },
    el("button", { type: "button", class: "btn guide-card-close", onclick: () => dialog.close() }, ArtSprites.icon("back"), guideText.card.close),
    body);

    function show(command) {
      const card = guideText.cards.find((item) => item.command === command);
      const item = commandItems.find((entry) => entry.command === command);
      body.replaceChildren(GuideCard.create({
        ...withGit(card), what: item.what, tag: item.tag, where: whereTaught(status, guideText.card, chapterOf.get(command), card.lessons),
      }, words, {
        onRelated: show,
        onConflict: () => {
          opener = null;
          dialog.close();
          conflict.scrollIntoView?.({ block: "start" });
          conflict.focus();
        },
      }));
      if (!dialog.open) dialog.showModal();
      dialog.scrollTop = 0;
    }

    function open(command, button) {
      opener = button;
      show(command);
    }

    return { dialog, open };
  }

  /* The bar that jumps to each part: a button per part that scrolls to it and focuses it. */
  function jumpBar(words, parts) {
    const go = (part) => {
      part.scrollIntoView?.({ block: "start" });
      part.focus();
    };
    return el("nav", { class: "guide-jump", "aria-label": words.label },
      parts.map(([key, part]) => el("button", { type: "button", class: "btn btn-quiet", onclick: () => go(part) }, words[key])));
  }

  function create(ctx, { onClose = null } = {}) {
    const status = ctx.status();
    const language = Strings.language();
    const text = localized(InfographicText, language);
    const guideText = localized(GuideText, language);
    const { places, states, commands } = text;
    const tag = (list) => tagged(status, text, list);
    const groups = commands.groups.map((group) => ({ title: group.title, commands: tag(group.commands) }));
    const conflict = GuideConflict.create(GuideGit, guideText.conflict).element;
    const chapterOf = new Map(commands.groups.flatMap((group) => group.commands).map((item) => [item.command, item.taught.chapter]));
    const cards = cardDialog({ status, text, guideText, commandItems: groups.flatMap((group) => group.commands), chapterOf, conflict });
    const boxes = tag(places.places).map((place) => ({ ...place, space: place.name, git: `(${place.space.toLowerCase()})` }));
    const parts = [
      ["places", ArtInfographics.places({ title: places.title, places: boxes, moves: tag(places.moves) })],
      ["states", ArtInfographics.states({ title: states.title, states: tag(states.states), moves: tag(states.moves) })],
      ["commands", ArtInfographics.commands({ title: commands.title, groups, open: cards.open })],
      ["conflict", conflict],
    ];
    for (const [, part] of parts) part.setAttribute("tabindex", "-1");
    const element = el("div", { class: "field-guide" },
      head(text, onClose),
      jumpBar(text.jump, parts),
      parts.map(([, part]) => part),
      cards.dialog,
    );
    return { element };
  }

  return { create, taught };
})();
