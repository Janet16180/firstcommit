"""
Build the guide-visuals storyboard: one static HTML page, every terminal pasted from record.sh's transcripts.

Usage: python3 -I build.py <transcripts-dir> <out.html>
"""

import html
import sys
from dataclasses import dataclass, field
from pathlib import Path

RUNS = Path(sys.argv[1])
TARGET = Path(sys.argv[2])
COLUMN = 22
ROW = 40


def transcript(scene: str) -> str:
    """
    Give one recorded scene's text, exactly as record.sh wrote it.

    Parameters
    ----------
    scene : str
        The scene's name.

    Returns
    -------
    str
        The transcript.
    """
    return (RUNS / f"{scene}.txt").read_text()


def term(*scenes: str, look: tuple[str, ...] = (), refused: tuple[str, ...] = ()) -> str:
    """
    Draw recorded scenes as the game's night terminal, with pieces of output marked: never in gold, which the pictures keep for what changed.

    Parameters
    ----------
    *scenes : str
        The scenes, shown one after the other.
    look : tuple[str, ...]
        Exact pieces of output that match the picture, underlined in violet.
    refused : tuple[str, ...]
        Exact pieces of output that say git refused, underlined in red.

    Returns
    -------
    str
        The terminal's HTML.
    """
    lines = []
    for line in "".join(transcript(scene) for scene in scenes).rstrip("\n").split("\n"):
        if line.startswith("$ "):
            lines.append(f'<span class="pr">$ </span><span class="cmd">{html.escape(line[2:])}</span>')
            continue
        text = html.escape(line)
        for kind, pieces in (("look", look), ("no", refused)):
            for piece in pieces:
                text = text.replace(html.escape(piece), f'<span class="{kind}">{html.escape(piece)}</span>')
        lines.append(text)
    return '<pre class="term">' + "\n".join(lines) + "</pre>"


@dataclass
class Row:
    """One row of a chain: a commit (with a hash) or a connector row of git's drawing (hash empty)."""

    hash: str = ""
    subject: str = ""
    column: int = 0
    parents: list[str] = field(default_factory=list)
    names: list[str] = field(default_factory=list)
    head: str = ""
    fresh: bool = False
    fresh_names: tuple[str, ...] = ()
    gone: tuple[str, ...] = ()
    mark: str = ""
    note: str = ""
    ring: bool = False
    faint: bool = False
    fresh_head: bool = False


def wires(rows: list[Row], height: int) -> str:
    """
    Draw the lines from each commit down to its parents, as git's graph does: down its own column, then across.

    Parameters
    ----------
    rows : list[Row]
        The chain's rows, newest first.
    height : int
        One row's height in pixels.

    Returns
    -------
    str
        The SVG paths.
    """
    where = {row.hash: (at, row.column) for at, row in enumerate(rows) if row.hash}
    paths = []
    for at, row in enumerate(rows):
        for parent in row.parents:
            below, column = where[parent]
            x1, y1 = row.column * COLUMN + COLUMN // 2, at * height + height // 2
            x2, y2 = column * COLUMN + COLUMN // 2, below * height + height // 2
            if column > row.column:
                points = f"{x1},{y1} {x2},{y1 + height} {x2},{y2}"
            else:
                points = f"{x1},{y1} {x1},{y2 - height} {x2},{y2}" if column < row.column else f"{x1},{y1} {x2},{y2}"
            lit = " lit" if row.fresh else ""
            paths.append(f'<polyline class="wire{lit}" points="{points}"/>')
    return "".join(paths)


def name_tag(name: str, row: Row) -> str:
    """
    Draw one branch name on a row: HEAD's (filled, after "HEAD"), a plain one, a fresh one or one taken off.

    Parameters
    ----------
    name : str
        The branch.
    row : Row
        Its row.

    Returns
    -------
    str
        The tag's HTML.
    """
    fresh = " fresh" if name in row.fresh_names else ""
    if name in row.gone:
        return f'<span class="gone"><s class="tag fresh">{name}</s> taken off</span>'
    if name == row.head:
        lit = " fresh" if fresh or row.fresh_head else ""
        return f'<span class="head{lit}" title="HEAD: you are here">HEAD &#9654;</span><span class="tag on{fresh}">{name}</span>'
    return f'<span class="tag{fresh}">{name}</span>'


