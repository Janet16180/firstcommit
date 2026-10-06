import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import get_args

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from firstcommit import changes, gitcmd, playground, records, repomap, save
from firstcommit.lab import Lab

PEOPLE: tuple[records.Who, ...] = get_args(records.Who)
BUTTONS: tuple[records.Button, ...] = get_args(records.Button)
SHARE: tuple[records.Button, ...] = ("edit", "add", "commit", "push")
"""The presses that share a change: edit, stage, commit and push it."""


@contextmanager
def new_lab() -> Iterator[Lab]:
    """
    Make a lab with the playground set up, in the game's labs folder, and remove it afterwards.

    Yields
    ------
    Lab
        The lab: GitHub and both clones.
    """
    save.ensure_gitconfig(gitcmd.BASE_CONFIG)
    labs = save.home() / save.LABS_FOLDER
    labs.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=labs) as root:
        lab = Lab(Path(root))
        playground.setup(lab)
        yield lab


def clone(lab: Lab, person: records.Who) -> Path:
    """
    Find a person's clone.

    Parameters
    ----------
    lab : Lab
        The lab.
    person : records.Who
        Who.

    Returns
    -------
    Path
        Their working folder.
    """
    return lab.project if person == "you" else lab.teammate


def views(lab: Lab) -> dict[str, repomap.Snapshot]:
    """
    Snapshot GitHub and both clones.

    Parameters
    ----------
    lab : Lab
        The lab.

    Returns
    -------
    dict[str, repomap.Snapshot]
        The snapshots by ``"github"`` and by person.
    """
    return {"github": repomap.snapshot(lab.github), "you": repomap.snapshot(lab.project), "alex": repomap.snapshot(lab.teammate)}


def target(snap: repomap.Snapshot, name: str = "main") -> str | None:
    """
    Find the commit a ref names.

    Parameters
    ----------
    snap : repomap.Snapshot
        The snapshot.
    name : str
        The ref, such as ``main`` or ``origin/main``.

    Returns
    -------
    str | None
        Its commit, or None when the snapshot has no such ref.
    """
    return next((ref["target"] for ref in snap["refs"] if ref["name"] == name), None)


def presses(lab: Lab, person: records.Who, *buttons: records.Button) -> list[records.Press]:
    """
    Press one person's buttons in order.

    Parameters
    ----------
    lab : Lab
        The lab.
    person : records.Who
        Who presses.
    *buttons : records.Button
        The buttons.

    Returns
    -------
    list[records.Press]
        What each press reported.
    """
    return [playground.press(lab, person, button) for button in buttons]


def test_setup_gives_github_one_commit_and_each_person_a_clone_of_it() -> None:
    with new_lab() as lab:
        seen = views(lab)
        assert seen["github"]["bare"]
        assert [commit["subject"] for commit in seen["github"]["commits"]] == ["Add the README"]
        first = seen["github"]["head"]
        for person in PEOPLE:
            assert seen[person]["branch"] == "main"
            assert seen[person]["head"] == first
            assert target(seen[person], "origin/main") == first
            assert [file["path"] for file in seen[person]["files"]] == ["README.md"]


def test_each_person_commits_under_their_own_name_in_their_clone() -> None:
    with new_lab() as lab:
        for person in PEOPLE:
            identity = playground.PEOPLE[person]
            assert gitcmd.output(clone(lab, person), "config", "--local", "user.name").strip() == identity.name
            assert gitcmd.output(clone(lab, person), "config", "--local", "user.email").strip() == identity.email
        presses(lab, "alex", "edit", "add", "commit")
        assert repomap.snapshot(lab.teammate)["commits"][0]["author"] == playground.PEOPLE["alex"].name


def test_both_people_have_the_same_buttons() -> None:
    assert set(playground.BUTTONS) == set(BUTTONS)
    assert all(set(commands) == set(PEOPLE) for commands in playground.BUTTONS.values())


def test_each_person_edits_a_file_of_their_own() -> None:
    with new_lab() as lab:
        presses(lab, "you", "edit")
        presses(lab, "alex", "edit")
        seen = views(lab)
        mine = {file["path"] for file in seen["you"]["files"] if file["folder_change"] == "untracked"}
        theirs = {file["path"] for file in seen["alex"]["files"] if file["folder_change"] == "untracked"}
        assert len(mine) == len(theirs) == 1
        assert mine != theirs


def test_every_button_shows_one_command_a_player_could_type() -> None:
    commands = [command for by_person in playground.BUTTONS.values() for command in by_person.values()]
    assert all(command and "\n" not in command and command == command.strip() for command in commands)
    assert playground.BUTTONS["push"] == {"you": "git push", "alex": "git push"}
    assert playground.BUTTONS["pull"] == {"you": "git pull", "alex": "git pull"}
    assert playground.BUTTONS["pull-no-rebase"] == {"you": "git pull --no-rebase", "alex": "git pull --no-rebase"}


