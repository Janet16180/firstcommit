"""
Build the four places demo: one standalone, playable HTML page.

Run it from the repository::

    uv run python tools/demo/build.py demo/places-demo.html

It records every scenario on real git first (recordings.py, and share.py for sharing a file with
Alex; a few seconds), then writes one HTML file holding the game's own scripts and stylesheets
(from src/firstcommit/web/static), the recordings as embedded JSON, and the demo's buttons: your
first commits step by step, sharing a file with Alex step by step, and one command at a time. The page fetches nothing and stores
nothing, so it runs as a file, or in a sandboxed iframe on another origin. Its light or dark look
follows the system until switched; under reduced motion it shows each result without moving.
"""

import json
import sys
from pathlib import Path

from recordings import record_commands, record_first_commits
from share import LABELS, record_sharing

STATIC = Path(__file__).resolve().parents[2] / "src" / "firstcommit" / "web" / "static"
SCRIPTS = ["dom.js", "map.js", "theme-time.js", "theme-time-motion.js", "theme-time-places.js", "theme-time-share.js"]
STYLES = ["app.css", "theme-time.css", "theme-time-share.css"]

SCENARIOS = [
    ("add", "git add", "You edited README.md and made a new file, notes.txt. Then:"),
    ("commit", "git commit", "README.md is edited and staged. Then:"),
    ("push", "git push", "You committed a change that GitHub does not have yet. Then:"),
    ("fetch", "git fetch", "A teammate pushed a new rule to GitHub. Then you ran:"),
    ("pull", "git pull", "A teammate pushed a new rule to GitHub. Then you ran:"),
    ("pull-after-fetch", "git pull, after a fetch", "A teammate pushed a new rule, and you already ran git fetch. Then:"),
    ("pull-merge", "git pull, both sides changed", "You committed, and a teammate pushed too: both sides have new commits. Then:"),
    ("clone", "git clone", "GitHub has the project and your folder is empty. Then:"),
]
"""The single commands' buttons: recording name, label, and the set-up the lab ran before it."""

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Four places demo</title>
<style>
{styles}
body {{ margin: 0; background: var(--bg); }}
.demo {{ max-width: 1320px; margin: 0 auto; padding: 20px 16px 32px; }}
.demo h1 {{ margin: 0 0 4px; font-family: var(--serif); font-size: 1.5rem; }}
.demo-lead {{ margin: 0 0 14px; color: var(--muted); }}
.demo-bar {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 10px; }}
.demo-bar .btn {{ font-family: var(--mono); }}
.demo-bar .btn[aria-pressed="true"] {{ border-color: var(--map-head); box-shadow: inset 0 0 0 1px var(--map-head); }}
.demo-tools {{ display: flex; gap: 8px; margin-left: auto; }}
.demo-tools .btn {{ font-family: inherit; }}
.demo-group {{ margin: 6px 0 4px; font-weight: 650; }}
.demo-step {{ margin: 6px 0 12px; }}
.demo-step p {{ margin: 0; color: var(--muted); }}
.demo-step code {{ display: block; margin-top: 4px; font-size: 1.05rem; font-weight: 700; }}
.demo-figure {{ padding: 4px 0; border: 1px solid var(--line); border-radius: var(--radius); background: var(--surface); }}
.demo-note {{ margin: 10px 0 0; color: var(--muted); font-size: 0.9rem; }}
.demo-note[hidden] {{ display: none; }}
</style>
</head>
<body>
<main class="demo">
  <h1>Your computer and GitHub: the four places</h1>
  <p class="demo-lead">Pick a command to see what it moves, and from where to where. Every drawing is recorded from real git.</p>
  <p class="demo-group">Your first commits, step by step:</p>
  <div class="demo-bar">
    <div class="demo-bar" id="steps" role="group" aria-label="Steps"></div>
    <button type="button" class="btn btn-primary btn-small" data-next="step">Next step</button>
  </div>
  <p class="demo-group">Share a file with Alex, step by step:</p>
  <div class="demo-bar">
    <div class="demo-bar" id="share" role="group" aria-label="Sharing steps"></div>
    <button type="button" class="btn btn-primary btn-small" data-next="share">Next step</button>
  </div>
  <p class="demo-group">One command at a time:</p>
  <div class="demo-bar">
    <div class="demo-bar" id="scenarios" role="group" aria-label="Commands"></div>
    <div class="demo-tools">
      <button type="button" class="btn btn-ghost btn-small" id="replay">Replay</button>
      <button type="button" class="btn btn-ghost btn-small" id="theme"></button>
    </div>
  </div>
  <div class="demo-step"><p id="setup"></p><div id="command"></div></div>
  <div class="demo-figure" id="figure"></div>
  <p class="demo-note" id="still" hidden>Your system asks for reduced motion, so the figure shows the result without moving. The lit arrows and the sentence under them say what happened.</p>