def chain(rows: list[Row], height: int = ROW, label: str = "") -> str:
    """
    Draw a chain, newest commit at the top, as the guide's chain picture does.

    Parameters
    ----------
    rows : list[Row]
        Its rows.
    height : int
        One row's height.
    label : str
        What a screen reader hears for the whole picture.

    Returns
    -------
    str
        The chain's HTML.
    """
    columns = max(row.column for row in rows) + 1
    width = columns * COLUMN
    body = []
    for at, row in enumerate(rows):
        if not row.hash:
            body.append(f'<li class="row link" style="height:{height}px"></li>')
            continue
        cap = "cap" + (" fresh" if row.fresh else "") + (" ring" if row.ring else "") + (" faint" if row.faint else "")
        names = "".join(name_tag(name, row) for name in row.names)
        mark = f'<span class="mark">{row.mark}</span>' if row.mark else ""
        note = f'<span class="note">{row.note}</span>' if row.note else ""
        body.append(
            f'<li class="row{" faint" if row.faint else ""}" style="height:{height}px">'
            f'<span class="{cap}" style="left:{row.column * COLUMN + COLUMN // 2 - 8}px;top:{at * height + height // 2 - 8}px"></span>'
            f'<span class="body" style="margin-left:{width + 6}px"><span class="hash">{row.hash}</span>{names}'
            f'<em class="subj">{row.subject}</em>{mark}{note}</span></li>'
        )
    svg = f'<svg class="wires" width="{width}" height="{len(rows) * height}" aria-hidden="true">{wires(rows, height)}</svg>'
    return f'<div class="chain" role="img" aria-label="{html.escape(label)}">{svg}<ol>{"".join(body)}</ol></div>'


def folder(files: list[str], fresh: tuple[str, ...] = (), left: tuple[str, ...] = (), note: str = "") -> str:
    """
    Draw the working folder's row under a chain: its files, a fresh one lit, one that left struck through.

    Parameters
    ----------
    files : list[str]
        The files, in ls order.
    fresh : tuple[str, ...]
        Files the command brought.
    left : tuple[str, ...]
        Files the command took away.
    note : str
        A short word after the files.

    Returns
    -------
    str
        The row's HTML.
    """
    chips = "".join(
        f'<span class="file{" fresh" if name in fresh else ""}{" left" if name in left else ""}">{name}</span>'
        for name in files
    )
    tail = f'<span class="fnote">{note}</span>' if note else ""
    return f'<div class="folder"><b>Working folder (workshop)</b>{chips}{tail}</div>'


def frame(step: str, caption: str, *pictures: str, kind: str = "") -> str:
    """
    One frame of a card's picture: its step label, a caption, and the pictures.

    Parameters
    ----------
    step : str
        "Before", "After", "1", ...
    caption : str
        One sentence.
    *pictures : str
        The chain, folder, terminal or editor HTML.
    kind : str
        An extra class: "refused" frames have a red edge.

    Returns
    -------
    str
        The frame's HTML.
    """
    return f'<figure class="frame {kind}"><figcaption><span class="step">{step}</span> {caption}</figcaption>{"".join(pictures)}</figure>'


def frames(*items: str, wide: bool = False, between: str = "then") -> str:
    """Lay frames side by side (stacked on a phone), with a "then" arrow, or the word "or", between them."""
    joined = (
        f'<span class="{between}" aria-hidden="true"></span>' if between == "then" else '<span class="or">or</span>'
    ).join(items)
    return f'<div class="frames{" wide" if wide else ""}">{joined}</div>'


def facts(*pairs: tuple[str, str]) -> str:
    """Give the "changed" and "same" list under a picture: (kind, words) with kind "new" or "same"."""
    words = {"new": "Changed", "same": "Same"}
    items = "".join(f'<li class="{kind}"><span class="fk">{words[kind]}</span> {text}</li>' for kind, text in pairs)
    return f'<ul class="facts">{items}</ul>'