def test_a_press_reports_who_pressed_what_and_what_the_command_printed() -> None:
    with new_lab() as lab:
        [press] = presses(lab, "alex", "status")
        assert press == {
            "person": "alex",
            "button": "status",
            "command": "git status",
            "status": 0,
            "output": "On branch main\nYour branch is up to date with 'origin/main'.\n\nnothing to commit, working tree clean\n",
        }


def test_a_press_changes_only_the_clone_of_the_person_who_pressed() -> None:
    with new_lab() as lab:
        before = views(lab)
        [press] = presses(lab, "alex", "edit")
        after = views(lab)
        assert press["status"] == 0
        assert after["you"] == before["you"]
        assert after["github"] == before["github"]
        assert after["alex"] != before["alex"]


def test_a_push_after_the_other_persons_push_is_refused_in_gits_words_and_moves_nothing() -> None:
    with new_lab() as lab:
        presses(lab, "alex", *SHARE)
        presses(lab, "you", "edit", "add", "commit")
        before = views(lab)
        [press] = presses(lab, "you", "push")
        assert press["status"] == 1
        assert " ! [rejected]        main -> main (fetch first)\n" in press["output"]
        assert "hint: Updates were rejected because the remote contains work that you do not\n" in press["output"]
        assert views(lab) == before


def test_a_plain_pull_on_diverged_branches_fetches_then_asks_how_to_reconcile_them() -> None:
    with new_lab() as lab:
        presses(lab, "alex", *SHARE)
        presses(lab, "you", "edit", "add", "commit")
        mine = repomap.snapshot(lab.project)["head"]
        [press] = presses(lab, "you", "pull")
        assert press["status"] == 128
        assert "fatal: Need to specify how to reconcile divergent branches.\n" in press["output"]
        after = repomap.snapshot(lab.project)
        assert after["head"] == mine
        assert target(after, "origin/main") == target(repomap.snapshot(lab.github))


def test_a_pull_without_rebase_merges_before_the_player_has_chosen_how() -> None:
    with new_lab() as lab:
        presses(lab, "alex", *SHARE)
        presses(lab, "you", "edit", "add", "commit")
        [press] = presses(lab, "you", "pull-no-rebase")
        assert press["status"] == 0, press["output"]
        assert "Merge made by the 'ort' strategy.\n" in press["output"]
        head = repomap.snapshot(lab.project)["commits"][0]
        assert len(head["parents"]) == 2
        assert head["subject"].startswith("Merge branch 'main' of ")


def test_once_the_player_chooses_merge_a_plain_pull_merges_without_waiting_for_an_editor() -> None:
    with new_lab() as lab:
        gitcmd.output(lab.project, "config", "--global", "pull.rebase", "false")
        presses(lab, "alex", *SHARE)
        presses(lab, "you", "edit", "add", "commit")
        [pull, push] = presses(lab, "you", "pull", "push")
        assert pull["status"] == 0, pull["output"]
        assert push["status"] == 0, push["output"]
        assert len(repomap.snapshot(lab.github)["commits"][0]["parents"]) == 2


def test_a_commit_with_nothing_staged_fails_as_git_does() -> None:
    with new_lab() as lab:
        [edit, commit] = presses(lab, "you", "edit", "commit")
        assert edit["status"] == 0
        assert commit["status"] == 1
        assert 'nothing added to commit but untracked files present (use "git add" to track)\n' in commit["output"]


def test_a_press_in_a_clone_the_player_deleted_reports_it_and_runs_nothing_elsewhere() -> None:
    with new_lab() as lab:
        shutil.rmtree(lab.teammate)
        [press] = presses(lab, "alex", "edit")
        assert press["status"] != 0
        assert press["output"].endswith(f"cd: {lab.teammate}: No such file or directory\n")
        assert press["output"].count("\n") == 1


def test_the_playground_starts_on_main_whatever_default_branch_the_player_set() -> None:
    save.ensure_gitconfig(gitcmd.BASE_CONFIG)
    gitcmd.output(save.home(), "config", "--global", "init.defaultBranch", "trunk")
    with new_lab() as lab:
        seen = views(lab)
        assert [seen[name]["branch"] for name in ("github", *PEOPLE)] == ["main", "main", "main"]



def test_each_clone_reaches_github_by_a_path_from_its_top_folder() -> None:
    with new_lab() as lab:
        for person in PEOPLE:
            folder = clone(lab, person)
            assert gitcmd.output(folder, "remote", "get-url", "origin").strip() == lab.github_url(folder)


