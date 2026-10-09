"use strict";

/*
 * The page's addresses, in the fragment: #/ (the map), #/level/<id>, #/guide (the field guide),
 * #/cards[/<chapter>], #/notes[/<chapter>], #/dev (dev mode's level list) and
 * #/playground[?start=<id>&view=<view>&try=<line>] (free play: a start, the view it opens on and a
 * line offered at the prompt, each optional and URL-encoded). The link the server prints carries
 * the access key in the fragment too (#token=... or &token=...), which client.js removes; it is
 * never part of the address, and outside the playground's query nothing from "&" on is.
 * Defines one global, Route.
 *
 * parse(hash)    the route: {view, ...} with the view's own fields; the map for anything unknown.
 * address(hash)  the hash without its access key.
 */

/* exported Route */

const Route = (function () {
  const HOME = { view: "home" };

  function decode(part) {
    try {
      return decodeURIComponent(part);
    } catch (error) {
      return null; /* A malformed escape: the address names nothing. */
    }
  }

  const address = (hash) => hash.replace(/&token=[^&]*/, "").replace(/^#token=[^&]*/, "#");

  /* The playground's query: each of start, view and try, null when absent or broken. */
  function playground(query) {
    const pairs = new Map(query.split("&").map((pair) => pair.split("=")).map(([name, value = ""]) => [name, decode(value)]));
    const field = (name) => pairs.get(name) || null;
    return { view: "playground", start: field("start"), picture: field("view"), tryLine: field("try") };
  }

  function parse(hash) {
    const [path, query = ""] = address(hash).replace(/^#/, "").split("?");
    if (path === "/playground") return playground(query);
    const [, view, rawName = ""] = path.split("&")[0].split("/");
    const name = rawName ? decode(rawName) : null;
    const malformed = rawName !== "" && name === null;
    let route = HOME;
    if (view === "level" && name) route = { view, id: name };
    else if (view === "guide" || view === "dev") route = { view };
    else if ((view === "cards" || view === "notes") && !malformed) route = { view, chapter: name };
    return route;
  }

  return { parse, address };
})();
