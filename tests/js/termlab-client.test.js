"use strict";

/* client.js runs in a VM context whose browser globals (location, history, localStorage,
   fetch, Request) are stand-ins that record what the client does with them. */

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const SOURCE = fs.readFileSync(path.join(__dirname, "..", "..", "src", "firstcommit", "termlab", "web", "static", "client.js"), "utf8");
const OPTIONS = { header: "X-Testgame-Token", storageKey: "testgame.token", command: "testgame serve" };

/* Objects made inside the VM context have its own prototypes; compare their JSON instead. */
const asJson = (value) => JSON.parse(JSON.stringify(value));

function reply(status, body, statusText = "") {
  return new Response(typeof body === "string" ? body : JSON.stringify(body), { status, statusText });
}

/* A page at http://localhost:8800/<search><hash> with the given storage and server. */
function page({ hash = "", search = "", stored = {}, server = () => reply(200, {}), blockedStorage = false } = {}) {
  const storage = new Map(Object.entries(stored));
  const seen = { addresses: [], requests: [], locked: 0 };
  const localStorage = {
    getItem(key) {
      if (blockedStorage) throw new Error("SecurityError");
      return storage.has(key) ? storage.get(key) : null;
    },
    setItem(key, value) {
      if (blockedStorage) throw new Error("SecurityError");
      storage.set(key, String(value));
    },
    removeItem(key) {
      if (blockedStorage) throw new Error("SecurityError");
      storage.delete(key);
    },
  };
  class Request {
    constructor(url, options) {
      Object.assign(this, options, { url });
    }
  }
  const context = vm.createContext({
    location: { hash, search, pathname: "/" },
    history: { replaceState: (state, title, address) => seen.addresses.push(address) },
    localStorage,
    Request,
    AbortSignal,
    fetch: async (request) => {
      seen.requests.push(request);
      return server(request);
    },
  });
  vm.runInContext(SOURCE, context);
  const client = context.createClient({ ...OPTIONS, onLocked: () => (seen.locked += 1) });
  return { client, storage, seen };
}

test("the key from the link is kept and removed from the address bar", () => {
  const { client, storage, seen } = page({ hash: "#token=abc-DEF_1", search: "?x=1" });
  assert.equal(client.token(), "abc-DEF_1");
  assert.equal(storage.get("testgame.token"), '"abc-DEF_1"');
  assert.deepEqual(seen.addresses, ["/?x=1"]);
});

test("without a link the kept key is used, and without either there is none", () => {
  assert.equal(page({ stored: { "testgame.token": '"kept"' } }).client.token(), "kept");
  const fresh = page();
  assert.equal(fresh.client.token(), null);
  assert.deepEqual(fresh.seen.addresses, []);
});

test("a key in the link replaces the kept one", () => {
  const { client, storage } = page({ hash: "#a=1&token=new%2Fkey", stored: { "testgame.token": '"old"' } });
  assert.equal(client.token(), "new/key");
  assert.equal(storage.get("testgame.token"), '"new/key"');
});

test("blocked storage still lets the key from the link work", async () => {
  const { client, seen } = page({ hash: "#token=abc", blockedStorage: true });
  assert.equal(client.token(), "abc");
  await client.api("/api/status");
  assert.equal(seen.requests[0].headers["X-Testgame-Token"], "abc");
  assert.equal(page({ blockedStorage: true }).client.token(), null);
});

test("every request carries the key, and a body makes it a JSON POST", async () => {
  const { client, seen } = page({ hash: "#token=abc", server: () => reply(200, { ok: true }) });
  assert.deepEqual(await client.api("/api/status"), { ok: true });
  assert.deepEqual(await client.api("/api/check", { answer: "42" }), { ok: true });
  const [get, post] = seen.requests;
  assert.equal(get.url, "/api/status");
  assert.equal(get.method, undefined);
  assert.deepEqual(asJson(get.headers), { "X-Testgame-Token": "abc" });
  assert.equal(post.method, "POST");
  assert.deepEqual(asJson(post.headers), { "X-Testgame-Token": "abc", "Content-Type": "application/json" });
  assert.equal(post.body, '{"answer":"42"}');
});

