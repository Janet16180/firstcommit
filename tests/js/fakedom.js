"use strict";

/*
 * A small stand-in for the browser DOM, enough for the page scripts under node: elements with
 * attributes, classes, dataset, style, children, events, focus and simple selectors (tag, #id,
 * .class, [attr], [attr="value"], compound, and descendant combinations). `html(node)` writes
 * a node out as markup, so a test can compare what a script built.
 */

const SVG_NS = "http://www.w3.org/2000/svg";

class FakeNode {
  constructor(document) {
    this.ownerDocument = document;
    this.parentNode = null;
    this.childNodes = [];
  }

  get parentElement() {
    return this.parentNode && this.parentNode.nodeType === 1 ? this.parentNode : null;
  }

  get firstChild() {
    return this.childNodes[0] || null;
  }

  get textContent() {
    return this.childNodes.map((child) => child.textContent).join("");
  }

  set textContent(value) {
    this.replaceChildren();
    if (value !== "") this.append(String(value));
  }

  adopt(item) {
    const node = typeof item === "string" ? this.ownerDocument.createTextNode(item) : item;
    if (node.nodeType === 11) return [...node.childNodes].flatMap((child) => this.adopt(child));
    if (node.parentNode) node.remove();
    node.parentNode = this;
    return [node];
  }

  append(...items) {
    for (const item of items) this.childNodes.push(...this.adopt(item));
  }

  appendChild(node) {
    this.append(node);
    return node;
  }

  prepend(...items) {
    this.childNodes.unshift(...items.flatMap((item) => this.adopt(item)));
  }

  insertBefore(node, before) {
    const adopted = this.adopt(node);
    const at = before ? this.childNodes.indexOf(before) : -1;
    this.childNodes.splice(at < 0 ? this.childNodes.length : at, 0, ...adopted);
    return node;
  }

  replaceChildren(...items) {
    for (const child of this.childNodes) child.parentNode = null;
    this.childNodes = [];
    this.append(...items);
  }

  replaceWith(...items) {
    const parent = this.parentNode;
    if (!parent) return;
    const at = parent.childNodes.indexOf(this);
    this.remove();
    parent.childNodes.splice(at, 0, ...items.flatMap((item) => parent.adopt(item)));
  }

  remove() {
    if (!this.parentNode) return;
    const siblings = this.parentNode.childNodes;
    siblings.splice(siblings.indexOf(this), 1);
    this.parentNode = null;
  }

  contains(node) {
    for (let at = node; at; at = at.parentNode) if (at === this) return true;
    return false;
  }
}

class FakeText extends FakeNode {
  constructor(document, text) {
    super(document);
    this.nodeType = 3;
    this.data = text;
  }

  get textContent() {
    return this.data;
  }

  set textContent(value) {
    this.data = String(value);
  }
}

class FakeFragment extends FakeNode {
  constructor(document) {
    super(document);
    this.nodeType = 11;
  }
}