def card(anchor: str, command: str, what: str, picture: str, prints: str, mistake: str, older: str = "") -> str:
    """
    One command's card, as the field guide would show it.

    Parameters
    ----------
    anchor : str
        The card's id.
    command : str
        The command, as its heading.
    what : str
        What it does, in one sentence.
    picture : str
        The visual explanation.
    prints : str
        What real git printed.
    mistake : str
        The common beginner mistake.
    older : str
        The older form of the command, if any.

    Returns
    -------
    str
        The card's HTML.
    """
    chip = f'<span class="older">older form: <code>{older}</code></span>' if older else ""
    return (
        f'<article class="card" id="{anchor}"><header class="ch"><h2><code>{command}</code></h2>{chip}</header>'
        f'<p class="what">{what}</p><div class="visual">{picture}</div>'
        + (f"<section><h3>What git prints</h3>{prints}</section>" if prints else "")
        + f"<section><h3>Common mistake</h3>{mistake}</section></article>"
    )


def subpart(title: str, body: str) -> str:
    """Give a folded part of a card, closed until the reader opens it."""
    return f'<details class="sub"><summary>{title}</summary>{body}</details>'


START = Row("4ba118d", "Start the project")


def plot(**kw: object) -> Row:
    """Give Plot the route, on Start the project."""
    return Row("e9db21e", "Plot the route", parents=["4ba118d"], **kw)


def probe(**kw: object) -> Row:
    """Give Ready the probe, on Plot the route."""
    return Row("e6af58d", "Ready the probe", parents=["e9db21e"], **kw)


def fill(**kw: object) -> Row:
    """Give Fill the tanks, on Plot the route."""
    return Row("776847b", "Fill the tanks", parents=["e9db21e"], **kw)


def merged(**kw: object) -> Row:
    """Give the merge commit: Fill the tanks first, Ready the probe second."""
    return Row("75119fc", "Merge branch 'scout'", parents=["776847b", "e6af58d"], **kw)


def link() -> Row:
    """Give a connector row of git's drawing (a fork or a join line): no commit."""
    return Row()


BRANCH = card(
    "branch",
    "git branch &lt;name&gt;",
    "Puts a new name tag on the commit you are on. Nothing else moves.",
    frames(
        frame(
            "Before",
            "One name, <code>main</code>, and <code>HEAD</code> on it.",
            chain([plot(names=["main"], head="main"), START], label="Plot the route has main, with HEAD on main."),
            folder(["notes.txt", "route.txt"]),
        ),
        frame(
            "After <code>git branch scout</code>",
            "A second tag on the <em>same</em> commit.",
            chain(
                [plot(names=["main", "scout"], head="main", fresh_names=("scout",)), START],
                label="Plot the route has main, with HEAD, and the new name scout.",
            ),
            folder(["notes.txt", "route.txt"], note="unchanged"),
            '<p class="gloss"><code>HEAD</code> is on <code>main</code>, not on <code>scout</code>.</p>',
        ),
    )
    + facts(
        ("new", "one name, <code>scout</code>, on <em>Plot the route</em>"),
        (
            "same",
            "no new commit; <code>HEAD</code> stays on <code>main</code>; the working folder keeps the same files",
        ),
    ),
    term("branch", look=("* main", "(HEAD -> main, scout)")),
    "<p>Expecting to be on the new branch now. <code>git branch scout</code> only makes the name: the <code>*</code> in "
    "<code>git branch</code> is still on <code>main</code>. To go there, <code>git switch scout</code>, or do both at once with "
    "<code>git switch -c scout</code>.</p>",
)

