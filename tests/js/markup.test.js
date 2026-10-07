"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const { html } = require("./fakedom");
const { installBrowser, load } = require("./load");

installBrowser();
const { Markup } = load(["dom.js", "markup.js"], ["Markup"]);
const SHARED_FIXTURE = path.join(__dirname, "..", "fixtures", "markup.json");

const span = (text, code = false) => ({ text, code });
const rendered = (blocks) => Markup.render(blocks).map(html).join("");

test("a paragraph shows its spans, with code spans as code", () => {
  const blocks = [{ kind: "para", spans: [span("Open "), span("README.md", true), span(" now.")] }];
  assert.equal(rendered(blocks), "<p>Open <code>README.md</code> now.</p>");
});

test("blocks fold under a closed More, and no blocks fold nothing", () => {
  const blocks = [{ kind: "para", spans: [span("Git keeps it in "), span(".git/index", true), span(".")] }];
  assert.equal(html(Markup.more(blocks)), "<details class=\"more\"><summary>More</summary><p>Git keeps it in <code>.git/index</code>.</p></details>");
  assert.equal(Markup.more([]), null);
});

test("a command of several words may break only between its words, never inside one", () => {
  const blocks = [{ kind: "para", spans: [span("Run "), span("git config --global user.name", true), span(".")] }];
  assert.equal(rendered(blocks), '<p>Run <code class="words"><span>git</span> <span>config</span> <span>--global</span> <span>user.name</span></code>.</p>');
});

test("a verbatim block is preformatted code, kept exactly", () => {
  const blocks = [{ kind: "code", text: "$ git log --oneline\nce01362 First commit" }];
  assert.equal(rendered(blocks), '<pre class="code"><code>$ git log --oneline\nce01362 First commit</code></pre>');
});

test("bullets are a list of items made of spans", () => {
  const blocks = [{ kind: "bullets", items: [[span("the "), span("main", true), span(" branch")], [span("a tag")]] }];
  assert.equal(rendered(blocks), "<ul><li>the <code>main</code> branch</li><li>a tag</li></ul>");
});

test("blocks are rendered in order", () => {
  const blocks = [{ kind: "para", spans: [span("One.")] }, { kind: "code", text: "two" }, { kind: "para", spans: [span("Three.")] }];
  assert.equal(rendered(blocks), '<p>One.</p><pre class="code"><code>two</code></pre><p>Three.</p>');
});

test("text that looks like html is shown as text", () => {
  const blocks = [{ kind: "para", spans: [span("<img src=x onerror=alert(1)>"), span("<b>", true)] }];
  assert.equal(rendered(blocks), "<p>&lt;img src=x onerror=alert(1)&gt;<code>&lt;b&gt;</code></p>");
});

test("an unknown kind of block is an error, not a blank", () => {
  assert.throws(() => Markup.render([{ kind: "table", rows: [] }]), /unknown block kind: table/);
});

test("plain text joins the blocks for labels and titles", () => {
  const blocks = [{ kind: "para", spans: [span("Run "), span("git add", true), span(".")] }, { kind: "bullets", items: [[span("a")], [span("b")]] }];
  assert.equal(Markup.plain(blocks), "Run git add.\na\nb");
});

test("every case of the shared markup fixture renders all of its text", () => {
  const fixture = JSON.parse(fs.readFileSync(SHARED_FIXTURE, "utf8"));
  const cases = Array.isArray(fixture) ? fixture : fixture.cases;
  assert.ok(cases.length > 0);
  const text = (spans) => spans.map((item) => item.text).join("");
  const written = (block) => (block.kind === "code" ? block.text : block.kind === "para" ? text(block.spans) : block.items.map(text).join(""));
  for (const { blocks } of cases) {
    assert.equal(Markup.render(blocks).map((node) => node.textContent).join(""), blocks.map(written).join(""));
  }
});
