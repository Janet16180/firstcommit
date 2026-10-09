"""
Build ../storyboard.html from the recorded terminal output in out/, so every git line on the page
is the recorder's, character for character.

Run: python3 storyboard.py   (from this folder)
"""

import html
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROMPT = "project $ "


def runs(name: str) -> list[tuple[str, str]]:
    """Split a recorded session into (typed line, its output) pairs."""
    text = (HERE / "out" / f"{name}.txt").read_text()
    pairs = []
    for chunk in text.split(PROMPT)[1:]:
        if not chunk:
            continue
        line, _, output = chunk.partition("\n")
        pairs.append((line, output))
    return pairs


def typed(name: str, line: str, occurrence: int = 0) -> tuple[str, str]:
    found = [pair for pair in runs(name) if pair[0] == line]
    return found[occurrence]


def terminal(*pairs: tuple[str, str], waiting: bool = False, prompt_after: bool = True, note: str = "") -> str:
    body = ""
    for line, output in pairs:
        body += f'<span class="ps">{html.escape(PROMPT)}</span><span class="cmd">{html.escape(line)}</span>\n{html.escape(output)}'
    if waiting:
        body = body.rstrip("\n") + "\n" + '<span class="cursor" aria-hidden="true"> </span>'
    elif prompt_after:
        body += f'<span class="ps">{html.escape(PROMPT)}</span><span class="cursor" aria-hidden="true"> </span>'
    status = '<span class="term-state">waiting for the panel</span>' if waiting else ""
    caption = f'<p class="term-note">{note}</p>' if note else ""
    return f'<figure class="term"><figcaption>Terminal{status}</figcaption><pre>{body}</pre>{caption}</figure>'


def line(text: str, part: str, who: str = "", dropped: bool = False, marker_gone: bool = False) -> str:
    classes = ["kl"]
    if part in ("ours-start", "fence", "theirs-end"):
        classes.append("is-marker")
    if dropped or marker_gone:
        classes.append("is-dropped")
    tag = f'<span class="tag tag-{who}">{"You" if who == "you" else "Alex"}</span>' if who else ""
    return f'<li class="{" ".join(classes)}" data-part="{part}"><span class="kt">{html.escape(text)}</span>{tag}</li>'


def picks(chosen: str | None) -> str:
    buttons = [("yours", "you", "Yours"), ("theirs", "alex", "Alex's"), ("both", "both", "Both")]
    row = "".join(
        f'<span class="pick pick-{who}{" is-on" if chosen == value else ""}">{label}</span>' for value, who, label in buttons
    )
    return f'<li class="choose"><span>Keep:</span>{row}</li>'


def block(ours: list[str], theirs: list[str], chosen: str | None) -> str:
    gone = chosen is not None
    out = line("<<<<<<< HEAD", "ours-start", marker_gone=gone)
    out += "".join(line(text, "ours", "you", dropped=chosen == "theirs") for text in ours)
    out += line("=======", "fence", marker_gone=gone)
    out += "".join(line(text, "theirs", "alex", dropped=chosen == "yours") for text in theirs)
    out += line(">>>>>>> scout", "theirs-end", marker_gone=gone)
    return out + picks(chosen)


def panel(first: str | None, second: str | None, *, message: str = "") -> str:
    ready = first is not None and second is not None
    lines = line("Launch plan", "same")
    lines += block(["Window: 07:00"], ["Window: 05:30"], first)
    lines += "".join(line(text, "same") for text in ["Pilot: Cadet", "Destination: Base 7", "Cargo:", "- water", "- fuel cells"])
    lines += block(["- oxygen"], ["- spare antenna"], second)
    note = f'<p class="msg">{message}</p>' if message else ""
    return f"""<figure class="panel">
<figcaption class="bar"><span>Merge tool</span> <code>firstcommit</code> <span class="bar-file">launch.txt</span></figcaption>
<p class="outside">Lines outside the markers: Git merged them on its own. Pick a side for each block.</p>
<div class="box"><h4><span>launch.txt</span><span class="state">conflict: 2 blocks</span></h4><ol>{lines}</ol></div>
<div class="act"><span class="btn cancel">Cancel</span><span class="btn write{" is-ready" if ready else ""}">Write this into launch.txt</span></div>
{note}<p class="honest">A training tool, one click per conflict. Real merge tools show more; the debrief says how.</p>
</figure>"""