SWITCH = card(
    "switch",
    "git switch &lt;branch&gt;",
    "Moves <code>HEAD</code> onto another name tag, and the working folder changes to show that commit's files.",
    frames(
        frame(
            "1 Before",
            "<code>HEAD</code> is on <code>main</code>. <code>scout</code> is one commit further on.",
            chain(
                [probe(names=["scout"]), plot(names=["main"], head="main"), START],
                label="Ready the probe has scout. Plot the route has main, with HEAD.",
            ),
            folder(["notes.txt", "route.txt"]),
        ),
        frame(
            "2 <code>git switch scout</code>",
            "<code>HEAD</code> hops to <code>scout</code>. The folder follows: <code>probe.txt</code> appears.",
            chain(
                [
                    probe(names=["scout"], head="scout", fresh_head=True),
                    plot(names=["main"]),
                    START,
                ],
                label="HEAD is now on scout, on Ready the probe.",
            ),
            folder(["notes.txt", "probe.txt", "route.txt"], fresh=("probe.txt",)),
        ),
        frame(
            "3 <code>git switch main</code>",
            "Back again: <code>probe.txt</code> leaves the folder. It is safe in <em>Ready the probe</em>.",
            chain(
                [probe(names=["scout"]), plot(names=["main"], head="main", fresh_head=True), START],
                label="HEAD is back on main, on Plot the route.",
            ),
            folder(["notes.txt", "probe.txt", "route.txt"], left=("probe.txt",), note="probe.txt: in scout's commit"),
        ),
        wide=True,
    )
    + facts(
        ("new", "where <code>HEAD</code> is, and the files in the working folder"),
        ("same", "every commit and every name tag"),
    ),
    term("switch", "switch-back", look=("probe.txt", "(HEAD -> scout)"))
    + subpart(
        "When you have edits you have not committed",
        frames(
            frame(
                "Comes along",
                "An edit to a file both branches hold the same way comes with you. git lists it with <code>M</code>.",
                term("switch-carry", look=("M\tnotes.txt",)),
            ),
            frame(
                "Refused",
                "An edit to a file the other branch holds differently would be overwritten, so git stops and moves nothing.",
                term("switch-refused", refused=("Aborting",)),
                '<p class="gloss">"stash" is a way to set edits aside for later; you will not need it yet.</p>',
                kind="refused",
            ),
            between="or",
        ),
    ),
    "<p>Switching with edits the other branch would overwrite: git refuses (above). Commit them, or undo them, first. The older form "
    "<code>git checkout scout</code> does the same switch:</p>" + term("checkout"),
    older="git checkout &lt;branch&gt;",
)


SWITCH_C = card(
    "switch-c",
    "git switch -c &lt;branch&gt;",
    "Makes a new name tag where you are and moves <code>HEAD</code> onto it, in one step. <code>-c</code> means create.",
    '<div class="sum"><span class="part"><code>git branch lights</code><small>a new tag</small></span><span class="op">+</span>'
    '<span class="part"><code>git switch lights</code><small><code>HEAD</code> hops onto it</small></span><span class="op">=</span>'
    '<span class="part all"><code>git switch -c lights</code><small>both at once</small></span></div>'
    + frames(
        frame(
            "Before",
            "<code>HEAD</code> on <code>main</code>.",
            chain([plot(names=["main"], head="main"), START], label="Plot the route has main, with HEAD."),
            folder(["notes.txt", "route.txt"]),
        ),
        frame(
            "After <code>git switch -c lights</code>",
            "A new tag, and <code>HEAD</code> already on it. <code>main</code> stays.",
            chain(
                [plot(names=["lights", "main"], head="lights", fresh_names=("lights",)), START],
                label="Plot the route has lights, with HEAD, and main.",
            ),
            folder(["notes.txt", "route.txt"], note="unchanged"),
        ),
    )
    + facts(
        ("new", "a name, <code>lights</code>, and <code>HEAD</code> on it"),
        ("same", "no new commit; the working folder, edits not yet committed included"),
    ),
    frames(
        frame("Today's form", "", term("switch-c", look=("(HEAD -> lights, main)",))),
        frame("The older form", "Same result, same words.", term("checkout-b")),
    ),
    "<p>Leaving out <code>-c</code> for a branch that does not exist yet: git cannot find the name and changes nothing.</p>"
    + term("switch-missing"),
    older="git checkout -b &lt;branch&gt;",
)

