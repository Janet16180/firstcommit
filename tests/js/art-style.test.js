"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { STYLE, TOKENS } = require("./art-check");

const rules = (selector) => [...STYLE.matchAll(/([^{}]+)\{([^{}]*)\}/g)].filter(([, selectors]) => selectors.split(",").some((part) => part.trim() === selector)).map(([, , body]) => body);

test("every animation runs on a keyframes rule the sheet defines, in steps", () => {
  const keyframes = new Set([...STYLE.matchAll(/@keyframes\s+([\w-]+)/g)].map((match) => match[1]));
  const used = [...STYLE.matchAll(/animation:\s*([\w-]+)\s+([^;]+);/g)].filter(([, name]) => name !== "none");
  assert.ok(used.length > 10);
  for (const [, name, rest] of used) {
    assert.ok(keyframes.has(name), `${name} is defined`);
    assert.match(rest, /steps\(\d+\)/, `${name} runs in steps`);
  }
});

test("reduced motion stops the art's animations and hides the burst", () => {
  const reduced = STYLE.slice(STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  assert.ok(reduced.length > 0 && reduced.includes("@media"));
  assert.match(reduced, /\.art-scene \*[\s\S]*animation: none !important/);
  assert.match(reduced, /\.art-sparks\s*\{\s*display: none;/);
});

test("the art tokens are fixed colours, the same in light and dark mode", () => {
  assert.equal(STYLE.match(/--art-[\w-]+:\s*#[0-9A-F]{6};/g).length, STYLE.match(/--art-[\w-]+:/g).length);
  assert.ok(!STYLE.includes("prefers-color-scheme"));
  assert.equal(rules(":root").length, 1);
});

test("a conflicted file chip shakes once while a crack flashes over it", () => {
  assert.match(rules(".art-crack").join(""), /animation: art-crack 0\.6s steps\(\d+\)/);
  const crack = rules(".art-crack::after").join("");
  assert.match(crack, /content: ""/);
  assert.match(crack, /position: absolute/);
  assert.match(crack, /animation: art-crack-flash 0\.6s steps\(\d+\)/);
  assert.match(rules(".art-crack").join(""), /position: relative/);
});

test("a revert capsule rises from below upside down and turns upright", () => {
  assert.match(rules(".art-rise-inverted").join(""), /animation: art-rise-inverted 0\.8s steps\(\d+\) both/);
  const frames = STYLE.slice(STYLE.indexOf("@keyframes art-rise-inverted"));
  assert.match(frames, /from \{ transform: translateY\(\d+px\) scaleY\(-1\)/);
});

test("the conflict and paused merge icons wear their state colours unless the page sets one", () => {
  assert.match(rules(".art-icon--conflict").join(""), /color: var\(--s-new\)/);
  assert.match(rules(".art-icon--merging").join(""), /color: var\(--s-mod\)/);
  assert.match(rules(".art-icon--inverted").join(""), /color: var\(--zc, var\(--z-va\)\)/);
});

test("reduced motion stops the crack, the inverted rise and the blinking pause bar", () => {
  const reduced = STYLE.slice(STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  for (const selector of [".art-crack", ".art-crack::after", ".art-rise-inverted", ".art-pause"]) assert.ok(reduced.includes(selector), selector);
});

test("a station frames its zones in its crew member's colour, with a name tab on the border", () => {
  const frame = rules(".art-station").join("");
  assert.match(frame, /--station-colour: var\(--z-va\)/);
  assert.match(frame, /border: 4px solid var\(--station-colour\)/);
  assert.match(frame, /min-width: 0/);
  assert.match(rules(".art-station--you").join(""), /--station-colour: var\(--z-va\)/);
  assert.match(rules(".art-station--alex").join(""), /--station-colour: var\(--z-re\)/);
  const tab = rules(".art-station-name").join("");
  assert.match(tab, /position: absolute/);
  assert.match(tab, /border: 3px solid var\(--station-colour\)/);
  assert.match(tab, /background: var\(--panel\)/);
});

test("a flying capsule trails an exhaust flame, above it when it lands", () => {
  const flame = rules(".art-crew-flight::after").join("");
  assert.match(flame, /content: ""/);
  assert.match(flame, /top: 100%/);
  assert.match(flame, /animation: art-crew-flame 0\.2s steps\(2\) infinite/);
  assert.match(rules(".art-crew-flight--down::after").join(""), /bottom: 100%/);
  const reduced = STYLE.slice(STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  assert.ok(reduced.includes(".art-crew-flight::after"));
});

const BIRTH = "var(--art-birth, 1.4s)";
const frames = (name) => STYLE.slice(STYLE.indexOf(`@keyframes ${name}`)).match(/^@keyframes[^{]*\{([\s\S]*?\}\s*)\}/)[1];
const birthAnimation = (selector) => rules(selector).join("").match(/animation: ([\w-]+) (.+?) steps\(\d+\) both;/);

test("the fold folds each zone up toward the strip, small and faded, over the page's birth time", () => {
  const zone = rules(".sky.art-birth-fold .viz .zone").join("");
  assert.match(zone, /transform-origin: top/);
  const [, name, duration] = birthAnimation(".sky.art-birth-fold .viz .zone");
  assert.equal(duration, BIRTH);
  assert.match(frames(name), /to \{ transform: translateY\(-\d+px\) scale\(0\.\d+, 0\.\d+\); opacity: 0; \}/);
});

test("in the fold each strip card lands from below, where its zone was, and stays", () => {
  assert.match(rules(".sky.art-birth-fold .strip-card").join(""), /transform-origin: bottom/);
  const [, name, duration] = birthAnimation(".sky.art-birth-fold .strip-card");
  assert.equal(duration, BIRTH);
  assert.match(frames(name), /from \{ transform: translateY\(\d+px\) scale\(0\.\d+\); opacity: 0; \}/);
  assert.match(frames(name), /to \{ transform: none; opacity: 1; \}/);
});

test("in the fold the flows and the legend fade out", () => {
  const [, flow, duration] = birthAnimation(".sky.art-birth-fold .viz .flow");
  assert.equal(duration, BIRTH);
  assert.deepEqual(birthAnimation(".sky.art-birth-fold .viz .legend").slice(1), [flow, BIRTH]);
  assert.match(frames(flow), /to \{ opacity: 0; \}/);
});

test("the unroll reveals every vault from the top down, then the mothership fades in", () => {
  const [, unroll, duration] = birthAnimation('.sky.art-birth-unroll .viz .zone[data-zone$="vault"]');
  assert.equal(duration, BIRTH);
  assert.match(frames(unroll), /from \{ clip-path: inset\(0 0 100% 0\); \}/);
  assert.match(frames(unroll), /clip-path: inset\(0\);/);
  const [, mothership, after] = birthAnimation('.sky.art-birth-unroll .viz .zone[data-zone="remote"]');
  assert.equal(after, BIRTH);
  assert.match(frames(mothership), /0%, \d+% \{ opacity: 0; \}/);
  assert.match(frames(mothership), /to \{ opacity: 1; \}/);
});

test("the unroll starts with the strip's vault card lit in its own colour", () => {
  const [, name, duration] = birthAnimation('.sky.art-birth-unroll .strip-card[data-zone="vault"]');
  assert.equal(duration, BIRTH);
  assert.match(frames(name), /background: color-mix\(in srgb, var\(--zc\) \d+%, var\(--panel\)\)/);
});

test("the births paint only with the design's tokens", () => {
  const births = STYLE.slice(STYLE.indexOf(".sky.art-birth-fold"), STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  assert.ok(births.length > 0);
  for (const [, name] of births.matchAll(/var\((--[\w-]+)/g)) assert.ok(TOKENS.has(name) || ["--art-birth", "--zc"].includes(name), name);
  assert.ok(!/#[0-9A-Fa-f]{3,6}\b|\brgba?\(|\bhsla?\(/.test(births));
});

test("reduced motion plays neither birth", () => {
  const reduced = STYLE.slice(STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  for (const selector of [".sky.art-birth-fold *", ".sky.art-birth-unroll *"]) assert.ok(reduced.includes(selector), selector);
});

test("the flatten squashes Alex's mirrored station up into a thin fading line over the page's birth time", () => {
  assert.match(rules(".sky.art-birth-flatten .station.is-mirror").join(""), /transform-origin: top/);
  const [, name, duration] = birthAnimation(".sky.art-birth-flatten .station.is-mirror");
  assert.equal(duration, BIRTH);
  assert.match(frames(name), /0%, \d+% \{ transform: none; opacity: 1; \}/);
  assert.match(frames(name), /to \{ transform: translateY\(-\d+px\) scaleY\(0\.0\d+\); opacity: 0; \}/);
  const [, flows] = birthAnimation(".sky.art-birth-flatten .flow.is-mirror");
  assert.equal(flows, "art-birth-fade-out");
});

test("in the flatten the band's cards land from below without touching their resting opacity, then the name shows", () => {
  const card = ".sky.art-birth-flatten .strip.is-band .strip-card";
  assert.match(rules(card).join(""), /transform-origin: bottom/);
  const [, name, duration] = birthAnimation(card);
  assert.equal(duration, BIRTH);
  assert.match(frames(name), /from \{ transform: translateY\(\d+px\) scaleY\(0\); \}/);
  assert.match(frames(name), /to \{ transform: none; \}/);
  assert.ok(!/opacity/.test(frames(name)), "the band's own opacity stays");
  assert.deepEqual(birthAnimation(".sky.art-birth-flatten .strip.is-band .strip-who").slice(1), ["art-birth-after", BIRTH]);
});

test("reduced motion plays no flatten", () => {
  const reduced = STYLE.slice(STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  assert.ok(reduced.includes(".sky.art-birth-flatten *"));
});

test("an ignored folder's chip sits behind a calm scanline field with emitters at its corners, behind its words", () => {
  const chip = rules(".art-ignore-field").join("");
  assert.match(chip, /position: relative/);
  assert.match(chip, /isolation: isolate/);
  const field = rules(".art-ignore-field::after").join("");
  assert.match(field, /content: ""/);
  assert.match(field, /position: absolute/);
  assert.match(field, /z-index: -1/);
  assert.match(field, /pointer-events: none/);
  assert.match(field, /repeating-linear-gradient\(/);
  assert.equal((field.match(/no-repeat/g) || []).length, 4, "four corner emitters");
  for (const [, token] of field.matchAll(/var\((--[\w-]+)/g)) assert.ok(TOKENS.has(token), token);
  assert.ok(!/#[0-9A-Fa-f]{3,6}\b|\brgba?\(|\bhsla?\(/.test(field));
  assert.ok(!/::before/.test(STYLE.match(/\.art-ignore-field[^{]*\{/g).join("")), "the chip's ::before is its state dot");
  const reduced = STYLE.slice(STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  assert.ok(reduced.includes(".art-ignore-field::after"));
});

test("the book opens each file's two halves outward from the spine like pages, over the page's birth time", () => {
  for (const [side, origin, sign] of [["you", "right", "-"], ["them", "left", ""]]) {
    const selector = `.sky.art-birth-book .sides-half[data-side="${side}"]`;
    assert.match(rules(selector).join(""), new RegExp(`transform-origin: ${origin}`));
    const [, name, duration] = birthAnimation(selector);
    assert.equal(duration, BIRTH);
    assert.match(frames(name), new RegExp(`0%, \\d+% \\{ transform: perspective\\(\\d+px\\) rotateY\\(${sign}8\\ddeg\\)`));
    assert.match(frames(name), /to \{ transform: none; \}/);
  }
});

test("the book starts closed on a red crack down its spine, which fades as the pages open", () => {
  const crack = rules(".sky.art-birth-book .sides-pages::after").join("");
  assert.match(crack, /content: ""/);
  assert.match(crack, /position: absolute/);
  assert.match(crack, /var\(--s-new\)/);
  assert.match(rules(".sky.art-birth-book .sides-pages").join(""), /position: relative/);
  const [, name, duration] = birthAnimation(".sky.art-birth-book .sides-pages::after");
  assert.equal(duration, BIRTH);
  assert.match(frames(name), /0%, \d+% \{ opacity: 1; \}/);
  assert.match(frames(name), /to \{ opacity: 0; \}/);
});

test("in the book the base line fades in last", () => {
  assert.deepEqual(birthAnimation(".sky.art-birth-book .sides-base").slice(1), ["art-birth-after", BIRTH]);
});

test("reduced motion plays no book", () => {
  const reduced = STYLE.slice(STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  assert.ok(reduced.includes(".sky.art-birth-book *"));
  assert.ok(reduced.includes(".sky.art-birth-book .sides-pages::after"));
});

const CASING = '.sky[data-view="blackbox"] .viz-kept.art-blackbox';

test("the black box wears a flight recorder's casing only in its view: a hard shadow, rivets and a hazard band behind the zones", () => {
  const selectors = [...STYLE.matchAll(/([^{}]*\.art-blackbox[^{}]*)\{/g)].flatMap(([, list]) => list.split(",")).filter((selector) => selector.includes(".art-blackbox"));
  assert.ok(selectors.length > 0);
  for (const selector of selectors) assert.match(selector.trim(), /^\.sky(\[data-view="blackbox"\]|\.art-birth-boundary) /, "nowhere else");
  const casing = rules(CASING).join("");
  assert.match(casing, /isolation: isolate/);
  assert.match(casing, /box-shadow: \d+px \d+px 0 var\(--edge\)/);
  const plate = rules(`${CASING}::before`).join("");
  assert.match(plate, /content: ""/);
  assert.match(plate, /position: absolute/);
  assert.match(plate, /z-index: -1/);
  assert.match(plate, /pointer-events: none/);
  assert.equal((plate.match(/no-repeat/g) || []).length, 5, "four rivets and the band");
  assert.match(plate, /repeating-linear-gradient\(-45deg, var\(--gold\)/);
});

test("the black box's name sits on a recorder plate with a steady lamp", () => {
  const name = rules(`${CASING} .viz-kept-name`).join("");
  assert.match(name, /background: var\(--panel\)/);
  assert.match(name, /border: 2px solid var\(--ink\)/);
  assert.match(name, /box-shadow: 2px 2px 0 var\(--edge\)/);
  const lamp = rules(`${CASING} .viz-kept-name::before`).join("");
  assert.match(lamp, /content: ""/);
  assert.match(lamp, /background: var\(--s-new\)/);
  assert.ok(!/animation/.test(lamp), "the lamp does not blink");
});

test("the boundary traces the frame's four edges round the kept zones over the page's birth time", () => {
  assert.match(rules(".sky.art-birth-boundary .viz-kept.art-blackbox").join(""), /border-color: transparent/);
  const trace = ".sky.art-birth-boundary .viz-kept.art-blackbox::after";
  const edges = rules(trace).join("");
  assert.match(edges, /content: ""/);
  assert.match(edges, /inset: -3px/);
  assert.match(edges, /pointer-events: none/);
  assert.equal((edges.match(/linear-gradient\(var\(--ink\) 0 0\)/g) || []).length, 4, "four edges");
  assert.match(edges, /background-size: 100% 3px, 3px 100%, 100% 3px, 3px 100%;/, "drawn whole when still");
  const [, name, duration] = birthAnimation(trace);
  assert.equal(duration, BIRTH);
  assert.match(frames(name), /0%, \d+% \{ background-size: 0 3px, 3px 0, 0 3px, 3px 0; \}/);
  assert.match(frames(name), /to \{ background-size: 100% 3px, 3px 100%, 100% 3px, 3px 100%; \}/);
});

test("in the boundary the casing shows after the trace, the plate lands and the workshop outside dims, then returns", () => {
  assert.deepEqual(birthAnimation(".sky.art-birth-boundary .viz-kept.art-blackbox::before").slice(1), ["art-birth-after", BIRTH]);
  const [, plate, duration] = birthAnimation(".sky.art-birth-boundary .viz-kept.art-blackbox .viz-kept-name");
  assert.equal(duration, BIRTH);
  assert.match(frames(plate), /0%, \d+% \{ transform: translateY\(-\d+px\); opacity: 0; \}/);
  assert.match(frames(plate), /to \{ transform: none; opacity: 1; \}/);
  for (const outside of ['.sky.art-birth-boundary .viz-row > .zone[data-zone="workshop"]', ".sky.art-birth-boundary .viz-row > .flow"]) {
    const [, dim, time] = birthAnimation(outside);
    assert.equal(time, BIRTH);
    assert.match(frames(dim), /0%, \d+% \{ opacity: 1; \}/);
    assert.match(frames(dim), /opacity: 0\.\d+;/);
    assert.match(frames(dim), /to \{ opacity: 1; \}/);
  }
});

test("the casing and the boundary paint only with the design's tokens", () => {
  const art = STYLE.slice(STYLE.indexOf(`${CASING} {`), STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  assert.ok(art.includes("art-birth-boundary"));
  for (const [, name] of art.matchAll(/var\((--[\w-]+)/g)) assert.ok(TOKENS.has(name) || name === "--art-birth", name);
  assert.ok(!/#[0-9A-Fa-f]{3,6}\b|\brgba?\(|\bhsla?\(/.test(art));
});

test("reduced motion plays no boundary and leaves the frame drawn", () => {
  const reduced = STYLE.slice(STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  for (const selector of [".sky.art-birth-boundary *", ".sky.art-birth-boundary .viz-kept.art-blackbox::before", ".sky.art-birth-boundary .viz-kept.art-blackbox::after"]) assert.ok(reduced.includes(selector), selector);
});
