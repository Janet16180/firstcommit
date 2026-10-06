"use strict";

/*
 * The page's addresses, in the fragment: #/ (the map), #/level/<id>, #/cards[/<chapter>] and
 * #/notes[/<chapter>]. The link the server prints carries the access key in the fragment too
 * (#token=...), which client.js removes; anything from "&" on is not part of the address.
 * Defines one global, Route.
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

  function parse(hash) {
    const address = hash.replace(/^#/, "").split("&")[0];
    const [, view, rawName = ""] = address.split("/");
    const name = rawName ? decode(rawName) : null;
    const malformed = rawName !== "" && name === null;
    let route = HOME;
    if (view === "level" && name) route = { view, id: name };
    else if ((view === "cards" || view === "notes") && !malformed) route = { view, chapter: name };
    return route;
  }

  return { parse };
})();