</main>
<script type="application/json" id="data">{data}</script>
<script type="application/json" id="steps-data">{steps}</script>
<script type="application/json" id="share-data">{share}</script>
<script>
{scripts}
</script>
<script>
"use strict";
(function () {{
  const DATA = JSON.parse(document.getElementById("data").textContent);
  const STEPS = JSON.parse(document.getElementById("steps-data").textContent);
  const SHARE = JSON.parse(document.getElementById("share-data").textContent);
  const SHARE_LABELS = {share_labels};
  const SCENARIOS = {scenarios};
  const root = document.documentElement;
  const dark = window.matchMedia("(prefers-color-scheme: dark)");
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  const box = document.getElementById("figure");
  const themeButton = document.getElementById("theme");
  let chosen = null;
  let current = {{ kind: "step", key: 0 }};
  let timer = null;

  function setTheme(scheme) {{
    root.dataset.theme = scheme;
    themeButton.textContent = scheme === "dark" ? "Light" : "Dark";
    themeButton.setAttribute("aria-label", scheme === "dark" ? "Switch to the light look" : "Switch to the dark look");
  }}

  /* What one button shows: a scenario of the lab, or a step of the first-commits walk. */
  function entry({{ kind, key }}) {{
    if (kind === "scenario") {{
      const data = DATA[key];
      return {{ ...data, lines: [data.command], setup: SCENARIOS.find(([id]) => id === key)[2] }};
    }}
    const step = STEPS[key];
    return {{ ...step, lines: step.commands, setup: `Step ${{key + 1}} of ${{STEPS.length}}: ${{step.name}}.` }};
  }}

  function mark(chosenEntry) {{
    for (const button of document.querySelectorAll("[data-kind]")) {{
      button.setAttribute("aria-pressed", String(button.dataset.kind === chosenEntry.kind && button.dataset.key === String(chosenEntry.key)));
    }}
  }}

  /* A sharing step: Alex's figure, which says its own command and caption. */
  function showShare(chosenEntry) {{
    const step = SHARE[chosenEntry.key];
    document.getElementById("setup").textContent = `Step ${{chosenEntry.key + 1}} of ${{SHARE.length}}.`;
    document.getElementById("command").replaceChildren();
    document.getElementById("still").hidden = !reduced.matches;
    box.replaceChildren(TimeShare.render(step, {{ at: "before" }}));
    timer = setTimeout(() => {{
      const figure = TimeShare.render(step);
      box.replaceChildren(figure);
      TimeShare.play(figure, step);
    }}, reduced.matches ? 0 : 500);
  }}

  /* Shows the state before the command, then the state after it with the command's motion. */
  function show(chosenEntry) {{
    current = chosenEntry;
    clearTimeout(timer);
    mark(chosenEntry);
    if (chosenEntry.kind === "share") {{
      showShare(chosenEntry);
      return;
    }}
    const {{ before, after, events, lines, setup }} = entry(chosenEntry);
    const commands = TimePlaces.commands(events, before.project, after.project);
    document.getElementById("setup").textContent = setup;
    document.getElementById("command").replaceChildren(...lines.map((line) => Object.assign(document.createElement("code"), {{ textContent: `$ ${{line}}` }})));
    document.getElementById("still").hidden = !reduced.matches;
    box.replaceChildren(TimePlaces.render(before, {{}}));
    timer = setTimeout(() => {{
      const figure = TimePlaces.render(after, {{ commands }});
      box.replaceChildren(figure);
      TimePlaces.play(figure, {{ before, after, commands }});
    }}, reduced.matches ? 0 : 500);
  }}

  function button(bar, kind, key, label) {{
    const node = document.createElement("button");
    node.type = "button";
    node.className = "btn btn-ghost btn-small";
    node.dataset.kind = kind;
    node.dataset.key = String(key);
    node.textContent = label;
    node.addEventListener("click", () => show({{ kind, key }}));
    bar.append(node);
  }}
  STEPS.forEach((step, index) => button(document.getElementById("steps"), "step", index, `${{index + 1}}. ${{step.name}}`));
  SHARE.forEach((step, index) => button(document.getElementById("share"), "share", index, `${{index + 1}}. ${{SHARE_LABELS[index]}}`));
  for (const [name, label] of SCENARIOS) button(document.getElementById("scenarios"), "scenario", name, label);
  for (const next of document.querySelectorAll("[data-next]")) {{
    const kind = next.dataset.next;
    const count = kind === "step" ? STEPS.length : SHARE.length;
    next.addEventListener("click", () => show({{ kind, key: current.kind === kind ? (current.key + 1) % count : 0 }}));
  }}
  document.getElementById("replay").addEventListener("click", () => show(current));
  themeButton.addEventListener("click", () => {{
    chosen = root.dataset.theme === "dark" ? "light" : "dark";
    setTheme(chosen);
  }});
  dark.addEventListener("change", () => {{
    if (!chosen) setTheme(dark.matches ? "dark" : "light");
  }});
  setTheme(dark.matches ? "dark" : "light");
  show(current);
}})();
</script>
</body>
</html>
"""


def embedded(value: object) -> str:
    """
    Write data as JSON that is safe inside a script element.

    Parameters
    ----------
    value : object
        JSON-shaped data.

    Returns
    -------
    str
        The JSON, with every ``</`` escaped so no ``</script>`` can end the element.
    """
    return json.dumps(value).replace("</", "<\\/")


def build(static: Path) -> str:
    """
    Record every scenario on real git and write the demo page.

    Parameters
    ----------
    static : Path
        The game's static folder, whose scripts and stylesheets the page holds.

    Returns
    -------
    str
        The whole HTML page.

    Raises
    ------
    ValueError
        If a script holds ``</script``, which would end its element early.
    """
    commands = record_commands()
    sharing = record_sharing()
    scripts = "\n".join(f"/* {name} */\n{(static / name).read_text()}" for name in SCRIPTS)
    if "</script" in scripts:
        raise ValueError("a script holds </script")
    return PAGE.format(
        styles="\n".join((static / name).read_text() for name in STYLES),
        data=embedded({name: commands[name] for name, _, _ in SCENARIOS}),
        steps=embedded(record_first_commits()),
        share=embedded(sharing),
        scripts=scripts,
        scenarios=json.dumps([list(scenario) for scenario in SCENARIOS]),
        share_labels=json.dumps([LABELS[step["id"]] for step in sharing]),
    )


def main() -> None:
    """Write the demo page to the path given on the command line."""
    out = Path(sys.argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(STATIC))
    print(out, out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
