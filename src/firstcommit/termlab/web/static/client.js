"use strict";

/*
 * The page's side of the web server shell (termlab/web/shell.py): the access key and the
 * JSON API. The link printed by the server hands the key over once in its fragment, which
 * browsers never send anywhere; from then on it is kept in localStorage, separate per host
 * and port. Defines one global, createClient.
 */

/*
 * Builds the client and reads the key at once, removing it from the address bar. Options:
 * - header: the header the server expects the key in, as in its ShellSettings.
 * - storageKey: the localStorage key that keeps the key.
 * - command: the command that starts the server, named when it does not answer.
 * - timeoutMs: how long a request waits for the server unless the call says otherwise.
 * - onLocked: called when the server refuses the key, so the page can ask for the link again.
 */
function createClient({ header, storageKey, command, timeoutMs = 15000, onLocked = () => {} }) {
  function recall() {
    try {
      return JSON.parse(localStorage.getItem(storageKey));
    } catch (error) {
      return null;
    }
  }

  function remember(value) {
    try {
      if (value === null) localStorage.removeItem(storageKey);
      else localStorage.setItem(storageKey, JSON.stringify(value));
    } catch (error) {
      /* Storage is blocked: the key lasts until the page closes. */
    }
  }

  function readToken() {
    const match = location.hash.match(/[#&]token=([^&]+)/);
    if (!match) return recall();
    history.replaceState(null, "", location.pathname + location.search);
    const found = decodeURIComponent(match[1]);
    remember(found);
    return found;
  }

  let token = readToken();

  /* What a call throws when the server gave no whole reply in time. */
  const noAnswer = () => Object.assign(new Error(`the game server did not answer. Is \`${command}\` still running?`), { status: 0 });

  /* Calls the game's JSON API and resolves with the parsed JSON of a 2xx reply. Otherwise it throws an
     Error whose `status` is 0 when no whole reply came in time (network error, timeout, or a body
     that stopped or never arrived), 403 when the key was refused (onLocked has been called), or the
     HTTP status, with the server's error text as message and the whole parsed reply as `data` ({}
     when the reply is not JSON). Anything else (a request the browser cannot build, a 2xx reply
     that is not JSON) throws the browser's own error, without a status. */
  async function api(path, body, timeout = timeoutMs) {
    const headers = { [header]: token || "" };
    const options = body === undefined
      ? { headers }
      : { method: "POST", headers: { ...headers, "Content-Type": "application/json" }, body: JSON.stringify(body) };
    /* Built before fetching, so that only fetch's own rejection is taken for "no reply". */
    const request = new Request(path, { ...options, signal: AbortSignal.timeout(timeout) });
    const response = await fetch(request).catch(() => {
      throw noAnswer();
    });
    if (response.status === 403) {
      /* A stale key, from an earlier run of the server: forget it and ask for the new link. */
      token = null;
      remember(null);
      onLocked();
      throw Object.assign(new Error("no access key"), { status: 403 });
    }
    if (!response.ok) {
      /* Error replies may come from outside the API (a plain-text page), so their body is optional. */
      const data = await response.json().catch(() => ({}));
      throw Object.assign(new Error(data.error || `${response.status} ${response.statusText}`), { status: response.status, data });
    }
    /* The body comes under the same timeout: when it fires before the body has all arrived, or the
       connection drops, reading it fails with the browser's AbortError or TypeError. */
    return response.json().catch((error) => {
      throw error.name === "SyntaxError" ? error : noAnswer();
    });
  }

  return {
    /* The access key, or null when there is none (no link opened yet, or refused since). */
    token: () => token,
    api,
  };
}
