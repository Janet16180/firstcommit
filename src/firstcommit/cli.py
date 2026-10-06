"""
The command line: parse arguments, call `firstcommit.game` or the web server, print the result.

Every rule lives in `firstcommit.game`; this module only checks its arguments, calls one game
function per command and lays the result out for a terminal.
"""

import argparse
import os
import re
import subprocess
import sys
import textwrap
from collections.abc import Callable

from termlab.web import terminal

from firstcommit import game, gitcmd, save
from firstcommit.markup import Block, Span

DEFAULT_PORT = 8820
PORT = re.compile(r"[0-9]{1,5}")
MAX_PORT = 65535
WIDTH = 88
INDENT = "  "
NO_LEVEL = "No level is in progress. Start one in the page: run `firstcommit` and open the link it prints."
DAMAGED = "Run `firstcommit reset --yes` to start over (this erases your progress)."


def main(argv: list[str] | None = None) -> int:
    """
    Run the command line.

    Parameters
    ----------
    argv : list[str] | None
        Arguments after the program name, or None for ``sys.argv``.

    Returns
    -------
    int
        Exit status: 0 for success, 1 when the command could not do its job (an unsolved check,
        no level in progress, a damaged save), 2 for bad arguments or a bad game home.
    """
    args = build_parser().parse_args(argv)
    run: Callable[[argparse.Namespace], int] = args.run
    home_problem = None if run is doctor else _home_problem()
    if home_problem is not None:
        print(home_problem, file=sys.stderr)
        status = 2
    else:
        status = _run(run, args)
    return status


def _home_problem() -> str | None:
    """
    Check the game home before a command uses it, so a bad one fails before anything starts.

    Returns
    -------
    str | None
        Why the home cannot be used, or None.
    """
    problem = None
    try:
        save.home()
    except ValueError as error:
        problem = str(error)
    return problem


def _run(run: Callable[[argparse.Namespace], int], args: argparse.Namespace) -> int:
    """
    Run one command, turning the game's expected refusals into a message.

    Parameters
    ----------
    run : Callable[[argparse.Namespace], int]
        The command's function.
    args : argparse.Namespace
        Its arguments.

    Returns
    -------
    int
        The command's exit status, or 1 if no level is in progress or the save is damaged.
    """
    try:
        status = run(args)
    except game.NotPlayingError:
        print(NO_LEVEL)
        status = 1
    except save.SaveError as error:
        print(f"{error}\n{DAMAGED}", file=sys.stderr)
        status = 1
    return status


def build_parser() -> argparse.ArgumentParser:
    """
    Describe the commands.

    Returns
    -------
    argparse.ArgumentParser
        The parser; each command sets ``run`` to its function, and no command means ``serve``.
    """
    parser = argparse.ArgumentParser(prog="firstcommit", description="First Commit: learn Git by playing, in your browser and your terminal.")
    commands = parser.add_subparsers(title="commands", metavar="<command>")
    serve_parser = commands.add_parser("serve", help="play in your browser (the default)")
    serve_parser.add_argument("--port", type=port_number, default=DEFAULT_PORT, help=f"local port of the page (default {DEFAULT_PORT})")
    serve_parser.set_defaults(run=serve)
    commands.add_parser("shell", help="open a shell where git uses the game's settings").set_defaults(run=shell)
    commands.add_parser("status", help="show your XP, rank and progress").set_defaults(run=status)
    check_parser = commands.add_parser("check", help="check the level in progress")
    check_parser.add_argument("answer", nargs="?", help="your answer, for a level that asks a question")
    check_parser.set_defaults(run=check)
    commands.add_parser("hint", help="reveal the next hint (it lowers the XP the level pays)").set_defaults(run=hint)
    reset_parser = commands.add_parser("reset", help="erase all progress and start over")
    reset_parser.add_argument("--yes", action="store_true", help="really erase everything")
    reset_parser.set_defaults(run=reset)
    commands.add_parser("doctor", help="check that this machine can run the game").set_defaults(run=doctor)
    parser.set_defaults(run=serve, port=DEFAULT_PORT)
    return parser


def port_number(text: str) -> int:
    """
    Read a port number from the command line.

    Parameters
    ----------
    text : str
        The argument.

    Returns
    -------
    int
        The port.

    Raises
    ------
    argparse.ArgumentTypeError
        If it is not a whole number from 1 to `MAX_PORT`.
    """
    if not PORT.fullmatch(text) or not 1 <= int(text) <= MAX_PORT:
        raise argparse.ArgumentTypeError(f"the port must be a whole number from 1 to {MAX_PORT}, not {text!r}")
    return int(text)


def serve(args: argparse.Namespace) -> int:
    """
    Serve the page until Ctrl-C.

    Parameters
    ----------
    args : argparse.Namespace
        ``port``.

    Returns
    -------
    int
        The server's exit status.
    """
    # Imported here so the other commands never load the web server. The ignore is for the
    # branch where web/routes.py is not merged yet; it can go once it is.
    from firstcommit.web import routes  # type: ignore[attr-defined, unused-ignore]

    exit_status: int = routes.serve(args.port)
    return exit_status


