"use strict";

/*
 * Building the page's elements. Defines one global, Dom; every other page script of the game
 * uses it, so it loads first.
 *
 * el(tag, attributes, ...children) and svg(tag, attributes, ...children) make an HTML or SVG
 * element. Attributes: `on<event>` functions become listeners; true becomes an empty attribute
 * (`disabled`); false, null and undefined are left out; anything else is set as text. Children
 * are nodes or text (never parsed as HTML); null, undefined and false are skipped and lists are
 * flattened, so `cond && node` and `items.map(...)` can be passed as they are.
 */

/* exported Dom */

const Dom = (() => {
  const SVG_NS = "http://www.w3.org/2000/svg";
  const absent = (value) => value === null || value === undefined || value === false;

  function setAttribute(node, name, value) {
    if (name.startsWith("on") && typeof value === "function") node.addEventListener(name.slice(2), value);
    else if (value === true) node.setAttribute(name, "");
    else if (!absent(value)) node.setAttribute(name, String(value));
  }

  function fill(node, attributes, children) {
    for (const [name, value] of Object.entries(attributes)) setAttribute(node, name, value);
    for (const child of children.flat(Infinity)) {
      if (!absent(child)) node.append(typeof child === "object" ? child : String(child));
    }
    return node;
  }

  const el = (tag, attributes = {}, ...children) => fill(document.createElement(tag), attributes, children);
  const svg = (tag, attributes = {}, ...children) => fill(document.createElementNS(SVG_NS, tag), attributes, children);
  const clear = (node) => node.replaceChildren();

  return { el, svg, clear };
})();