def test_git_names_github_by_that_path_so_no_output_or_merge_subject_holds_the_players_folders() -> None:
    with new_lab() as lab:
        presses(lab, "alex", *SHARE)
        [*_, refused, merge, push] = presses(lab, "you", *SHARE, "pull-no-rebase", "push")
        [pull] = presses(lab, "alex", "pull")
        assert "error: failed to push some refs to '../github/project.git'\n" in refused["output"]
        assert push["output"].startswith("To ../github/project.git\n")
        assert pull["output"].startswith("From ../../github/project\n")
        assert [str(save.home()) in press["output"] for press in (refused, merge, push, pull)] == [False] * 4
        assert repomap.snapshot(lab.project)["commits"][0]["subject"] == "Merge branch 'main' of ../github/project"


def test_a_clone_reaches_github_from_a_subfolder_too() -> None:
    with new_lab() as lab:
        presses(lab, "alex", *SHARE)
        notes = lab.project / "notes"
        notes.mkdir()
        (notes / "plan.txt").write_text("A plan.\n")
        commands = [("add", "plan.txt"), ("commit", "-m", "Add a plan"), ("push",), ("fetch",), ("pull", "--no-rebase"), ("push",), ("status",)]
        results = [gitcmd.run(notes, *command) for command in commands]
        assert [result.returncode for result in results] == [0, 0, 1, 0, 0, 0, 0], [result.stderr for result in results]
        assert target(repomap.snapshot(lab.github)) == repomap.snapshot(lab.project)["head"]


Step = tuple[records.Who, records.Button]
ONE_PRESS = st.tuples(st.sampled_from(PEOPLE), st.sampled_from(BUTTONS)).map(lambda step: [step])
A_COMMIT = st.sampled_from(PEOPLE).map(lambda person: [(person, button) for button in SHARE[:-1]])
A_SHARE = st.sampled_from(PEOPLE).map(lambda person: [(person, button) for button in SHARE])
A_CATCH_UP = st.tuples(st.sampled_from(PEOPLE), st.sampled_from(["pull", "pull-no-rebase"])).map(lambda pull: [pull, (pull[0], "push")])
MOVES = st.one_of(ONE_PRESS, A_COMMIT, A_SHARE, A_CATCH_UP)
STEPS = st.lists(MOVES, min_size=1, max_size=8).map(lambda moves: [step for move in moves for step in move])
"""
Press sequences built from moves: one press; a person's edit, add and commit, with or without a push; or a pull then a push.

Single presses alone almost never reach a commit, let alone a refused push or a merge.
"""

DIVERGE_AND_MERGE: list[Step] = [
    *[("alex", button) for button in SHARE],
    *[("you", button) for button in SHARE],
    ("you", "pull"),
    ("you", "pull-no-rebase"),
    ("you", "push"),
    ("alex", "pull"),
    ("alex", "status"),
]
"""Alex shares first; your push is refused, your plain pull stops, the pull that merges works, and Alex catches up."""


@pytest.mark.slow
@settings(max_examples=25, deadline=None)
@given(steps=STEPS)
@example(steps=DIVERGE_AND_MERGE)
def test_any_sequence_of_presses_keeps_the_facts_the_figure_draws(steps: list[Step]) -> None:
    with new_lab() as lab:
        seen = views(lab)
        for person, button in steps:
            press = playground.press(lab, person, button)
            now = views(lab)
            other = "alex" if person == "you" else "you"
            events = changes.describe(seen[person], now[person])
            told = " ".join(event["text"] for event in events)
            context = (steps, press, events)
            assert now[other] == seen[other], context
            assert str(save.home()) not in press["output"], context
            for snap in now.values():
                remote = {ref["name"] for ref in snap["refs"] if ref["kind"] == "remote"}
                assert snap["pushed"] == sorted(set(snap["pushed"]) & remote), context
            if button != "push" or press["status"] != 0:
                assert now["github"] == seen["github"], context
            if button == "status" or (button in ("add", "commit", "push") and press["status"] != 0):
                assert now[person] == seen[person], context
            if button == "edit":
                assert (now[person]["head"], now[person]["refs"]) == (seen[person]["head"], seen[person]["refs"]), context
            if button == "push" and press["status"] == 0:
                assert target(now["github"]) == now[person]["head"] == target(now[person], "origin/main"), context
                assert "came from the remote" not in told, context
            if button in ("fetch", "pull", "pull-no-rebase"):
                assert target(now[person], "origin/main") == target(now["github"]), context
            if button == "commit" and press["status"] == 0:
                assert {event["kind"] for event in events} & {"commit-created", "merge-commit-created"}, context
            seen = now
