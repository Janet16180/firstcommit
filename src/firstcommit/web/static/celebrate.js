"use strict";

/*
 * The moment a level is solved: a calm card with the XP paid and any new rank, the XP counting
 * up, and a few seconds of soft confetti (none, and no counting, under prefers-reduced-motion).
 * It is a modal <dialog>: focus starts on its title and reaches its button a moment later, so
 * an Enter the player was typing in the terminal cannot dismiss it unseen; Escape continues
 * too. Needs dom.js.
 * Defines one global, Celebrate.
 */

/* global Dom */
/* exported Celebrate */

const Celebrate = (function () {
  const { el, svg } = Dom;
  const CONFETTI_MS = 4500;
  const COUNT_MS = 1200;
  const FOCUS_DELAY_MS = 900;
  const COLORS = ["--map-lane-0", "--map-lane-1", "--map-lane-2", "--map-lane-3", "--map-head"];

  const calm = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function countUp(node, target) {
    const start = performance.now();
    const frame = (now) => {
      const k = Math.min((now - start) / COUNT_MS, 1);
      node.textContent = `+${Math.round(target * (1 - Math.pow(1 - k, 3)))}`;
      if (k < 1) requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
  }

  /* Paper-like pieces drifting down from the top of the screen. */
  function confetti(canvas) {
    const width = window.innerWidth;
    const height = window.innerHeight;
    const ratio = window.devicePixelRatio || 1;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    const ctx = canvas.getContext("2d");
    ctx.scale(ratio, ratio);
    const style = getComputedStyle(document.documentElement);
    const colors = COLORS.map((name) => style.getPropertyValue(name).trim() || "#888");
    const pieces = Array.from({ length: 90 }, (_, index) => ({
      x: Math.random() * width,
      y: Math.random() * height * 0.35 - height * 0.15,
      vx: (Math.random() - 0.5) * 1.2,
      vy: 1.2 + Math.random() * 1.8,
      spin: Math.random() * Math.PI,
      size: 5 + Math.random() * 6,
      color: colors[index % colors.length],
    }));
    const started = performance.now();
    const frame = (now) => {
      ctx.clearRect(0, 0, width, height);
      const fade = Math.max(0, 1 - (now - started) / CONFETTI_MS);
      for (const piece of pieces) {
        piece.x += piece.vx + Math.sin((now - started) / 500 + piece.spin);
        piece.y += piece.vy;
        piece.spin += 0.05;
        ctx.globalAlpha = fade;
        ctx.fillStyle = piece.color;
        ctx.fillRect(piece.x, piece.y, piece.size, piece.size * Math.abs(Math.cos(piece.spin)));
      }
      if (fade > 0) requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
  }

  const emblem = () => svg("svg", { class: "celebration-emblem", viewBox: "-40 -40 80 80", "aria-hidden": "true" },
    svg("circle", { r: 34, class: "emblem-ring" }),
    svg("path", { d: "M-15 1 L-4 12 L17 -11", class: "emblem-check" }),
  );

  /* Shows the card; resolves when the player continues. `xp` is what the server paid. */
  function show({ kicker, title, subtitle = "", xp, firstTime, rankBefore, rankAfter, button, timers = window }) {
    return new Promise((resolve) => {
      const reduced = calm();
      const value = el("span", { class: "celebration-xp-value" }, reduced ? `+${xp}` : "+0");
      const continueButton = el("button", { type: "button", class: "btn btn-primary btn-large", onclick: () => dialog.close() }, button);
      const canvas = el("canvas", { class: "celebration-sparks", "aria-hidden": "true" });
      const dialog = el("dialog", { class: "celebration", "aria-labelledby": "celebration-title" },
        canvas,
        el("div", { class: "celebration-card" },
          emblem(),
          el("p", { class: "kicker" }, kicker),
          el("h2", { id: "celebration-title", tabindex: "-1", autofocus: true }, title),
          subtitle && el("p", { class: "celebration-sub" }, subtitle),
          el("p", { class: "celebration-xp" }, value, " XP"),
          !firstTime && el("p", { class: "celebration-replay muted" }, "Played again"),
          el("p", { class: "celebration-rank", hidden: rankBefore === rankAfter }, "New rank: ", el("strong", {}, rankAfter)),
          continueButton,
        ),
      );
      dialog.addEventListener("close", () => {
        dialog.remove();
        resolve();
      });
      document.body.append(dialog);
      dialog.showModal();
      dialog.querySelector("h2").focus();
      timers.setTimeout(() => dialog.open && continueButton.focus(), FOCUS_DELAY_MS);
      if (reduced) return;
      countUp(value, xp);
      confetti(canvas);
    });
  }

  return { show, FOCUS_DELAY_MS };
})();