def resolved(text: str, message: str) -> str:
    lines = "".join(line(entry, "same") for entry in text.rstrip("\n").split("\n"))
    return f"""<figure class="panel">
<figcaption class="bar"><span>Merge tool</span> <code>firstcommit</code> <span class="bar-file">launch.txt</span></figcaption>
<div class="box"><h4><span>launch.txt, as it is now</span><span class="state is-ok">no markers left</span></h4><ol>{lines}</ol></div>
<p class="msg is-ok">{message}</p>
</figure>"""


def sides() -> str:
    return """<figure class="sides">
<figcaption>Two sides: <code>launch.txt</code>, 2 conflicts</figcaption>
<div class="half you"><b>You</b> <span>Window: 07:00</span><span>- oxygen</span></div>
<div class="half alex"><b>Alex</b> <span>Window: 05:30</span><span>- spare antenna</span></div>
<p class="crew-note">Crew note on Alex's commit: <em>The window closes early: launch at 05:30, and pack a spare antenna</em></p>
</figure>"""


def chain() -> str:
    return """<figure class="chain">
<figcaption>History</figcaption>
<ol>
<li class="merge"><span class="cap two"></span><span><b>main</b> <em>Merge branch 'scout'</em> <small>two parents</small></span></li>
<li class="you"><span class="cap"></span><span><em>Launch at 07:00 and pack oxygen</em></span></li>
<li class="alex"><span class="cap"></span><span><b class="lab">scout</b> <em>The window closes early: launch at 05:30, and pack a spare antenna</em></span></li>
<li class="you"><span class="cap"></span><span><em>Write the launch plan</em></span></li>
</ol>
</figure>"""


def rama(text: str, mood: str = "info") -> str:
    return f'<p class="rama rama-{mood}"><b>Rama</b> {text}</p>'


def beat(number: str, title: str, body: str, picture: str = "", term: str = "") -> str:
    grid = f'<div class="grid"><div class="left">{picture}</div><div class="right">{term}</div></div>' if picture or term else ""
    return f'<section class="beat"><h2><span class="n">{number}</span> {title}</h2>{body}{grid}</section>'


def code(text: str) -> str:
    return f"<code>{html.escape(text)}</code>"


MISSION = "1-mission"
merge = typed(MISSION, "git merge --no-edit scout")
tool = typed(MISSION, "git mergetool")
status = typed(MISSION, "git status")
commit = typed(MISSION, "git commit --no-edit")
cat_after = typed(MISSION, "cat launch.txt")
waiting_output = tool[1]
cancel_run = typed("3-cancel", "git mergetool")
before = typed("2-before-merge", "git mergetool")
restore = typed("15-restore-theirs", "git restore --theirs launch.txt")
restore_cat = typed("15-restore-theirs", "cat launch.txt")
wrong_tool = typed("16-wrong-pick", "git mergetool")
abort = typed("16-wrong-pick", "git merge --abort")
again = typed("16-wrong-pick", "git merge --no-edit scout", 1)
added_twice = typed("14-twice", "git add launch.txt")
guessed = typed("17-git-guesses", "git mergetool")
defaults_tool = typed("7-git-defaults", "git mergetool")
defaults_ls = typed("7-git-defaults", "ls")
defaults_short = typed("7-git-defaults", "git status --short")
hung = typed("18-hangup", "git mergetool")
after_hang = typed("18-hangup", "git status --short")

