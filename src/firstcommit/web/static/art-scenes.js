"use strict";

/*
 * The level scenes: the pictures beside Rama's short explanation the first time a level opens,
 * on the design's 160x90 night canvas, with its animations. Defines one global, ArtScenes;
 * dom.js and art-pixels.js load first, art-style.css animates them.
 *
 * NAMES                   the scenes there are, the values of the engine's `Art`: the design's
 *                         thirteen and fork, merge, collision and blackbox for chapters 5 to 7.
 * scene(name, {label})    a new <svg> of that scene, named by `label` or by the scene's own
 *                         description; it scales to its box (the page sets the width).
 */

/* global Dom, ArtPixels */
/* exported ArtScenes */

const ArtScenes = (function () {
  const { tone, draw, place, picture, stars, rama: ramaParts, planet, ARROW, sprite } = ArtPixels;
  const OUTLINE = tone("art-outline");

  const file = (paper = "star") => sprite("file", { p: tone(paper) });
  const arrow = () => draw(ARROW, { k: tone("star") });
  const ramaAt = (x, y) => place(x, y, 2, Dom.svg("g", { class: "art-bob" }, ramaParts()));
  const sky = (name, count) => stars(name, { count, width: 160, height: 71, twinkle: 0.3, tint: 0.25, dim: 0.6 });
  const rect = (x, y, width, height, fill, extra = {}) => Dom.svg("rect", { x, y, width, height, fill, ...extra });

  function text(x, y, words, { fill = tone("star"), size = 8, anchor = "middle", className = null, delay = null } = {}) {
    const classes = ["art-text", className].filter(Boolean).join(" ");
    return Dom.svg("text", { x, y, "text-anchor": anchor, "font-size": size, fill, class: classes, style: delay === null ? null : `animation-delay:${delay}s` }, words);
  }

  const timed = (className, delay, children) => Dom.svg("g", { class: className, style: `animation-delay:${delay}s` }, children);

  const ground = () => [
    rect(0, 74, 160, 16, tone("art-ground")),
    rect(0, 74, 160, 1, tone("art-ground-edge")),
    rect(18, 79, 10, 2, tone("art-ground-pit")),
    rect(20, 78, 6, 1, tone("art-ground-pit")),
    rect(118, 82, 14, 2, tone("art-ground-pit")),
    rect(121, 81, 8, 1, tone("art-ground-pit")),
  ];

  function planetAt(x, y, radius, palette) {
    const { rects, width, height } = planet(radius, palette);
    return place(x - Math.floor(width / 2), y - Math.floor(height / 2), 1, rects);
  }

  /* The top half of a small cyan planet, a dome standing on the ground. */
  function dome(x, y) {
    const { rects, width } = planet(9, { a: tone("art-cyan"), b: tone("art-cyan-dk"), c: tone("art-cyan-lt") });
    return [
      Dom.svg("svg", { x: x - 9, y: y - 10, width, height: 11, viewBox: `0 0 ${width} 11`, overflow: "hidden" }, rects),
      rect(x - 10, y, 21, 2, OUTLINE),
    ];
  }

  const ZONE_TONES = ["art-orange", "art-cyan", "art-violet", "art-pink"];
  const NIGHT_PLANET = { a: tone("art-ground-edge"), b: tone("art-ground"), c: tone("art-muted-dk") };
  const ALEX_CAPSULE = { v: tone("art-pink"), V: tone("art-pink-dk"), h: tone("art-pink-lt") };
  const CRACK = ["...c....", "...cc...", "....c...", "...cc...", "...c....", "....c...", "....cc..", "...c....", "...cc...", "....c..."];

  const capsuleAt = (x, y, scale = 2, recolour = {}) => place(x, y, scale, sprite("capsule", recolour));
  const boxLabel = (x, y, width, words, colour) => [rect(x, y, width, 11, tone("crt"), { stroke: tone(colour), "stroke-width": 1 }), text(x + width / 2, y + 8.5, words, { fill: tone(colour), size: 7.5 })];

  /* A branch label: a light tag with its name and a stem down to the capsule it points at. */
  const branchLabel = (x, y, width, words, colour = "star") => [
    rect(x + width / 2 - 1, y + 10, 2, 4, tone(colour)),
    rect(x, y, width, 10, tone(colour)),
    text(x + width / 2, y + 7.5, words, { fill: tone("crt"), size: 8 }),
  ];

  /* A 2-pixel line from one point to another, in steps, the link from a capsule to its parent. */
  function link(x0, y0, x1, y1, colour = "star") {
    const steps = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0));
    return Array.from({ length: steps + 1 }, (_, step) => rect(Math.round(x0 + ((x1 - x0) * step) / steps), Math.round(y0 + ((y1 - y0) * step) / steps), 2, 2, tone(colour)));
  }

  /* Children drawn where they end up, sliding in from (dx, dy) canvas pixels away. */
  const slide = (dx, dy, delay, children) => Dom.svg("g", { class: "art-slide", style: `--dx:${dx}px;--dy:${dy}px;animation-delay:${delay}s` }, children);

  const SCENES = {
    space: {
      label: "Rama hovers above a small base with a flag, a ringed planet in the sky",
      draw: () => [
        sky("space", 55),
        planetAt(132, 20, 9, { a: tone("art-pink"), b: tone("art-pink-dk"), c: tone("art-pink-lt"), n: tone("art-violet") }),
        ground(),
        dome(108, 74),
        rect(108, 54, 1, 10, tone("star")),
        place(109, 54, 1, sprite("flag"), { className: "art-wave" }),
        ramaAt(30, 34),
      ],
    },
    timeline: {
      label: "Four snapshots, v1 to v4, and an arrow back to the first: every commit is a snapshot",
      draw: () => [
        sky("timeline", 25),
        [0, 1, 2, 3].map((index) => {
          const left = 22 + index * 32;
          return timed("art-pop", index * 0.45, [
            rect(left, 38, 22, 26, tone("art-hull"), { stroke: OUTLINE, "stroke-width": 1 }),
            rect(left + 3, 41, 16, 13, tone(ZONE_TONES[index])),
            rect(left + 5, 49, 4, 3, OUTLINE),
            rect(left + 11, 46, 5, 6, OUTLINE, { opacity: 0.6 }),
            text(left + 11, 62, `v${index + 1}`, { fill: OUTLINE }),
          ]);
        }),
        timed("art-fade", 2.1, [
          rect(129, 24, 2, 12, tone("art-pink")),
          rect(33, 24, 98, 2, tone("art-pink")),
          rect(33, 24, 2, 10, tone("art-pink")),
          rect(30, 32, 8, 2, tone("art-pink")),
          rect(32, 34, 4, 2, tone("art-pink")),
        ]),
        text(82, 18, "back in time", { fill: tone("art-pink"), size: 9, className: "art-fade", delay: 2.4 }),
        text(80, 80, "every commit is a snapshot", { size: 9, className: "art-fade", delay: 1.6 }),
      ],
    },
    terminal: {
      label: "A terminal: ls lists the folder, then git status fails because the folder is not a Git repository",
      draw: () => [
        sky("terminal", 25),
        rect(8, 14, 112, 60, tone("crt"), { stroke: tone("star"), "stroke-width": 1 }),
        rect(9, 15, 110, 7, tone("crt-2")),
        rect(16, 17, 3, 3, tone("art-pink")),
        rect(21, 17, 3, 3, tone("art-yellow")),
        rect(26, 17, 3, 3, tone("art-cyan")),
        text(17, 32, "$ ls", { fill: tone("crt-cmd"), size: 9, anchor: "start", className: "art-fade", delay: 0.4 }),
        timed("art-fade", 1, [
          rect(17, 36, 22, 3, tone("crt-ink"), { opacity: 0.75 }),
          rect(45, 36, 28, 3, tone("crt-ink"), { opacity: 0.75 }),
          rect(79, 36, 16, 3, tone("crt-ink"), { opacity: 0.75 }),
        ]),
        text(17, 53, "$ git status", { fill: tone("crt-cmd"), size: 9, anchor: "start", className: "art-fade", delay: 1.8 }),
        text(17, 62, "fatal: not a git repository", { fill: tone("crt-err"), size: 7, anchor: "start", className: "art-fade", delay: 2.4 }),
        rect(17, 65, 4, 6, tone("crt-cmd"), { class: "art-alarm" }),
        ramaAt(128, 36),
      ],
    },
    planet: {
      label: "A plain folder on a planet, in a dashed outline: does Git know it?",
      draw: () => [
        sky("planet", 35),
        ground(),
        place(73, 54, 2, sprite("folder")),
        rect(62, 46, 50, 30, "none", { stroke: tone("art-muted"), "stroke-width": 1, "stroke-dasharray": "3 3" }),
        text(87, 22, "a plain folder", { size: 9 }),
        text(87, 38, "does Git know it?", { fill: tone("art-muted") }),
        ramaAt(14, 36),
      ],
    },
    flag: {
      label: "git init plants a flag beside the folder and creates .git",
      draw: () => [
        sky("flag", 35),
        ground(),
        place(56, 54, 2, sprite("folder")),
        timed("art-rise", 0.2, [rect(96, 40, 2, 34, tone("star")), place(98, 40, 2, sprite("flag"), { className: "art-wave" })]),
        text(108, 32, "git init", { fill: tone("art-yellow"), size: 10, className: "art-fade", delay: 0.9 }),
        timed("art-pop", 1.5, [rect(122, 56, 26, 14, tone("crt"), { stroke: tone("art-mint"), "stroke-width": 1 }), text(135, 66, ".git", { fill: tone("art-mint"), size: 10 })]),
        rect(122, 56, 26, 14, "none", { stroke: tone("art-mint"), "stroke-width": 1, class: "art-ring", style: "animation-delay:1.9s" }),
        ramaAt(10, 36),
      ],
    },
    zones: {
      label: "Three zones: the workshop where you edit, the cargo dock where you pick, the vault where you keep",
      draw: () => [
        sky("zones", 20),
        [
          ["workshop", "art-orange", "you edit", place(22, 30, 2, file())],
          ["cargo dock", "art-cyan", "you pick", place(70, 32, 2, sprite("crate"))],
          ["vault", "art-violet", "you keep", place(122, 32, 2, sprite("capsule"))],
        ].map(([name, colour, doing, cargo], index) => timed("art-pop", index * 0.5, [
          rect(12 + index * 52, 22, 36, 36, tone("void-2"), { stroke: tone(colour), "stroke-width": 2 }),
          cargo,
          text(30 + index * 52, 70, name, { fill: tone(colour), size: 9 }),
          text(30 + index * 52, 80, doing, { fill: tone("art-muted") }),
        ])),
        [0, 1].map((index) => place(50 + index * 52, 37, 1, arrow(), { className: "art-fade", delay: 0.4 + index * 0.5 })),
      ],
    },
    conveyor: {
      label: "git add picks what goes up: two files hop from the workshop belt to the cargo dock, a third is left behind",
      draw: () => [
        sky("conveyor", 20),
        rect(8, 58, 64, 5, tone("art-orange"), { stroke: OUTLINE, "stroke-width": 1 }),
        rect(12, 63, 3, 14, tone("art-muted-dk")),
        rect(64, 63, 3, 14, tone("art-muted-dk")),
        text(40, 86, "workshop", { fill: tone("art-orange"), size: 9 }),
        place(104, 46, 3, sprite("crate")),
        text(122, 86, "cargo dock", { fill: tone("art-cyan"), size: 9 }),
        Dom.svg("g", { class: "art-hop-a" }, place(14, 38, 2, file())),
        Dom.svg("g", { class: "art-hop-b" }, place(32, 38, 2, file())),
        Dom.svg("g", { class: "art-shake" }, place(50, 38, 2, file("art-red-lt"))),
        place(52, 26, 1, sprite("cross"), { className: "art-pop", delay: 2.2 }),
        text(80, 14, "git add picks what goes up", { size: 10 }),
      ],
    },
    capsule: {
      label: "git commit seals the cargo crate with its lid and drops it into the vault as capsule a1b2c3d",
      draw: () => [
        sky("capsule", 20),
        rect(44, 76, 72, 10, tone("art-violet-dk"), { stroke: OUTLINE, "stroke-width": 1 }),
        text(136, 84, "vault", { fill: tone("art-violet"), size: 9 }),
        Dom.svg("g", { class: "art-drop" }, [
          place(68, 34, 2, sprite("crate")),
          place(66, 28, 2, sprite("lid"), { className: "art-lid" }),
          timed("art-pop", 1.2, [rect(98, 36, 34, 11, tone("art-pink"), { stroke: OUTLINE, "stroke-width": 1 }), text(115, 44.5, "a1b2c3d", { fill: tone("crt") })]),
        ]),
        timed("art-fade", 1.3, boxLabel(6, 12, 84, '-m "first liftoff"', "star")),
        text(126, 30, "git commit", { fill: tone("art-yellow"), size: 10 }),
      ],
    },
    chain: {
      label: "Three capsules in a chain, each pointing to the one before, and HEAD on the newest",
      draw: () => [
        sky("chain", 20),
        [["a1b2c3d", "liftoff"], ["f00d42e", "Phobos stop"], ["9c0ffee", "logbook"]].map(([hash, message], index) => timed("art-pop", index * 0.55, [
          capsuleAt(14 + index * 50, 38),
          text(26 + index * 50, 62, hash),
          text(26 + index * 50, 70, message, { fill: tone("art-muted"), size: 7 }),
        ])),
        [0, 1].map((index) => Dom.svg("g", { class: "art-fade", style: `animation-delay:${0.9 + index * 0.55}s`, transform: `translate(${60 + index * 50} 45) scale(-1 1)` }, arrow())),
        timed("art-pop", 1.9, [rect(112, 18, 28, 11, tone("star")), text(126, 26.5, "HEAD", { fill: tone("crt"), size: 9 }), rect(125, 29, 2, 7, tone("star"))]),
        text(80, 84, "each capsule points to the one before", { size: 7, className: "art-fade", delay: 2.2 }),
      ],
    },
    orbit: {
      label: "Your base on a dark planet, and the mothership, origin, circling it in orbit",
      draw: () => [
        sky("orbit", 40),
        planetAt(80, 66, 14, NIGHT_PLANET),
        dome(80, 53),
        text(80, 88, "your base (local)"),
        Dom.svg("g", { class: "art-orbit" }, [place(69, 10, 1, sprite("ship")), text(80, 26, "origin", { fill: tone("art-pink") })]),
      ],
    },
    rocket: {
      label: "git remote add lights the base's antenna; git push launches a probe up to the mothership",
      draw: () => [
        sky("rocket", 40),
        planetAt(26, 76, 16, NIGHT_PLANET),
        rect(30, 46, 1, 14, tone("star")),
        rect(29, 44, 3, 3, tone("art-yellow")),
        [0, 0.7].map((delay) => rect(27, 42, 7, 7, "none", { stroke: tone("art-yellow"), "stroke-width": 1, class: "art-ring", style: `animation-delay:${delay}s` })),
        place(118, 10, 2, sprite("ship")),
        Dom.svg("g", { class: "art-push" }, place(34, 54, 2, sprite("probe"))),
        text(46, 38, "git remote add"),
        text(124, 40, "git push", { fill: tone("art-pink"), size: 11 }),
      ],
    },
    pull: {
      label: "git pull brings Alex's capsule down from the mothership to your base",
      draw: () => [
        sky("pull", 40),
        planetAt(26, 76, 16, NIGHT_PLANET),
        dome(26, 60),
        place(118, 10, 2, sprite("ship")),
        Dom.svg("g", { class: "art-pull" }, capsuleAt(128, 34, 2, ALEX_CAPSULE)),
        text(118, 46, "Alex's commit", { fill: tone("art-muted") }),
        text(70, 26, "git pull", { fill: tone("art-cyan"), size: 11 }),
      ],
    },
    alarm: {
      label: "Alert: a meteorite strikes base 7 while Rama watches, the sky flashing red",
      draw: () => [
        sky("alarm", 30),
        rect(0, 0, 160, 90, tone("art-red"), { opacity: 0.14, class: "art-alarm" }),
        ground(),
        Dom.svg("g", { class: "art-meteor" }, [
          place(130, 2, 2, sprite("meteor")),
          rect(144, 0, 8, 2, tone("art-orange"), { opacity: 0.7 }),
          rect(146, -2, 10, 2, tone("art-orange"), { opacity: 0.4 }),
        ]),
        rect(40, 58, 18, 18, tone("art-orange"), { stroke: tone("art-yellow"), "stroke-width": 2, class: "art-boom" }),
        text(49, 52, "base 7", { size: 9 }),
        ramaAt(104, 38),
        text(80, 16, "alert", { fill: tone("art-red"), size: 12, className: "art-alarm" }),
      ],
    },
    fork: {
      label: "git switch -c feature puts a second label on the newest capsule; a new capsule grows on a branch and the feature label moves to it, while main stays",
      draw: () => [
        sky("fork", 20),
        [10, 46, 82].map((x) => capsuleAt(x, 52)),
        rect(35, 59, 10, 2, tone("star")),
        rect(71, 59, 10, 2, tone("star")),
        timed("art-pop", 1.2, [link(104, 52, 124, 36, "art-yellow"), capsuleAt(124, 22)]),
        slide(-38, 22, 1.5, timed("art-pop", 0.4, branchLabel(114, 8, 36, "feature", "art-yellow"))),
        branchLabel(82, 38, 24, "main"),
        text(80, 84, "git switch -c feature", { fill: tone("art-yellow"), size: 9 }),
      ],
    },
    merge: {
      label: "Two chains of capsules join in one merge capsule that links to both parents",
      draw: () => [
        sky("merge", 20),
        [10, 46, 82].map((x) => capsuleAt(x, 58)),
        rect(35, 65, 10, 2, tone("star")),
        rect(71, 65, 10, 2, tone("star")),
        link(30, 57, 50, 30, "art-pink"),
        [46, 82].map((x) => capsuleAt(x, 14, 2, ALEX_CAPSULE)),
        rect(71, 21, 10, 2, tone("art-pink")),
        timed("art-pop", 0.8, capsuleAt(124, 36)),
        timed("art-fade", 1.3, link(123, 40, 107, 24, "art-pink")),
        timed("art-fade", 1.6, link(123, 48, 107, 64)),
        rect(122, 34, 28, 20, "none", { stroke: tone("art-mint"), "stroke-width": 1, class: "art-ring", style: "animation-delay:2s" }),
        timed("art-fade", 2, branchLabel(124, 56, 24, "main")),
        text(80, 86, "git merge", { fill: tone("art-yellow"), size: 9 }),
      ],
    },
    collision: {
      label: "Two capsules collide on the same file and the file cracks: a conflict",
      draw: () => [
        sky("collision", 20),
        Dom.svg("g", { class: "art-shake" }, [
          place(68, 26, 3, file()),
          place(68, 26, 3, draw(CRACK, { c: tone("art-red") }), { className: "art-fade", delay: 0.9 }),
        ]),
        slide(-24, 0, 0.2, capsuleAt(42, 34)),
        slide(24, 0, 0.2, capsuleAt(94, 34, 2, ALEX_CAPSULE)),
        [[64, 30], [92, 30], [65, 52], [91, 52]].map(([x, y], index) => rect(x, y, 3, 3, tone("art-yellow"), { class: "art-pop", style: `animation-delay:${0.8 + index * 0.1}s` })),
        text(80, 15, "CONFLICT", { fill: tone("art-red"), size: 11, className: "art-fade", delay: 0.9 }),
        text(80, 76, "same file, same lines", { fill: tone("art-muted") }),
      ],
    },
    blackbox: {
      label: "main moves back two capsules and the newer three vanish from the branch, but the black box, the reflog, still keeps them",
      draw: () => [
        sky("blackbox", 20),
        [66, 96, 126].map((x) => rect(x, 10, 24, 16, "none", { stroke: tone("art-muted"), "stroke-width": 1, "stroke-dasharray": "2 2" })),
        [6, 36].map((x) => capsuleAt(x, 10)),
        rect(30, 17, 6, 2, tone("star")),
        timed("art-vanish", 1.4, [[66, 96, 126].map((x) => capsuleAt(x, 10)), [60, 90, 120].map((x) => rect(x, 17, 6, 2, tone("star")))]),
        slide(90, 0, 0.6, branchLabel(36, 30, 24, "main")),
        rect(44, 50, 72, 32, tone("art-orange"), { stroke: OUTLINE, "stroke-width": 1 }),
        rect(45, 51, 70, 3, tone("art-orange-dk")),
        rect(70, 46, 20, 2, OUTLINE),
        rect(70, 46, 2, 5, OUTLINE),
        rect(88, 46, 2, 5, OUTLINE),
        text(80, 63, "reflog", { fill: tone("crt"), size: 9 }),
        [58, 74, 90].map((x, index) => timed("art-pop", 1.8 + index * 0.2, capsuleAt(x, 68, 1))),
      ],
    },
  };

  const NAMES = Object.freeze(Object.keys(SCENES));

  function scene(name, { label = "" } = {}) {
    if (!(name in SCENES)) throw new RangeError(`unknown scene: ${name}`);
    const { label: description, draw: parts } = SCENES[name];
    const backdrop = rect(0, 0, 160, 90, tone("void"));
    return picture({ class: "art-scene", viewBox: "0 0 160 90", "data-scene": name }, label || description, [backdrop, parts()]);
  }

  return { NAMES, scene };
})();