BRANCH_D = card(
    "branch-d",
    "git branch -d &lt;branch&gt;",
    "Takes a name tag off. The commits stay. Git refuses while the branch you are on does not hold that branch's commits yet.",
    frames(
        frame(
            "Before",
            "After the merge, <code>main</code> holds <code>scout</code>'s commits.",
            chain(
                [probe(names=["main", "scout"], head="main"), plot(), START],
                label="Ready the probe has main, with HEAD, and scout.",
            ),
        ),
        frame(
            "After <code>git branch -d scout</code>",
            "The tag is gone. The commit stays: <code>main</code> still leads to it.",
            chain(
                [probe(names=["main", "scout"], head="main", gone=("scout",)), plot(), START],
                label="Ready the probe has main, with HEAD; scout taken off.",
            ),
        ),
    )
    + facts(("new", "one name less"), ("same", "every commit, <code>HEAD</code>, the working folder"))
    + term("branch-d", look=("Deleted branch scout (was e6af58d).",))
    + subpart(
        "When git refuses",
        frames(
            frame(
                "Not merged",
                "git compares with the branch you are on. <code>main</code> does not hold <em>Ready the probe</em>, so git keeps the name.",
                chain(
                    [
                        fill(names=["main"], head="main"),
                        probe(column=1, names=["scout"], ring=True, note="not in main"),
                        plot(),
                        START,
                    ],
                    label="Fill the tanks has main with HEAD. Ready the probe, on a side line, has scout and is not in main.",
                ),
                term("branch-d-refused", refused=("not fully merged",)),
                kind="refused",
            ),
            frame(
                "You are on it",
                "<code>HEAD</code> is on <code>scout</code>. Switch to another branch first.",
                chain(
                    [probe(names=["scout"], head="scout"), plot(names=["main"]), START],
                    label="Ready the probe has scout, with HEAD on it.",
                ),
                term("branch-d-here", refused=("cannot delete branch 'scout'",)),
                '<p class="gloss">"used by worktree" means: it is the branch of the folder you are working in.</p>',
                kind="refused",
            ),
            between="or",
        ),
    ),
    "",
    "<p>Thinking <code>-d</code> deletes the branch's commits: it takes off a name only. Reaching for <code>-D</code> because git refused: "
    "<code>-D</code> forces it, and a commit no name leads to drops out of <code>git log</code>.</p>",
)


MERGE = card(
    "merge",
    "git merge &lt;branch&gt;",
    "Brings another branch's commits into the branch you are on. Switch to the branch that receives them first.",
    subpart(
        "Only <code>scout</code> moved on: a fast-forward",
        frames(
            frame(
                "Before",
                "<code>main</code> is behind <code>scout</code> on the same line.",
                chain(
                    [probe(names=["scout"]), plot(names=["main"], head="main"), START],
                    label="Ready the probe has scout. Plot the route has main, with HEAD.",
                ),
                folder(["notes.txt", "route.txt"]),
            ),
            frame(
                "After <code>git merge scout</code>",
                "No new commit: <code>main</code>'s tag just slides up to <code>scout</code>'s commit.",
                chain(
                    [probe(names=["main", "scout"], head="main", fresh_names=("main",)), plot(), START],
                    label="Ready the probe has main, with HEAD, and scout.",
                ),
                folder(["notes.txt", "probe.txt", "route.txt"], fresh=("probe.txt",)),
            ),
        )
        + term("merge-ff", look=("Fast-forward",)),
    )
    + subpart(
        "Both moved on: a merge commit",
        frames(
            frame(
                "Before",
                "The line forks: <code>main</code> and <code>scout</code> each have a commit the other lacks.",
                chain(
                    [fill(names=["main"], head="main"), probe(column=1, names=["scout"]), plot(), START],
                    label="Fill the tanks has main with HEAD; Ready the probe, on a side line, has scout.",
                ),
                folder(["fuel.txt", "notes.txt", "route.txt"]),
            ),
            frame(
                "After <code>git merge scout</code>",
                "A new commit, the <b>merge commit</b>, with <b>two parents</b> (the two commits it joins). <code>main</code> climbs onto it; <code>scout</code> stays.",
                chain(
                    [
                        merged(names=["main"], head="main", fresh=True, fresh_names=("main",), mark="merge commit"),
                        probe(column=1, names=["scout"]),
                        fill(),
                        plot(),
                        START,
                    ],
                    label="A merge commit with two parents, Fill the tanks and Ready the probe, has main with HEAD. scout stays on Ready the probe.",
                ),
                folder(["fuel.txt", "notes.txt", "probe.txt", "route.txt"], fresh=("probe.txt",)),
            ),
        )
        + term(
            "merge-commit",
            look=("Merge made by the 'ort' strategy.", "*   75119fc (HEAD -> main) Merge branch 'scout'"),
        ),
    ),
    "",
    "<p>Running the merge from the wrong branch: <code>git merge scout</code> brings <code>scout</code> into the branch <code>HEAD</code> is on. "
    "On <code>scout</code>, it would move <code>scout</code>, not <code>main</code>. And a merge never deletes the other branch: "
    "<code>scout</code>'s tag stays where it was.</p>",
)