beats = [
    beat("1", "Scene", """<ol class="frames">
<li><span class="art">collision</span> Two crews changed the launch plan, and it cracked in two places.</li>
<li><span class="art">collision</span> You know the terminal way. Today Git opens a tool for you: one click per conflict.</li>
</ol>"""),
    beat("2", "Briefing", """<div class="brief"><p>You moved the launch to 07:00 and packed oxygen, on <code>main</code>. Alex, on <code>scout</code>, moved it to 05:30 and packed a spare antenna: the launch window closes early. Bring <code>scout</code> into <code>main</code>, and answer both conflicts with a merge tool: Alex's launch time, and both cargo lines.</p>
<p>The mission is done when <code>main</code>'s last commit holds <code>scout</code>'s work, launches at 05:30 and packs both the oxygen and the spare antenna, with no conflict markers.</p></div>
<ol class="goals"><li>Bring <code>scout</code> into <code>main</code>.</li><li>Open the merge tool, and answer each conflict.</li><li>See what the tool did.</li><li>Finish the merge.</li></ol>"""),
    beat("3", "Bring <code>scout</code> into <code>main</code>",
         '<p class="step">Step 1 of 4. The player types the merge from 7-1. It stops with two conflicts in one file; the Two sides view shows both, the crew note pinned.</p>'
         + rama("The merge stopped: <code>launch.txt</code> has two conflicts."),
         sides(), terminal(merge)),
    beat("4", "Open the merge tool",
         '<p class="step">Step 2 of 4. Git prints which files need merging, then starts the game\'s tool on <code>launch.txt</code>. The tool sets the terminal\'s title, and the page opens the merge panel over the Two sides view. The terminal waits: keys typed there do nothing, and Ctrl-C cancels.</p>'
         + rama("Git opened the game's merge tool: the panel. Your terminal waits until you press Write.")
         + rama("In git's words, local is yours and remote is Alex's.") + '<p class="step">(The second line plays once per player, the first time <code>{local}</code> and <code>{remote}</code> appear.)</p>',
         panel(None, None), terminal(merge, ("git mergetool", waiting_output), waiting=True)),
    beat("5", "Pick a side for each conflict",
         '<p class="step">Alex\'s for the window: your 07:00 line is struck through and the markers fade. Both for the cargo: your oxygen, then Alex\'s spare antenna. Nothing is written yet; Write turns gold once every block has a pick.</p>',
         panel("theirs", "both"), terminal(("git mergetool", waiting_output), waiting=True)),
    beat("6", "Write",
         '<p class="step">The page sends the picks; the server rewrites only the marker blocks, into a temporary file beside it, then swaps it in whole, so the tool never reads half a file. The tool sees no markers left and ends with success, so git adds <code>launch.txt</code> and returns to the prompt. Git prints nothing more.</p>'
         + rama("The tool wrote <code>launch.txt</code>, and Git added it to the staging area (the cargo dock). No <code>git add</code> this time.", "ok"),
         resolved(cat_after[1], "Written from your picks. The tool finished, and Git added <code>launch.txt</code>. Next: <code>git status</code>."),
         terminal(("git mergetool", waiting_output))),
    beat("7", "See what the tool did",
         '<p class="step">Step 3 of 4. "All conflicts fixed": <code>launch.txt</code> is under "Changes to be committed".</p>'
         + rama("<code>launch.txt</code> is in the staging area (the cargo dock): the tool added it for you.", "ok"),
         sides().replace("2 conflicts", "no conflict left"), terminal(status)),
    beat("8", "Finish the merge",
         '<p class="step">Step 4 of 4. The merge commit keeps Git\'s prepared message, as in 7-3.</p>'
         + rama("<code>main</code>'s last commit holds <code>scout</code>'s work, launches at 05:30 and packs both.", "ok"),
         chain(), terminal(commit)),
    beat("9", "Debrief", """<div class="brief"><p><code>git mergetool</code> opened a merge tool on the file in conflict: here, the game's panel. You answered each conflict on its own, Write saved the file, and when the tool finished, Git added <code>launch.txt</code> to the staging area itself. <code>git commit --no-edit</code> finished the merge, as in 7-3. <code>git restore --theirs</code> could not have done it: it keeps one side for the whole file.</p>
<div class="honest-box"><p>Real tools differ. The panel is a training tool: one click per conflict, made to learn with. At work, people answer conflicts in their editor's merge view or in a merge tool. In VS Code you usually open its merge editor from the conflicted file or from the Source Control view; it can also be set as git's merge tool. A tool such as Meld is what <code>git mergetool</code> opens once you set your own: <code>git config merge.tool meld</code>. Real tools show more of the file and let you write an answer line by line, for when neither side alone is right.</p>
<p>The game also hides two things git does on its own. It keeps the file as it was, markers and all, as <code>launch.txt.orig</code> after each answer, until you delete it. And when no tool is set, it picks one it finds and asks "Hit return to start merge resolution tool" before opening it.</p></div>
<p>The terminal way from 7-3 works everywhere, with or without a tool, and so does <code>git merge --abort</code>.</p>
<pre class="keep-cmds">$ git mergetool   # open the merge tool on each file in conflict; it adds each answer</pre></div>
<p class="step">Designer note: what git does without the game's settings, recorded in a fresh home. Not shown to the player; it backs the debrief's last paragraph.</p>"""
         + '<div class="grid"><div class="left">' + terminal(guessed, prompt_after=False, note="No <code>merge.tool</code> set: git lists the tools it would try and asks before starting one (here it found vimdiff). The recorder pressed Ctrl-C at the question.")
         + '</div><div class="right">' + terminal(("git mergetool", defaults_tool[1]), defaults_ls, defaults_short, note="A tool set, git's other defaults: the backup stays as <code>launch.txt.orig</code>, untracked.") + "</div></div>"),
]