function parseSelector(text) {
  return text.trim().split(/\s+/).map((part) => {
    const tag = (part.match(/^[a-zA-Z][\w-]*/) || [""])[0].toLowerCase();
    const id = (part.match(/#([\w-]+)/) || [null, null])[1];
    const classes = [...part.matchAll(/\.([\w-]+)/g)].map((match) => match[1]);
    const attributes = [...part.matchAll(/\[([\w-]+)(?:="([^"]*)")?\]/g)].map((match) => ({ name: match[1], value: match[2] }));
    return { tag, id, classes, attributes };
  });
}

function matchesPart(element, part) {
  return (!part.tag || element.localName === part.tag)
    && (!part.id || element.getAttribute("id") === part.id)
    && part.classes.every((name) => element.classList.contains(name))
    && part.attributes.every(({ name, value }) => element.hasAttribute(name) && (value === undefined || element.getAttribute(name) === value));
}

function matches(element, parts) {
  if (!matchesPart(element, parts[parts.length - 1])) return false;
  let rest = parts.length - 2;
  for (let at = element.parentElement; at && rest >= 0; at = at.parentElement) {
    if (matchesPart(at, parts[rest])) rest -= 1;
  }
  return rest < 0;
}

class FakeElement extends FakeNode {
  constructor(document, tag, namespace) {
    super(document);
    this.nodeType = 1;
    this.namespaceURI = namespace;
    this.localName = namespace === SVG_NS ? tag : tag.toLowerCase();
    this.attributes = new Map();
    this.listeners = new Map();
    this.style = {
      setProperty(key, value) {
        this[key] = value;
      },
      removeProperty(key) {
        delete this[key];
      },
    };
    const element = this;
    this.classList = {
      list: () => (element.getAttribute("class") || "").split(/\s+/).filter(Boolean),
      contains: (name) => element.classList.list().includes(name),
      add: (...names) => element.setAttribute("class", [...new Set([...element.classList.list(), ...names])].join(" ")),
      remove: (...names) => element.setAttribute("class", element.classList.list().filter((name) => !names.includes(name)).join(" ")),
      toggle: (name, force) => {
        const on = force === undefined ? !element.classList.contains(name) : Boolean(force);
        if (on) element.classList.add(name);
        else element.classList.remove(name);
        return on;
      },
    };
    this.dataset = new Proxy({}, {
      get: (target, key) => element.getAttribute(`data-${String(key).replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`)}`) ?? undefined,
      set: (target, key, value) => {
        element.setAttribute(`data-${String(key).replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`)}`, value);
        return true;
      },
      deleteProperty: (target, key) => {
        element.removeAttribute(`data-${String(key).replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`)}`);
        return true;
      },
    });
    this.valueProperty = null;
  }

  get tagName() {
    return this.namespaceURI === SVG_NS ? this.localName : this.localName.toUpperCase();
  }

  get children() {
    return this.childNodes.filter((child) => child.nodeType === 1);
  }

  get className() {
    return this.getAttribute("class") || "";
  }

  set className(value) {
    this.setAttribute("class", value);
  }

  get id() {
    return this.getAttribute("id") || "";
  }

  set id(value) {
    this.setAttribute("id", value);
  }

  get value() {
    return this.valueProperty ?? this.getAttribute("value") ?? "";
  }

  set value(text) {
    this.valueProperty = String(text);
  }

  get disabled() {
    return this.hasAttribute("disabled");
  }

  set disabled(on) {
    this.toggleAttribute("disabled", on);
  }

  get hidden() {
    return this.hasAttribute("hidden");
  }

  set hidden(on) {
    this.toggleAttribute("hidden", on);
  }

  get checked() {
    return this.hasAttribute("checked");
  }

  set checked(on) {
    this.toggleAttribute("checked", on);
  }

  setAttribute(name, value) {
    this.attributes.set(name, String(value));
  }

  getAttribute(name) {
    return this.attributes.has(name) ? this.attributes.get(name) : null;
  }

  hasAttribute(name) {
    return this.attributes.has(name);
  }

  removeAttribute(name) {
    this.attributes.delete(name);
  }

  toggleAttribute(name, force) {
    const on = force === undefined ? !this.hasAttribute(name) : Boolean(force);
    if (on) this.setAttribute(name, "");
    else this.removeAttribute(name);
    return on;
  }

  addEventListener(type, listener) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(listener);
  }

  removeEventListener(type, listener) {
    const list = this.listeners.get(type) || [];
    if (list.includes(listener)) list.splice(list.indexOf(listener), 1);
  }

  dispatchEvent(event) {
    event.target = event.target || this;
    for (let at = this; at && !event.stopped; at = at.parentNode) {
      event.currentTarget = at;
      for (const listener of [...(at.listeners ? at.listeners.get(event.type) || [] : [])]) listener(event);
    }
    return !event.defaultPrevented;
  }

  click() {
    if (!this.disabled) this.dispatchEvent(makeEvent("click"));
  }

  focus() {
    this.ownerDocument.activeElement = this;
  }

  blur() {
    if (this.ownerDocument.activeElement === this) this.ownerDocument.activeElement = this.ownerDocument.body;
  }

  closest(selector) {
    const parts = parseSelector(selector);
    for (let at = this; at && at.nodeType === 1; at = at.parentNode) if (matches(at, parts)) return at;
    return null;
  }

  querySelectorAll(selector) {
    const parts = parseSelector(selector);
    const found = [];
    const walk = (node) => {
      for (const child of node.children) {
        if (matches(child, parts)) found.push(child);
        walk(child);
      }
    };
    walk(this);
    return found;
  }

  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }

  get open() {
    return this.hasAttribute("open");
  }

  showModal() {
    this.setAttribute("open", "");
  }

  close(returnValue = "") {
    this.returnValue = returnValue;
    this.removeAttribute("open");
    this.dispatchEvent(makeEvent("close"));
  }

  getBoundingClientRect() {
    return { x: 0, y: 0, top: 0, left: 0, width: 0, height: 0, right: 0, bottom: 0 };
  }
}

function makeEvent(type, fields = {}) {
  return {
    type,
    target: null,
    currentTarget: null,
    defaultPrevented: false,
    stopped: false,
    preventDefault() {
      this.defaultPrevented = true;
    },
    stopPropagation() {
      this.stopped = true;
    },
    ...fields,
  };
}

function createDocument() {
  const document = {
    listeners: new Map(),
    hidden: false,
    createElement: (name) => new FakeElement(document, name, "http://www.w3.org/1999/xhtml"),
    createElementNS: (namespace, name) => new FakeElement(document, name, namespace),
    createTextNode: (text) => new FakeText(document, String(text)),
    createDocumentFragment: () => new FakeFragment(document),
    addEventListener(type, listener) {
      if (!this.listeners.has(type)) this.listeners.set(type, []);
      this.listeners.get(type).push(listener);
    },
    removeEventListener(type, listener) {
      const list = this.listeners.get(type) || [];
      if (list.includes(listener)) list.splice(list.indexOf(listener), 1);
    },
    dispatchEvent(event) {
      for (const listener of [...(this.listeners.get(event.type) || [])]) listener(event);
      return !event.defaultPrevented;
    },
    getElementById: (id) => document.body.querySelector(`#${id}`),
    querySelector: (selector) => document.body.querySelector(selector),
    querySelectorAll: (selector) => document.body.querySelectorAll(selector),
  };
  document.documentElement = document.createElement("html");
  document.body = document.createElement("body");
  document.documentElement.append(document.body);
  document.activeElement = document.body;
  return document;
}

function escapeText(text) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/* The node as markup: attributes in the order they were set, text escaped. */
function html(node) {
  if (node.nodeType === 3) return escapeText(node.data);
  const inner = node.childNodes.map(html).join("");
  if (node.nodeType === 11) return inner;
  const attributes = [...node.attributes].map(([name, value]) => (value === "" ? ` ${name}` : ` ${name}="${escapeText(value).replace(/"/g, "&quot;")}"`)).join("");
  return `<${node.localName}${attributes}>${inner}</${node.localName}>`;
}

module.exports = { createDocument, html, makeEvent, SVG_NS };