EDITOR = (
    '<pre class="editor"><span class="ebar">.git/MERGE_MSG</span>'
    + "\n".join(
        f'<span class="look">{html.escape(line)}</span>'
        if at == 0
        else f'<span class="ecomment">{html.escape(line)}</span>'
        for at, line in enumerate(transcript("merge-editor").rstrip("\n").split("\n"))
    )
    + "</pre>"
)

MERGE_NO_EDIT = card(
    "merge-no-edit",
    "git merge --no-edit &lt;branch&gt;",
    'Makes the merge commit (the new commit with two parents, see <a href="#merge"><code>git merge</code></a>) with the message git prepared, without opening an editor to ask you for one.',
    '<table class="ways"><tr><th><code>git merge scout</code></th><td>On your own computer, git opens this message in your editor '
    "and waits until you save and close it. In the game no editor ever opens.</td></tr>"
    "<tr><th><code>git merge --no-edit scout</code></th><td>git keeps the message as it is, and no editor opens anywhere.</td></tr></table>"
    + frames(
        frame(
            "The message git prepares",
            "Lines starting with <code>#</code> are dropped. The rest is the message; its first line is the subject.",
            EDITOR,
        ),
        frame(
            "The merge commit",
            "Either way, the same commit, with that message.",
            chain(
                [
                    merged(names=["main"], head="main", fresh=True, mark="merge commit"),
                    probe(column=1, names=["scout"]),
                    fill(),
                    plot(),
                    START,
                ],
                label="The merge commit, Merge branch 'scout', has main with HEAD.",
            ),
        ),
    )
    + facts(
        (
            "same",
            "a fast-forward makes no commit, so it never asks for a message, with or without <code>--no-edit</code>",
        )
    ),
    term("merge-no-edit", look=("Merge branch 'scout'",)),
    "<p>Getting stuck in the editor outside the game: in vim, type <code>:wq</code> and Enter to keep the message. Next time, "
    "<code>--no-edit</code> skips it. After a conflict, <code>git commit --no-edit</code> finishes the merge the same way.</p>",
)


def decoder(scene: str, rows: list[Row], label: str) -> str:
    """
    Draw git's drawing beside the chain, line for line: row n of the picture is line n of the output.

    Parameters
    ----------
    scene : str
        The recorded scene; its first line is the command.
    rows : list[Row]
        The chain's rows, one per output line.
    label : str
        The chain's label for a screen reader.

    Returns
    -------
    str
        The pair's HTML.
    """
    lines = transcript(scene).rstrip("\n").split("\n")
    command, output = lines[0], lines[1:]
    if len(output) != len(rows):
        raise ValueError(f"{scene}: {len(output)} lines, {len(rows)} rows")
    text = "".join(f'<span class="dl">{html.escape(line) or " "}</span>' for line in output)
    return (
        f'<div class="decoder"><div><pre class="term dterm"><span class="dl dcmd"><span class="pr">$ </span><span class="cmd">{html.escape(command[2:])}</span></span>{text}</pre></div>'
        f'<div class="dpic"><div class="dspacer"></div>{chain(rows, height=28, label=label)}</div></div>'
    )


KEY = (
    '<dl class="key">'
    "<dt><code>*</code></dt><dd>a commit (a square in the picture)</dd>"
    "<dt><code>|</code></dt><dd>a line going down to the parent</dd>"
    "<dt><code>/</code> <code>\\</code></dt><dd>a line forking off or joining back</dd>"
    "<dt><code>(HEAD -&gt; main)</code></dt><dd>you are here, on the tag <code>main</code></dd>"
    "<dt><code>(scout)</code></dt><dd>a name tag on that commit</dd>"
    "</dl>"
)