test("a refused key is forgotten, the page is told once, and the error says 403", async () => {
  const { client, storage, seen } = page({ hash: "#token=stale", server: () => reply(403, "Open the link") });
  await assert.rejects(client.api("/api/status"), (error) => error.status === 403 && error.message === "no access key");
  assert.equal(client.token(), null);
  assert.equal(storage.has("testgame.token"), false);
  assert.equal(seen.locked, 1);
  await assert.rejects(client.api("/api/status"), (error) => error.status === 403);
  assert.equal(seen.requests[1].headers["X-Testgame-Token"], "");
});

test("a server that does not answer gives status 0 and names the command", async () => {
  const { client, seen } = page({ hash: "#token=abc", server: () => Promise.reject(new TypeError("Failed to fetch")) });
  await assert.rejects(client.api("/api/status"), (error) => {
    assert.equal(error.status, 0);
    assert.equal(error.message, "the game server did not answer. Is `testgame serve` still running?");
    return true;
  });
  assert.equal(seen.locked, 0);
});

test("a request gives up after its timeout with status 0", async () => {
  /* The server never answers; only the request's own signal can end the wait. */
  const hang = (request) => new Promise((resolve, reject) => {
    if (request.signal) request.signal.addEventListener("abort", () => reject(request.signal.reason));
  });
  const { client } = page({ hash: "#token=abc", server: hang });
  const outcome = client.api("/api/start", { mission: "x" }, 50).then(() => "answered", (error) => error.status);
  const deadline = new Promise((resolve) => setTimeout(() => resolve("still waiting"), 2000));
  assert.equal(await Promise.race([outcome, deadline]), 0);
});

test("a reply whose body does not arrive in time, or is cut off, gives status 0 like a server that does not answer", async () => {
  /* What Chrome rejects with when the request's own timeout fires between the headers and the
     body, and when the connection drops while the body comes. */
  const failures = [() => new DOMException("The user aborted a request.", "AbortError"), () => new TypeError("network error")];
  for (const failure of failures) {
    const late = { ok: true, status: 200, json: () => Promise.reject(failure()) };
    const { client } = page({ hash: "#token=abc", server: () => late });
    await assert.rejects(client.api("/api/observe"), (error) => {
      assert.equal(error.status, 0);
      assert.equal(error.message, "the game server did not answer. Is `testgame serve` still running?");
      return true;
    });
  }
});

test("an error reply carries its status and the server's error text when there is one", async () => {
  const conflict = page({ hash: "#token=abc", server: () => reply(409, { error: "no mission in progress" }) });
  await assert.rejects(conflict.client.api("/api/check", {}), (error) => error.status === 409 && error.message === "no mission in progress");
  const plain = page({ hash: "#token=abc", server: () => reply(404, "not found", "Not Found") });
  await assert.rejects(plain.client.api("/api/nope"), (error) => error.status === 404 && error.message === "404 Not Found");
  assert.equal(plain.client.token(), "abc");
});

test("an error reply also carries the server's whole reply, so a game can read its own fields", async () => {
  const save = page({ hash: "#token=abc", server: () => reply(500, { error: "progress.json is damaged", kind: "save" }) });
  await assert.rejects(save.client.api("/api/status"), (error) => error.status === 500 && error.data.kind === "save");
  const plain = page({ hash: "#token=abc", server: () => reply(502, "bad gateway", "Bad Gateway") });
  await assert.rejects(plain.client.api("/api/status"), (error) => error.status === 502 && Object.keys(error.data).length === 0);
});

test("a 2xx reply that is not JSON throws the browser's own error, without a status", async () => {
  const { client } = page({ hash: "#token=abc", server: () => reply(200, "<html>") });
  await assert.rejects(client.api("/api/status"), (error) => error instanceof SyntaxError && error.status === undefined);
});
