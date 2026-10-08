"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

installBrowser();
const { Places, Strings } = load(["dom.js", "strings.js", "places.js"], ["Places", "Strings"]);

const REAL = {
  en: { workshop: "Working folder", dock: "Staging area", vault: "Repository", remote: "Remote" },
  es: { workshop: "Carpeta de trabajo", dock: "Staging area", vault: "Repositorio", remote: "Remoto" },
};
const GAME = {
  en: { workshop: "workshop", dock: "cargo dock", vault: "vault", remote: "mothership" },
  es: { workshop: "taller", dock: "muelle de carga", vault: "bóveda", remote: "nave nodriza" },
};

test("every place label names the real git place first, then the game's name in brackets, in both languages", () => {
  for (const language of ["en", "es"]) {
    Strings.use(language);
    for (const id of Places.IDS) {
      const label = Places.label(id);
      assert.equal(label.textContent, `${REAL[language][id]} (${GAME[language][id]})`, `${language} ${id}`);
      assert.equal(label.querySelector(".place-game").textContent, ` (${GAME[language][id]})`);
      assert.equal(Places.text(id), label.textContent);
    }
  }
  Strings.use("en");
});

test("the four places are the working folder, the staging area, the repository and the remote", () => {
  assert.deepEqual(Places.IDS, ["workshop", "dock", "vault", "remote"]);
});