GRAPH = card(
    "graph",
    "git log --oneline --graph --all",
    "Draws every branch's commits as a tree, one line each, with the names on them.",
    '<p class="gloss">Newest at the top, in git\'s drawing and in the picture.</p>'
    + decoder(
        "graph",
        [fill(names=["main"], head="main"), probe(column=1, names=["scout"]), link(), plot(), START],
        "The fork: Fill the tanks has main with HEAD; Ready the probe has scout; both on Plot the route.",
    )
    + KEY
    + subpart(
        "After the merge",
        decoder(
            "merge-graph",
            [
                merged(names=["main"], head="main", mark="merge commit"),
                link(),
                probe(column=1, names=["scout"], note="scout's line"),
                fill(note="main's line"),
                link(),
                plot(),
                START,
            ],
            "The merge commit has main with HEAD; its two lines go down to Ready the probe and Fill the tanks.",
        ),
    )
    + subpart(
        "Without <code>--all</code>",
        frames(
            frame(
                "Only what <code>HEAD</code> leads back to",
                "<em>Ready the probe</em> is missing from the output. It is not gone: <code>git log</code> was not asked for it. The picture draws it faintly.",
                term("graph-no-all"),
                chain(
                    [
                        fill(names=["main"], head="main"),
                        probe(column=1, names=["scout"], faint=True, note="not shown"),
                        plot(),
                        START,
                    ],
                    label="Fill the tanks has main with HEAD. Ready the probe, on scout, is faint: the output leaves it out.",
                ),
            )
        ),
    ),
    "<p>The output is the picture: each line above is pasted from git.</p>",
    "<p>Leaving out <code>--all</code>: <code>git log</code> shows only what your branch leads back to, so another branch's commits seem to be missing.</p>",
)


CSS = (Path(__file__).parent / "storyboard.css").read_text()

INTRO = """
<section class="intro box">
<p>Seven command cards for the field guide, each with a picture of what changes. Every terminal on this page is real git 2.43
output, recorded by <code>record.sh</code> in one small story: <em>Start the project</em>, <em>Plot the route</em>, then a
branch <code>scout</code> with <em>Ready the probe</em>, and <em>Fill the tanks</em> on <code>main</code>. The hashes are the
same on every card.</p>
<div class="legend">
<span><span class="cap inline"></span> a commit (yours: violet)</span>
<span><span class="tag">scout</span> a name tag (a branch)</span>
<span><span class="head">HEAD &#9654;</span><span class="tag on">main</span> you are here</span>
<span><span class="cap inline fresh"></span> <span class="tag fresh">gold</span> what the command changed</span>
<span><em>Plot the route</em> a commit's subject, in italics</span>
<span><span class="folder chipf"><b>Working folder (workshop)</b></span> your files on disk</span>
<span><span class="look-chip">look here</span> matches the picture</span>
<span><span class="no-chip">refused</span> git said no</span>
</div>
</section>
"""

NAV = (
    '<nav class="toc" aria-label="Cards">'
    + "".join(
        f'<a href="#{a}"><code>{t}</code></a>'
        for a, t in [
            ("branch", "git branch"),
            ("switch", "git switch"),
            ("switch-c", "git switch -c"),
            ("branch-d", "git branch -d"),
            ("merge", "git merge"),
            ("merge-no-edit", "git merge --no-edit"),
            ("graph", "git log --graph --all"),
        ]
    )
    + "</nav>"
)


def page() -> str:
    """Give the whole storyboard page."""
    version = (RUNS / "version.txt").read_text().strip()
    cards = "".join([BRANCH, SWITCH, SWITCH_C, BRANCH_D, MERGE, MERGE_NO_EDIT, GRAPH])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Branch and merge cards</title>
<style>
{CSS}</style>
</head>
<body>
<header class="top"><span class="no">Field guide</span><span class="title">Branch and merge cards: storyboard</span><span class="chip">{version}</span>
<button type="button" class="theme" onclick="const r=document.documentElement;r.dataset.theme=r.dataset.theme==='dark'?'light':'dark'">Light / dark</button></header>
<main>
{INTRO}
{NAV}
{cards}
</main>
</body>
</html>
"""


TARGET.write_text(page())
