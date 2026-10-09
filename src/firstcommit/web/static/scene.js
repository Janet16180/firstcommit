"use strict";

/*
 * A level's scene: Rama's short explanation, one line at a time beside its picture (art-scenes.js),
 * each line typed in a few characters at a time as in the design. Next finishes a line still
 * typing, then moves on; Skip (or Escape) ends the scene. It opens on the browser's own <dialog>.
 * Needs dom.js, strings.js, art-sprites.js and art-scenes.js. Defines one global, ScenePlayer.
 *
 * play({scene, timers, reducedMotion, sound}) resolves once the scene is over; `scene` is the
 * level's list of {art, text} (LevelView.scene). With reduced motion each line shows whole at
 * once. `sound` (as sound.js) plays the typewriter while a line types and a page turn for each
 * new line.
 */

/* global Dom, Strings, ArtSprites, ArtScenes */
/* exported ScenePlayer */

const ScenePlayer = (function () {
  const { el } = Dom;
  const { t } = Strings;
  const TYPE_MS = 22;
  const STEP = 2;

  /* A line's paragraphs as pieces of text, each code or not; other kinds of block have no text to type. */
  const pieces = (blocks) => blocks.filter((block) => block.kind === "para").map((block) => block.spans);
  const length = (paragraphs) => paragraphs.flat().reduce((sum, span) => sum + span.text.length, 0);

  /* The first `count` characters of the paragraphs, as elements. */
  function typed(paragraphs, count) {
    let left = count;
    return paragraphs.map((spans) => el("p", {}, spans.map((span) => {
      const part = span.text.slice(0, Math.max(0, left));
      left -= span.text.length;
      return part && (span.code ? el("code", {}, part) : span.em ? el("em", {}, part) : part);
    })));
  }

  function play({ scene, timers, reducedMotion, sound = { play() {} } }) {
    if (!scene.length) return Promise.resolve();
    return new Promise((resolve) => {
      const parts = {
        art: el("div", { class: "cs-art" }),
        text: el("div", { class: "cs-txt", "aria-live": "polite" }),
        pips: el("div", { class: "pips", "aria-hidden": "true" }, scene.map(() => el("i"))),
        next: el("button", { type: "button", class: "btn btn-primary cs-next" }),
        skip: el("button", { type: "button", class: "btn cs-skip" }, t("scene.skip")),
      };
      const dialog = el("dialog", { class: "cutscene", "aria-label": t("scene.label") },
        parts.art,
        el("div", { class: "cs-dlg" },
          el("span", { class: "cs-who" }, t("scene.who")),
          ArtSprites.rama({ size: "comms" }),
          parts.text,
          el("div", { class: "cs-ctl" }, parts.pips, parts.skip, parts.next),
        ),
      );
      const state = { index: 0, shown: 0, total: 0, timer: null, art: null };

      function draw() {
        parts.text.replaceChildren(...typed(pieces(scene[state.index].text), state.shown));
      }

      function tick() {
        if (state.shown % (STEP * 3) === 0) sound.play("type");
        state.shown += STEP;
        draw();
        state.timer = state.shown < state.total ? timers.setTimeout(tick, TYPE_MS) : null;
      }

      function finish() {
        timers.clearTimeout(state.timer);
        state.timer = null;
        state.shown = state.total;
        draw();
      }

      function show() {
        const { art, text } = scene[state.index];
        if (art !== state.art) parts.art.replaceChildren(ArtScenes.scene(art, { label: t(`sceneLabel.${art}`), captions: Strings.group(`sceneCaption.${art}.`) }));
        if (state.index > 0) sound.play("page");
        state.art = art;
        parts.pips.querySelectorAll("i").forEach((pip, index) => pip.classList.toggle("on", index <= state.index));
        parts.next.textContent = t(state.index === scene.length - 1 ? "scene.start" : "scene.next");
        state.total = length(pieces(text));
        state.shown = 0;
        if (reducedMotion) finish();
        else state.timer = timers.setTimeout(tick, TYPE_MS);
        draw();
      }

      function next() {
        if (state.shown < state.total) return finish();
        state.index += 1;
        return state.index < scene.length ? show() : dialog.close();
      }

      dialog.addEventListener("close", () => {
        timers.clearTimeout(state.timer);
        dialog.remove();
        resolve();
      });
      parts.next.addEventListener("click", next);
      parts.skip.addEventListener("click", () => dialog.close());
      parts.text.addEventListener("click", next);
      parts.art.addEventListener("click", next);
      document.body.append(dialog);
      dialog.showModal();
      show();
      parts.next.focus();
    });
  }

  return { play, TYPE_MS };
})();