def shell(args: argparse.Namespace) -> int:
    """
    Open the game's shell in the terminal folder, with git kept to the game's settings.

    Parameters
    ----------
    args : argparse.Namespace
        No arguments.

    Returns
    -------
    int
        The shell's exit status.
    """
    folder = game.terminal_folder()
    env = {**terminal.player_env(os.environ), **gitcmd.isolation(save.home()), "PWD": folder}
    print("This is the game's shell: git here uses the game's own settings, never yours. Type `exit` to leave.")
    return subprocess.run([terminal.shell_path(env)], cwd=folder, env=env, check=False).returncode


def status(args: argparse.Namespace) -> int:
    """
    Print XP, rank, the level in progress, the cards to review and every chapter's levels.

    Parameters
    ----------
    args : argparse.Namespace
        No arguments.

    Returns
    -------
    int
        0.
    """
    dashboard = game.status()
    rank = dashboard["rank"]
    following = "" if rank["next_title"] is None else f" (next: {rank['next_title']} at {rank['next_at']} XP)"
    print(f"{INDENT}{dashboard['xp']} XP, rank {rank['title']}{following}")
    titles = {entry["id"]: entry["title"] for chapter in dashboard["chapters"] for entry in chapter["levels"]}
    active = dashboard["active"]
    if active is not None:
        quest = "" if active["steps"] == 0 else f", step {min(active['step'] + 1, active['steps'])} of {active['steps']}"
        print(f"{INDENT}In progress: {titles[active['level']]} ({active['level']}){quest}, hints {active['hints']} of {active['hints_total']}")
    print(f"{INDENT}Cards to review: {dashboard['cards_due']}")
    for chapter in dashboard["chapters"]:
        print(f"\n{INDENT}{chapter['title']} ({chapter['id']})")
        for entry in chapter["levels"]:
            print(f"{INDENT * 2}[{'x' if entry['done'] else ' '}] {entry['title']} ({entry['id']}), {entry['xp']} XP")
    return 0


def check(args: argparse.Namespace) -> int:
    """
    Check the level in progress and print the verdict, and the payout and debrief once solved.

    Parameters
    ----------
    args : argparse.Namespace
        ``answer``, or None.

    Returns
    -------
    int
        0 if the level is solved, else 1.
    """
    result = game.check(args.answer, auto=False)
    print(render(result["message"]))
    payout = result["payout"]
    if payout is not None:
        again = "" if payout["first_time"] else " (you had solved it before)"
        print(f"\n{INDENT}Solved! +{payout['xp']} XP{again}")
        if payout["rank_after"] != payout["rank_before"]:
            print(f"{INDENT}New rank: {payout['rank_after']}")
    if result["debrief"] is not None:
        print("\n" + render(result["debrief"]))
    return 0 if result["solved"] else 1


def hint(args: argparse.Namespace) -> int:
    """
    Reveal and print the next hint of the level in progress.

    Parameters
    ----------
    args : argparse.Namespace
        No arguments.

    Returns
    -------
    int
        0.
    """
    view = game.hint()
    print(f"{INDENT}Hint {view['used']} of {view['total']} (it cost {view['cost']} XP):\n")
    print(render(view["hint"]))
    return 0


def reset(args: argparse.Namespace) -> int:
    """
    Erase all progress, if asked with ``--yes``.

    Parameters
    ----------
    args : argparse.Namespace
        ``yes``.

    Returns
    -------
    int
        0 once erased, 1 without ``--yes``.
    """
    if args.yes:
        game.reset()
        print(f"{INDENT}All progress is erased.")
    else:
        print(f"{INDENT}This erases all your progress and practice repositories. To do it, run `firstcommit reset --yes`.")
    return 0 if args.yes else 1


def doctor(args: argparse.Namespace) -> int:
    """
    Print one line per check of this machine.

    Parameters
    ----------
    args : argparse.Namespace
        No arguments.

    Returns
    -------
    int
        0 if every check passed, else 1.
    """
    report = game.doctor()
    for item in report:
        print(f"{'ok' if item['ok'] else 'FAIL':4} {item['check']:6} {item['detail']}")
    return 0 if all(item["ok"] for item in report) else 1


def render(blocks: list[Block]) -> str:
    """
    Lay text blocks out for a terminal.

    Parameters
    ----------
    blocks : list[Block]
        Parsed text.

    Returns
    -------
    str
        Paragraphs and bullets wrapped at `WIDTH`, verbatim blocks indented as written, code
        spans between backticks, and a blank line between blocks.
    """
    parts = []
    for block in blocks:
        if block["kind"] == "code":
            parts.append(textwrap.indent(block["text"], INDENT * 2))
        elif block["kind"] == "para":
            parts.append(_wrap(block["spans"], INDENT, INDENT))
        else:
            parts.append("\n".join(_wrap(item, INDENT + "- ", INDENT + "  ") for item in block["items"]))
    return "\n\n".join(parts)


def _wrap(spans: list[Span], first: str, rest: str) -> str:
    """
    Wrap a paragraph or bullet.

    Parameters
    ----------
    spans : list[Span]
        Its spans.
    first : str
        Prefix of the first line.
    rest : str
        Prefix of the other lines.

    Returns
    -------
    str
        The wrapped lines; long words such as hashes are never broken.
    """
    text = "".join(f"`{span['text']}`" if span["code"] else span["text"] for span in spans)
    return textwrap.fill(text, width=WIDTH, initial_indent=first, subsequent_indent=rest, break_long_words=False, break_on_hyphens=False)