mistakes = [
    beat("M1", "Cancel in the panel (or Ctrl-C)",
         '<p class="step">The panel\'s Cancel types Ctrl-C into the terminal. The tool reads it as a key, ends with failure, and git puts the file back as it was before the tool started. "failed" is git\'s word; nothing is lost.</p>'
         + rama("You stopped the tool, so Git put <code>launch.txt</code> back as it was, markers and all. Nothing is lost. Run <code>git mergetool</code> again when you are ready.", "warn"),
         sides(), terminal(cancel_run)),
    beat("M2", "<code>git mergetool</code> before the merge",
         '<p class="step">No file is in conflict, so git starts no tool and the panel never opens. Exit status 0.</p>'
         + rama("Nothing to answer yet: Git opens a merge tool only for files in conflict. Start the merge first: <code>git merge --no-edit scout</code>.", "warn"),
         "", terminal(before)),
    beat("M3", "7-3's way: <code>git restore --theirs</code>",
         '<p class="step">Alex\'s side of the whole file: the window is right, but your oxygen line is gone. The step stays open with its message.</p>'
         + rama("That keeps Alex's side of the whole file, so your oxygen line went too. Here each conflict needs its own answer: <code>git mergetool</code>.", "warn"),
         "", terminal(restore, restore_cat)),
    beat("M4", "Yours for the window",
         '<p class="step">The tool succeeds (the file has no markers), so git adds 07:00. The step names the fix with commands from 7-2 and 7-1.</p>'
         + rama("<code>launch.txt</code> launches at 07:00, after the window closes. To answer again: <code>git merge --abort</code>, then <code>git merge --no-edit scout</code> and <code>git mergetool</code>.", "warn"),
         panel("yours", "both"), terminal(("git mergetool", wrong_tool[1]), abort, again)),
    beat("M5", "<code>git add</code> after the tool",
         '<p class="step">Harmless: the file is already in the staging area. Git prints nothing.</p>'
         + rama("The tool already added <code>launch.txt</code>. Adding it again changes nothing."),
         "", terminal(added_twice)),
    beat("M6", "The terminal closes while the tool waits",
         '<p class="step">Not a player\'s mistake: a closed tab or a lost connection. The hang-up ends the tool and git with it; the file keeps its markers and the merge stays paused. The page closes the panel with the terminal; a new terminal finds no tool waiting. The temporary copies left behind sit in the game home and go at the next reset.</p>'
         + rama("Your terminal restarted, so the merge tool stopped. <code>launch.txt</code> is as it was: run <code>git mergetool</code> again."),
         "", terminal(("git mergetool", hung[1].replace("\n[the terminal closes; a new one opens]\n", "")), prompt_after=False, note="The terminal closes here; a new one opens.") + terminal(after_hang)),
]

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Merge tools storyboard</title>
<style>
:root {
  --bg: #E6E3EF; --panel: #FBF9F3; --panel-2: #EFEBE0; --ink: #1F1A3D; --ink-soft: #5E577E;
  --edge: #1F1A3D; --line: #C9C3DA; --you: #7A52D1; --alex: #3D8A18; --gold: #F2B01E;
  --ok: #1D93A8; --warn: #B98A00; --err: #D33A32; --on-accent: #FFFFFF;
  --crt: #120F2C; --crt-ink: #FFE6B0; --crt-soft: #9F95C8; --crt-cmd: #FFD25A;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0E0C24; --panel: #1B1840; --panel-2: #141134; --ink: #F2EAD3; --ink-soft: #A39CC9;
    --edge: #04030F; --line: #332E66; --you: #B08CFF; --alex: #A6E05A; --ok: #4FD8EA;
    --warn: #FFD054; --err: #FF6B5E; --on-accent: #120F2C; color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #0E0C24; --panel: #1B1840; --panel-2: #141134; --ink: #F2EAD3; --ink-soft: #A39CC9;
  --edge: #04030F; --line: #332E66; --you: #B08CFF; --alex: #A6E05A; --ok: #4FD8EA;
  --warn: #FFD054; --err: #FF6B5E; --on-accent: #120F2C; color-scheme: dark;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1180px; margin: 0 auto; padding: 24px 16px 64px; }
h1 { font-size: 1.6rem; margin: 0 0 4px; }
h2 { font-size: 1.15rem; margin: 0 0 8px; display: flex; gap: 10px; align-items: baseline; flex-wrap: wrap; }
h2 .n { background: var(--edge); color: #FBF9F3; padding: 0 8px; font-size: 0.9rem; }
.lede { color: var(--ink-soft); margin: 0 0 20px; max-width: 70ch; }
code, pre { font-family: ui-monospace, Menlo, Consolas, monospace; }
code { font-size: 0.92em; background: var(--panel-2); padding: 0 3px; }
em { font-style: italic; }
.beat { background: var(--panel); border: 3px solid var(--edge); box-shadow: 5px 5px 0 var(--edge); padding: 16px; margin: 0 0 22px; }
.step { margin: 0 0 8px; max-width: 75ch; }
.grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 14px; margin-top: 10px; align-items: start; }
.grid .left:empty { display: none; }
.grid:has(.left:empty) { grid-template-columns: minmax(0, 1fr); }
@media (max-width: 760px) { .grid { grid-template-columns: minmax(0, 1fr); } }
figure { margin: 0; }
.term { background: var(--crt); color: var(--crt-ink); border: 3px solid var(--you); }
.term figcaption { background: var(--you); color: var(--on-accent); font-size: 0.8rem; font-weight: 700; padding: 2px 8px; display: flex; gap: 8px; flex-wrap: wrap; }
.term-state { background: var(--gold); color: #1F1A3D; padding: 0 6px; }
.term pre { margin: 0; padding: 10px; white-space: pre-wrap; overflow-wrap: anywhere; font-size: 0.86rem; line-height: 1.4; }
.term .ps { color: var(--crt-soft); }
.term .cmd { color: var(--crt-cmd); }
.term .cursor { background: var(--crt-ink); }
.term-note code { background: transparent; color: var(--crt-cmd); }
code { white-space: nowrap; }
.term-note { margin: 0; padding: 4px 10px 8px; color: var(--crt-soft); font-size: 0.8rem; }
.rama { margin: 8px 0 0; padding: 6px 10px; border-left: 6px solid var(--ok); background: var(--panel-2); max-width: 75ch; }
.rama b { margin-right: 6px; }
.rama-ok { border-color: var(--alex); }
.rama-warn { border-color: var(--warn); }
.frames, .goals { margin: 0; padding-left: 22px; }
.frames li { margin: 4px 0; }
.art { display: inline-block; font-size: 0.75rem; border: 2px dashed var(--line); padding: 0 6px; margin-right: 6px; color: var(--ink-soft); }
.brief p { max-width: 75ch; }
.honest-box { border: 2px solid var(--gold); padding: 8px 10px; background: var(--panel-2); }
.keep-cmds { background: var(--crt); color: var(--crt-ink); padding: 10px; white-space: pre-wrap; overflow-wrap: anywhere; font-size: 0.86rem; }
.panel { border: 3px solid var(--edge); background: var(--panel); display: flex; flex-direction: column; gap: 8px; padding-bottom: 8px; font-size: 0.92rem; }
.panel .bar { background: var(--gold); color: #1F1A3D; padding: 3px 10px; font-weight: 700; display: flex; gap: 6px; flex-wrap: wrap; align-items: baseline; }
.panel .bar code { background: transparent; }
.bar-file { margin-left: auto; font-family: ui-monospace, Menlo, Consolas, monospace; }
.outside, .msg, .honest { margin: 0 10px; }
.outside { color: var(--ink-soft); }
.honest { color: var(--ink-soft); font-size: 0.82rem; border-top: 2px dashed var(--line); padding-top: 6px; }
.box { margin: 0 10px; border: 3px solid var(--edge); }
.box h4 { margin: 0; padding: 3px 10px; background: var(--edge); color: var(--crt-ink); display: flex; flex-wrap: wrap; gap: 4px 10px; font: 700 0.95rem ui-monospace, Menlo, Consolas, monospace; }
.state { margin-left: auto; color: #FF8A78; }
.state.is-ok { color: #9EF0A0; }
.box ol { list-style: none; margin: 0; padding: 4px 0; font: 0.9rem/1.5 ui-monospace, Menlo, Consolas, monospace; }
.kl { display: flex; flex-wrap: wrap; gap: 2px 8px; align-items: center; padding: 0 10px; }
.kt { white-space: pre-wrap; overflow-wrap: anywhere; }
.kl.is-marker { color: var(--ink-soft); }
.kl.is-dropped { text-decoration: line-through; opacity: 0.45; }
.kl[data-part="ours"] { background: color-mix(in srgb, var(--you) 14%, var(--panel)); box-shadow: inset 5px 0 0 var(--you); }
.kl[data-part="theirs"] { background: color-mix(in srgb, var(--alex) 14%, var(--panel)); box-shadow: inset 5px 0 0 var(--alex); }
.tag { padding: 0 6px; border-radius: 8px; color: var(--on-accent); font: 700 0.7rem system-ui, sans-serif; }
.tag-you { background: var(--you); }
.tag-alex { background: var(--alex); }
.choose { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; padding: 6px 10px; border-top: 2px dashed var(--line); border-bottom: 2px dashed var(--line); font: 700 0.85rem system-ui, sans-serif; }
.pick { padding: 2px 10px; border: 2px solid var(--edge); background: var(--panel); }
.pick-you.is-on { background: var(--you); color: var(--on-accent); }
.pick-alex.is-on { background: var(--alex); color: var(--on-accent); }
.pick-both.is-on { background: var(--gold); color: #1F1A3D; }
.act { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 10px; }
.btn { padding: 4px 12px; border: 3px solid var(--edge); font-weight: 700; }
.btn.write { background: var(--gold); color: #1F1A3D; opacity: 0.45; }
.btn.write.is-ready { opacity: 1; }
.btn.cancel { background: var(--panel); }
.msg { padding: 6px 10px; border: 2px solid var(--edge); }
.msg.is-ok { border-color: var(--ok); }
.sides { border: 3px solid var(--edge); background: var(--panel-2); padding: 8px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.sides figcaption, .sides .crew-note { grid-column: 1 / -1; margin: 0; }
.sides .crew-note { font-size: 0.85rem; color: var(--ink-soft); }
.half { display: flex; flex-direction: column; padding: 6px 8px; border: 2px solid var(--edge); font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 0.85rem; overflow-wrap: anywhere; }
.half b { font-family: system-ui, sans-serif; }
.half.you { box-shadow: inset 5px 0 0 var(--you); background: color-mix(in srgb, var(--you) 12%, var(--panel)); }
.half.alex { box-shadow: inset 5px 0 0 var(--alex); background: color-mix(in srgb, var(--alex) 12%, var(--panel)); }
.chain { border: 3px solid var(--edge); background: var(--panel-2); padding: 8px; }
.chain ol { list-style: none; margin: 6px 0 0; padding: 0; }
.chain li { display: flex; gap: 8px; align-items: center; padding: 3px 0; overflow-wrap: anywhere; }
.cap { flex: none; width: 18px; height: 18px; border-radius: 50%; border: 3px solid var(--edge); background: var(--you); }
.chain li.alex .cap { background: var(--alex); }
.cap.two { background: linear-gradient(90deg, var(--you) 50%, var(--alex) 50%); }
.chain small { color: var(--ink-soft); }
.lab { border: 2px solid var(--alex); padding: 0 4px; }
.mistakes-h { font-size: 1.3rem; margin: 30px 0 8px; }
</style>
</head>
<body>
<main>
<h1>7-4 Merge tools: storyboard</h1>
<p class="lede">The mission beat by beat: the terminal as the player sees it, and the page's merge panel. Every line of terminal output is a real git 2.43 run (recorder/record.py, recorder/out/). The two "Waiting" lines come from the prototype of the game's tool, not from git. Violet is you, green is Alex. Script: script.md; technical plan: plan.md.</p>
{beats}
<h2 class="mistakes-h">Expected mistakes</h2>
{mistakes}
</main>
</body>
</html>
"""

(HERE.parent / "storyboard.html").write_text(PAGE.replace("{beats}", "\n".join(beats)).replace("{mistakes}", "\n".join(mistakes)))
