"use strict";

/*
 * The page's space backgrounds and the celebration burst. Defines one global, ArtSky; dom.js and
 * art-pixels.js load first, art-style.css styles and animates them. All three are decorative
 * (aria-hidden) and drawn the same way every time for the same seed (a number or text).
 *
 * field(seed)   the stars of a sector's dark strip: an <svg> with a 200x60 viewBox that fills
 *               its box (preserveAspectRatio slice); some stars twinkle.
 * dust(seed)    the page's background specks in --speck, some twinkling: a fixed, full-window
 *               <svg> behind everything (z-index 0, no pointer events).
 * sparks(seed)  32 coloured squares flying out from the centre of the box it is put in, once,
 *               as the design's celebration does: a <div> that fills its positioned parent and
 *               plays itself (about 1.6 s). Under reduced motion it shows nothing.
 */

/* global Dom, ArtPixels */
/* exported ArtSky */

const ArtSky = (function () {
  const { tone, picture, random, stars } = ArtPixels;

  function field(seed) {
    const attributes = { class: "art-field", viewBox: "0 0 200 60", preserveAspectRatio: "xMidYMid slice" };
    return picture(attributes, "", stars(seed, { count: 46, width: 200, height: 60, twinkle: 0.2, tint: 0.2, dim: 0.55 }));
  }

  function dust(seed) {
    const next = random(seed);
    const specks = Array.from({ length: 70 }, () => {
      const size = next() < 0.15 ? 3 : 2;
      const twinkles = next() < 0.25;
      const x = (next() * 100).toFixed(2);
      const y = (next() * 100).toFixed(2);
      const delay = (next() * 2.4).toFixed(2);
      return Dom.svg("rect", { x: `${x}%`, y: `${y}%`, width: size, height: size, fill: tone("speck"), opacity: 0.55, class: twinkles && "art-tw", style: twinkles && `animation-delay:${delay}s` });
    });
    return picture({ class: "art-dust", width: "100%", height: "100%" }, "", specks);
  }

  const SPARK_TONES = ["art-yellow", "art-cyan", "art-pink", "art-violet", "star"];
  const SPARK_SIZES = [6, 8, 12];

  /* Each spark flies along a random angle to 140px plus a random share of 55vmax, as the design's
     celebrate() does with the window's size; CSS works the distance out from --dx, --dy, --far. */
  function sparks(seed = 1) {
    const next = random(seed);
    const pieces = Array.from({ length: 32 }, (_, index) => {
      const angle = next() * Math.PI * 2;
      const far = next().toFixed(3);
      const delay = (0.2 + next() * 0.3).toFixed(2);
      const style = [
        `--size:${SPARK_SIZES[index % 3]}px`,
        `--dx:${Math.cos(angle).toFixed(3)}`,
        `--dy:${Math.sin(angle).toFixed(3)}`,
        `--far:${far}`,
        `background:${tone(SPARK_TONES[index % 5])}`,
        `animation-delay:${delay}s`,
      ].join(";");
      return Dom.el("i", { class: "art-spark", style });
    });
    return Dom.el("div", { class: "art-sparks", "aria-hidden": "true" }, pieces);
  }

  return { field, dust, sparks };
})();
