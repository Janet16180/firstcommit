"use strict";

/*
 * The station strip (V2 in docs/drafts/chapters-5-9.md): a station folded into one row of cards,
 * so another view can take the stage. Each card is a zone the player knows: up to three files,
 * or three capsules, then "+N"; an edited or new file is tagged "on no branch" (uncommitted
 * work belongs to no branch yet), a conflicted one "conflict"; every card badges its count. Each
 * strip is named for whose station it is, with that station's icon. It hides on purpose what the
 * stage shows: hashes, branch names, file contents and older capsules. A tapped card asks to be
 * expanded back into its zone. Alex's strip is the crew band (V3 band), a thin row with their
 * station's three cards. It reads a station as zones.js reads it. Needs dom.js, strings.js and
 * art-sprites.js. Defines one global, Strip.
 *
 * create({onExpand, who}) {element, update(reading)}: the strip of `who` ("you", the default, or
 *                    "alex"), redrawn from a Zones.read reading (Alex's: its `crew`); onExpand(zone)
 *                    is called with the tapped card's zone.
 */

/* global Dom, Strings, ArtSprites */
/* exported Strip */

const Strip = (function () {
  const { el } = Dom;
  const { t } = Strings;
  const SHOWN = 3;
  /* The file states the strip tags, and what each tag says. */
  const TAGS = { conflicted: "zones.tag.conflicted", edited: "strip.noBranch", new: "strip.noBranch" };

  /* The first few items, and the rest folded into a count. */
  const fold = (items, draw) => [items.slice(0, SHOWN).map(draw), items.length > SHOWN && el("span", { class: "strip-more" }, `+${items.length - SHOWN}`)];

  const fileChip = (item) => el("span", { class: "strip-file" }, item.path, TAGS[item.state] && el("span", { class: "strip-tag", "data-state": item.state }, t(TAGS[item.state])));

  /* A capsule as its block alone, in its author's colour. */
  const capsuleBlock = (commit) => el("span", { class: "strip-capsule", "data-author": commit.author.split(" ")[0].toLowerCase(), "aria-hidden": "true" });

  function card(zone, items, draw, onExpand) {
    const off = items === null;
    return el("button", { type: "button", class: off ? "strip-card is-off" : "strip-card", "data-zone": zone, onclick: () => onExpand(zone) },
      el("span", { class: "strip-name" }, t(`zones.${zone}`)),
      el("span", { class: "strip-count" }, off ? "–" : String(items.length)),
      el("span", { class: "strip-items" }, off ? [] : fold(items, draw)));
  }

  function create({ onExpand, who = "you" }) {
    const band = who === "alex";
    const element = el("div", { class: band ? "strip is-band" : "strip", role: "group", "aria-label": t(band ? "strip.crewLabel" : "strip.label") });
    return {
      element,

      update(reading) {
        const cards = [
          el("span", { class: "strip-who" }, ArtSprites.icon(`station-${who}`), t(`zones.station.${who}`)),
          card("workshop", reading.workshop, fileChip, onExpand),
          card("dock", reading.dock, fileChip, onExpand),
          card("vault", reading.vault, capsuleBlock, onExpand),
          reading.remote && card("remote", reading.remote, capsuleBlock, onExpand),
        ];
        element.replaceChildren(...cards.filter(Boolean));
      },
    };
  }

  return { create };
})();
