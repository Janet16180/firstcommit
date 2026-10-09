import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import get_args

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from firstcommit import changes, gitcmd, playground, records, repomap, save
from firstcommit.lab import Lab
from playground_helpers import (
    COMMIT_NOTES,
    NOTES,
    PEOPLE,
    PLAYER,
    SHARE_NOTES,
    bar,
    clone,
    conflicted_lab,
    new_lab,
    presses,
    target,
    views,
)


def test_setup_gives_github_one_commit_with_both_files_and_each_person_a_clone_of_it() -> None:
    with new_lab() as lab:
        seen = views(lab)
        assert seen["github"]["bare"]
        assert [commit["subject"] for commit in seen["github"]["commits"]] == ["Start the project"]
        first = seen["github"]["head"]
        for person in PEOPLE:
            assert (seen[person]["branch"], seen[person]["head"], target(seen[person], "origin/main")) == ("main", first, first)
            assert [file["path"] for file in seen[person]["files"]] == ["README.md", "notes.txt"]
        assert (lab.project / NOTES).read_text() == "Notes\n"
        assert (lab.project / "README.md").read_text() == "# Project\n"


def test_each_clone_reaches_github_by_a_path_from_its_top_folder() -> None:
    with new_lab() as lab:
        for person in PEOPLE:
            folder = clone(lab, person)
            assert gitcmd.output(folder, "remote", "get-url", "origin").strip() == lab.github_url(folder)


def test_each_clone_shows_only_main_and_origin_main_with_no_origin_head_even_after_a_fetch_and_a_pull() -> None:
    with new_lab() as lab:
        for person in PEOPLE:
            assert gitcmd.output(clone(lab, person), "log", "-1", "--format=%D").strip() == "HEAD -> main, origin/main"
        presses(lab, "alex", *SHARE_NOTES)
        presses(lab, "you", "fetch", "pull")
        for person in PEOPLE:
            assert gitcmd.output(clone(lab, person), "for-each-ref", "--format=%(refname)", "refs/remotes").split() == ["refs/remotes/origin/main"]
        assert gitcmd.output(lab.project, "log", "-1", "--format=%D").strip() == "HEAD -> main, origin/main"


def test_each_clone_tells_a_newer_git_never_to_bring_origin_head_back_on_a_fetch() -> None:
    with new_lab() as lab:
        for person in PEOPLE:
            assert gitcmd.output(clone(lab, person), "config", "--local", "remote.origin.followRemoteHEAD").strip() == "never"


def test_githubs_first_commit_has_a_fixed_date_so_it_is_the_same_commit_in_every_playground() -> None:
    with new_lab() as lab:
        assert gitcmd.output(lab.github, "log", "-1", "--format=%aI %cI", "main").split() == [playground.START_DATE] * 2


def push_line(lab: Lab, line: str) -> subprocess.CompletedProcess[str]:
    """
    Run one line in your clone as the player's shell would, hooks and all.

    Parameters
    ----------
    lab : Lab
        The lab.
    line : str
        The line.

    Returns
    -------
    subprocess.CompletedProcess[str]
        What ran, its output and its errors.
    """
    env = {**gitcmd.shell_environment(os.environ, save.home()), "HOME": str(save.home())}
    return subprocess.run(["bash", "--noprofile", "--norc", "-c", line], cwd=lab.project, env=env, capture_output=True, text=True, check=True)


def test_alex_runs_their_lines_inside_the_push_that_brings_the_awaited_file_once_and_silently() -> None:
    with new_lab() as lab:
        playground.on_push(lab, "notes.txt", "Notes\nYou: line 2\n", ["git pull -q", "echo x > alex.txt", "git add alex.txt", 'git commit -q -m "Alex adds a file"', "git push -q"])
        presses(lab, "you", "edit:README.md", "add:README.md", "commit")
        push_line(lab, "git push -q")
        assert gitcmd.output(lab.teammate, "log", "-1", "--format=%s").strip() == "Start the project"
        presses(lab, "you", *COMMIT_NOTES)
        pushed = push_line(lab, "git push")
        assert "remote:" not in pushed.stdout + pushed.stderr
        assert gitcmd.output(lab.github, "log", "-1", "--format=%an %s", "main").strip() == "Alex Alex adds a file"
        presses(lab, "you", "edit:README.md", "add:README.md", "commit")
        push_line(lab, "git pull -q --no-rebase --no-edit && git push -q")
        assert gitcmd.output(lab.github, "log", "-1", "--format=%an", "main").strip() == PLAYER.name


def test_only_alexs_clone_has_an_identity_of_its_own() -> None:
    with new_lab() as lab:
        assert gitcmd.run(lab.project, "config", "--local", "user.name").returncode == 1
        assert gitcmd.output(lab.teammate, "config", "--local", "user.name").strip() == playground.ALEX.name
        assert gitcmd.output(lab.teammate, "config", "--local", "user.email").strip() == playground.ALEX.email


def test_your_commits_carry_the_players_name_and_alexs_carry_alexs() -> None:
    with new_lab() as lab:
        presses(lab, "you", *COMMIT_NOTES)
        presses(lab, "alex", *COMMIT_NOTES)
        assert repomap.snapshot(lab.project)["commits"][0]["author"] == PLAYER.name
        assert repomap.snapshot(lab.teammate)["commits"][0]["author"] == playground.ALEX.name


def test_a_commit_without_the_players_identity_fails_as_git_does() -> None:
    with new_lab(identity=False) as lab:
        [*_, commit] = presses(lab, "you", *COMMIT_NOTES)
        assert commit["status"] == 128
        assert "Please tell me who you are." in commit["output"]
        assert repomap.snapshot(lab.project)["commits"][0]["subject"] == "Start the project"


def test_the_playground_starts_on_main_whatever_default_branch_the_player_set() -> None:
    save.ensure_gitconfig(gitcmd.BASE_CONFIG)
    gitcmd.output(save.home(), "config", "--global", "init.defaultBranch", "trunk")
    with new_lab() as lab:
        seen = views(lab)
        assert [seen[name]["branch"] for name in ("github", *PEOPLE)] == ["main", "main", "main"]


def test_every_button_id_is_a_kind_or_a_file_kind_with_a_playground_file() -> None:
    kinds = set(get_args(records.Button))
    assert {button.partition(":")[0] for button in playground.BUTTON_IDS} == kinds
    assert {button.partition(":")[2] for button in playground.BUTTON_IDS if ":" in button} == set(playground.FILES)


def test_both_people_see_the_same_bar_in_the_same_order() -> None:
    with new_lab() as lab:
        expected = ["status", "commit", "push", "fetch", "pull", "edit:README.md", "add:README.md", "edit:notes.txt", "add:notes.txt"]
        assert list(bar(lab, "you")) == list(bar(lab, "alex")) == expected


def test_each_button_says_its_label_and_the_exact_line_it_runs_now() -> None:
    with new_lab() as lab:
        shown = bar(lab, "alex")
        assert [(view["label"], view["line"], view["off"]) for view in shown.values()] == [
            ("git status", "git status", ""),
            ("git commit", 'git commit -m "Save my work"', ""),
            ("git push", "git push", ""),
            ("git fetch", "git fetch", ""),
            ("git pull", "git pull", ""),
            ("Edit README.md", 'echo "Alex: line 2" >> README.md', ""),
            ("git add README.md", "git add README.md", ""),
            ("Edit notes.txt", 'echo "Alex: line 2" >> notes.txt', ""),
            ("git add notes.txt", "git add notes.txt", ""),
        ]


def test_the_commit_line_names_what_is_staged() -> None:
    with new_lab() as lab:
        presses(lab, "you", "edit:notes.txt", "add:notes.txt")
        assert bar(lab, "you")["commit"]["line"] == 'git commit -m "Update notes.txt"'
        presses(lab, "you", "edit:README.md", "add:README.md")
        assert bar(lab, "you")["commit"]["line"] == 'git commit -m "Update README.md and notes.txt"'
        gitcmd.output(lab.project, "rm", "-q", "--cached", "README.md")
        assert bar(lab, "you")["commit"]["line"] == 'git commit -m "Update notes.txt and delete README.md"'
        (lab.project / "other.txt").write_text("other\n")
        gitcmd.output(lab.project, "add", "other.txt")
        assert bar(lab, "you")["commit"]["line"] == 'git commit -m "Save my work"'


def test_edit_appends_the_persons_next_numbered_line() -> None:
    with new_lab() as lab:
        first, second = presses(lab, "you", "edit:notes.txt", "edit:notes.txt")
        assert (first["command"], first["status"], first["output"]) == ('echo "You: line 2" >> notes.txt', 0, "")
        assert second["command"] == 'echo "You: line 3" >> notes.txt'
        assert (lab.project / NOTES).read_text() == "Notes\nYou: line 2\nYou: line 3\n"
        assert (lab.teammate / NOTES).read_text() == "Notes\n"


@pytest.mark.parametrize("content", [b"Notes\n", b"Notes", b"", None, b"one\ntwo\n\nfour\n"], ids=["line", "no-newline", "empty", "missing", "blank-line"])
def test_edit_writes_the_same_bytes_and_mode_as_its_line_typed_in_bash(content: bytes | None) -> None:
    with new_lab() as lab:
        notes = lab.project / NOTES
        notes.unlink()
        if content is not None:
            notes.write_bytes(content)
        twin = lab.root / "twin"
        twin.mkdir()
        if content is not None:
            (twin / NOTES).write_bytes(content)
        [press] = presses(lab, "you", "edit:notes.txt")
        subprocess.run(["bash", "--norc", "--noprofile", "-c", press["command"]], cwd=twin, check=True)
        assert notes.read_bytes() == (twin / NOTES).read_bytes()
        assert stat.S_IMODE(notes.stat().st_mode) == stat.S_IMODE((twin / NOTES).stat().st_mode)


def test_a_git_button_shows_its_output_as_the_terminal_does() -> None:
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
        presses(lab, "alex", *COMMIT_NOTES)
        after = views(lab)
        assert (after["you"], after["github"]) == (before["you"], before["github"])
        assert after["alex"] != before["alex"]


def test_a_push_after_the_other_persons_push_is_refused_in_gits_words_and_moves_nothing() -> None:
    with new_lab() as lab:
        presses(lab, "alex", *SHARE_NOTES)
        presses(lab, "you", "edit:README.md", "add:README.md", "commit")
        before = views(lab)
        [press] = presses(lab, "you", "push")
        assert press["status"] == 1
        assert " ! [rejected]        main -> main (fetch first)\n" in press["output"]
        assert "error: failed to push some refs to '../github.com/moonbase/project.git'\n" in press["output"]
        assert views(lab) == before


def test_a_plain_pull_on_diverged_branches_fetches_then_asks_how_to_reconcile_them() -> None:
    with new_lab() as lab:
        presses(lab, "alex", *SHARE_NOTES)
        presses(lab, "you", "edit:README.md", "add:README.md", "commit")
        mine = repomap.snapshot(lab.project)["head"]
        [press] = presses(lab, "you", "pull")
        assert press["status"] == 128
        assert "fatal: Need to specify how to reconcile divergent branches.\n" in press["output"]
        after = repomap.snapshot(lab.project)
        assert (after["head"], target(after, "origin/main")) == (mine, target(repomap.snapshot(lab.github)))


def test_pull_without_rebase_shows_only_while_the_branches_have_diverged() -> None:
    with new_lab() as lab:
        assert "pull-no-rebase" not in bar(lab, "you")
        presses(lab, "alex", *SHARE_NOTES)
        presses(lab, "you", "edit:README.md", "add:README.md", "commit")
        assert "pull-no-rebase" not in bar(lab, "you")
        presses(lab, "you", "fetch")
        assert bar(lab, "you")["pull-no-rebase"]["line"] == "git pull --no-rebase --no-edit"
        [merge, push] = presses(lab, "you", "pull-no-rebase", "push")
        assert (merge["status"], push["status"]) == (0, 0), merge["output"] + push["output"]
        assert repomap.snapshot(lab.project)["commits"][0]["subject"] == "Merge branch 'main' of ../github.com/moonbase/project"
        assert "pull-no-rebase" not in bar(lab, "you")


def test_once_the_player_chooses_merge_a_plain_pull_merges_without_waiting_for_an_editor() -> None:
    with new_lab() as lab:
        gitcmd.output(lab.project, "config", "--global", "pull.rebase", "false")
        presses(lab, "alex", *SHARE_NOTES)
        presses(lab, "you", "edit:README.md", "add:README.md", "commit")
        [pull, push] = presses(lab, "you", "pull", "push")
        assert (pull["status"], push["status"]) == (0, 0), pull["output"] + push["output"]
        assert len(repomap.snapshot(lab.github)["commits"][0]["parents"]) == 2


def test_during_a_paused_merge_the_bar_adds_abort_and_the_conflicted_files_buttons() -> None:
    with new_lab() as lab:
        pull = conflicted_lab(lab)
        assert pull["status"] == 1
        assert "CONFLICT (content): Merge conflict in notes.txt\n" in pull["output"]
        shown = bar(lab, "you")
        assert list(shown)[-4:] == ["merge-abort", "keep-ours:notes.txt", "keep-theirs:notes.txt", "pull-no-rebase"]
        assert [(shown[key]["label"], shown[key]["line"]) for key in ("keep-ours:notes.txt", "keep-theirs:notes.txt", "commit")] == [
            ("Keep mine in notes.txt", "git restore --ours notes.txt"),
            ("Keep theirs in notes.txt", "git restore --theirs notes.txt"),
            ("git commit", "git commit --no-edit"),
        ]
        assert "merge-abort" not in bar(lab, "alex")


def test_keeping_one_side_adding_it_and_committing_finishes_the_merge_with_gits_message() -> None:
    with new_lab() as lab:
        conflicted_lab(lab)
        keep, add, commit, push = presses(lab, "you", "keep-theirs:notes.txt", "add:notes.txt", "commit", "push")
        assert [keep["status"], add["status"], commit["status"], push["status"]] == [0, 0, 0, 0], commit["output"]
        assert (lab.project / NOTES).read_text() == "Notes\nAlex: line 2\n"
        head = repomap.snapshot(lab.project)["commits"][0]
        assert (head["subject"], len(head["parents"])) == ("Merge branch 'main' of ../github.com/moonbase/project", 2)
        assert "merge-abort" not in bar(lab, "you")


def test_aborting_the_merge_puts_your_files_and_branch_back() -> None:
    with new_lab() as lab:
        presses(lab, "alex", *SHARE_NOTES)
        presses(lab, "you", *COMMIT_NOTES)
        before = repomap.snapshot(lab.project)
        presses(lab, "you", "pull-no-rebase")
        [abort] = presses(lab, "you", "merge-abort")
        after = repomap.snapshot(lab.project)
        assert (abort["status"], after["operation"], after["head"], after["files"]) == (0, None, before["head"], before["files"])


def test_a_conditional_button_pressed_out_of_its_state_runs_and_git_answers() -> None:
    with new_lab() as lab:
        [abort] = presses(lab, "you", "merge-abort")
        assert abort["status"] == 128
        assert "fatal: There is no merge to abort (MERGE_HEAD missing).\n" in abort["output"]



def test_the_folder_facts_say_what_each_button_file_is_and_its_lines() -> None:
    with new_lab() as lab:
        assert playground.folder_facts(lab, "you") == {
            "usable": True,
            "kinds": {"README.md": "file", "notes.txt": "file"},
            "lines": {"README.md": 1, "notes.txt": 1},
            "marked": [],
            "locked": False,
        }
        (lab.project / NOTES).unlink()
        (lab.project / "README.md").write_text("one\ntwo")
        facts = playground.folder_facts(lab, "you")
        assert (facts["kinds"], facts["lines"]) == ({"README.md": "file", "notes.txt": "missing"}, {"README.md": 1})


def test_the_folder_facts_mark_a_file_holding_conflict_markers_and_a_left_lock() -> None:
    with new_lab() as lab:
        conflicted_lab(lab)
        (lab.project / ".git" / "index.lock").write_text("")
        facts = playground.folder_facts(lab, "you")
        assert (facts["marked"], facts["locked"]) == (["notes.txt"], True)


def test_a_gone_clone_has_no_usable_folder_and_no_facts_about_its_files() -> None:
    with new_lab() as lab:
        shutil.rmtree(lab.teammate)
        assert playground.folder_facts(lab, "alex") == {"usable": False, "kinds": {}, "lines": {}, "marked": [], "locked": False}


def test_edit_numbers_its_line_by_the_line_breaks_in_the_file() -> None:
    with new_lab() as lab:
        (lab.project / NOTES).write_text("Notes")
        assert bar(lab, "you")["edit:notes.txt"]["line"] == 'echo "You: line 1" >> notes.txt'


def test_the_config_facts_say_whether_an_identity_a_remote_and_an_upstream_are_set() -> None:
    with new_lab() as lab:
        snap = repomap.snapshot(lab.project)
        assert playground.config_facts(lab, "you", snap) == {"name": True, "email": True, "remote": True, "upstream": True}
        gitcmd.output(lab.project, "remote", "remove", "origin")
        assert playground.config_facts(lab, "you", repomap.snapshot(lab.project)) == {"name": True, "email": True, "remote": False, "upstream": False}


def test_the_config_facts_say_when_the_player_has_no_identity_while_alex_has_one() -> None:
    with new_lab(identity=False) as lab:
        facts = playground.config_facts(lab, "you", repomap.snapshot(lab.project))
        assert (facts["name"], facts["email"]) == (False, False)
        assert playground.config_facts(lab, "alex", repomap.snapshot(lab.teammate))["name"]


def test_the_facts_of_a_press_hold_github_only_where_there_is_one() -> None:
    with new_lab() as lab:
        seen = views(lab)
        facts = playground.facts(lab, "alex", seen["alex"], seen["github"])
        assert facts["github"] == seen["github"]
        assert facts["folder"] == playground.folder_facts(lab, "alex")
        assert facts["config"] == playground.config_facts(lab, "alex", seen["alex"])
        assert playground.facts(lab, "alex", seen["alex"], repomap.snapshot(lab.root / "nowhere"))["github"] is None


GONE = "The project folder is gone: start the playground again."


@pytest.mark.parametrize("person", PEOPLE)
@pytest.mark.parametrize("linked", [False, True], ids=["gone", "link"])
def test_every_button_is_off_and_runs_nothing_when_the_clone_is_gone_or_a_link(person: records.Who, linked: bool) -> None:
    with new_lab() as lab:
        folder = clone(lab, person)
        moved = folder.with_name("moved")
        folder.rename(moved)
        if linked:
            folder.symlink_to(moved, target_is_directory=True)
        assert {view["off"] for view in bar(lab, person).values()} == {GONE}
        with pytest.raises(playground.ButtonOffError, match=GONE):
            playground.press(lab, person, "edit:notes.txt")
        with pytest.raises(playground.ButtonOffError, match=GONE):
            playground.press(lab, person, "status")
        assert (moved / NOTES).read_text() == "Notes\n"


def test_a_clone_whose_parent_folder_is_a_link_is_off() -> None:
    with new_lab() as lab:
        outside = Path(tempfile.mkdtemp(dir=save.home()))
        shutil.move(lab.teammate.parent, outside / "teammate")
        lab.teammate.parent.symlink_to(outside / "teammate", target_is_directory=True)
        assert {view["off"] for view in bar(lab, "alex").values()} == {GONE}


@pytest.mark.parametrize("kind", ["folder", "link"])
def test_edit_is_off_when_its_file_is_not_a_plain_file(kind: str) -> None:
    with new_lab() as lab:
        notes = lab.project / NOTES
        notes.unlink()
        outside = lab.root / "outside.txt"
        outside.write_text("keep me\n")
        notes.mkdir() if kind == "folder" else notes.symlink_to(outside)
        shown = bar(lab, "you")
        assert shown["edit:notes.txt"]["off"] == "notes.txt is not a plain file any more."
        assert shown["edit:README.md"]["off"] == shown["add:notes.txt"]["off"] == ""
        with pytest.raises(playground.ButtonOffError, match="notes.txt is not a plain file any more."):
            playground.press(lab, "you", "edit:notes.txt")
        assert outside.read_text() == "keep me\n"



@pytest.mark.parametrize("button", ["edit:../outside.txt", "edit:", "add:other.txt", "rebase", "edit"])
def test_a_button_the_playground_does_not_have_is_refused_before_anything_runs(button: str) -> None:
    with new_lab() as lab:
        before = views(lab)
        with pytest.raises(KeyError, match="no button"):
            playground.press(lab, "you", button)
        assert not (lab.root / "outside.txt").exists()
        assert views(lab) == before


def test_no_press_output_names_the_players_folders() -> None:
    with new_lab() as lab:
        done = [*presses(lab, "alex", *SHARE_NOTES), *presses(lab, "you", *COMMIT_NOTES, "push", "pull-no-rebase")]
        assert [str(save.home()) in press["output"] for press in done] == [False] * len(done)


Step = tuple[records.Who, str]
ONE_PRESS = st.tuples(st.sampled_from(PEOPLE), st.sampled_from(sorted(playground.BUTTON_IDS))).map(lambda step: [step])
A_COMMIT = st.tuples(st.sampled_from(PEOPLE), st.sampled_from(playground.FILES)).map(lambda pick: [(pick[0], f"edit:{pick[1]}"), (pick[0], f"add:{pick[1]}"), (pick[0], "commit")])
A_SHARE = A_COMMIT.map(lambda steps: [*steps, (steps[0][0], "push")])
A_CATCH_UP = st.tuples(st.sampled_from(PEOPLE), st.sampled_from(["pull", "pull-no-rebase"])).map(lambda pull: [pull, (pull[0], "push")])
A_RESOLVE = st.tuples(st.sampled_from(PEOPLE), st.sampled_from(["keep-ours", "keep-theirs"])).map(
    lambda pick: [(pick[0], f"{pick[1]}:notes.txt"), (pick[0], "add:notes.txt"), (pick[0], "commit"), (pick[0], "push")]
)
MOVES = st.one_of(ONE_PRESS, A_COMMIT, A_SHARE, A_CATCH_UP, A_RESOLVE)
STEPS = st.lists(MOVES, min_size=1, max_size=8).map(lambda moves: [step for move in moves for step in move])
"""
Press sequences built from moves: one press; a person's edit, add and commit of one file, with or without a push; a pull then a push; or keeping one side of ``notes.txt``, adding, committing and pushing.

Single presses alone almost never reach a commit, let alone a refused push, a merge or a conflict.
"""

CONFLICT_AND_RESOLVE: list[Step] = [
    *[("alex", button) for button in SHARE_NOTES],
    *[("you", button) for button in SHARE_NOTES],
    ("you", "pull"),
    ("you", "pull-no-rebase"),
    ("you", "keep-ours:notes.txt"),
    ("you", "add:notes.txt"),
    ("you", "commit"),
    ("you", "push"),
    ("alex", "pull"),
    ("alex", "status"),
]
"""Alex shares first; your push is refused, your plain pull stops, the pull that merges stops on a conflict, you keep your side, finish and push, and Alex catches up."""


@pytest.mark.slow
@settings(max_examples=25, deadline=None)
@given(steps=STEPS)
@example(steps=CONFLICT_AND_RESOLVE)
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
            kind = button.partition(":")[0]
            if kind != "push" or press["status"] != 0:
                assert now["github"] == seen["github"], context
            if kind == "status" or (kind in ("add", "commit", "push") and press["status"] != 0):
                assert now[person] == seen[person], context
            if kind == "edit":
                assert (now[person]["head"], now[person]["refs"]) == (seen[person]["head"], seen[person]["refs"]), context
            if kind == "push" and press["status"] == 0:
                assert target(now["github"]) == now[person]["head"] == target(now[person], "origin/main"), context
                assert "came from the remote" not in told, context
            if kind in ("fetch", "pull", "pull-no-rebase") and seen[person]["operation"] is None:
                assert target(now[person], "origin/main") == target(now["github"]), context
            if kind == "commit" and press["status"] == 0:
                assert {event["kind"] for event in events} & {"commit-created", "merge-commit-created"}, context
            shown = bar(lab, person)
            assert set(shown) <= playground.BUTTON_IDS, context
            assert ("merge-abort" in shown) == (now[person]["operation"] == "merge"), context
            assert all("\n" not in view["line"] and view["off"] == "" for view in shown.values()), context
            seen = now


def test_the_stand_in_github_keeps_a_reflog_so_a_forced_push_can_be_seen_and_undone() -> None:
    with new_lab() as lab:
        assert gitcmd.output(lab.github, "config", "core.logAllRefUpdates").strip() == "true"
        before = gitcmd.output(lab.github, "rev-parse", "main").strip()
        you = clone(lab, "you")
        gitcmd.output(you, "commit", "--quiet", "--allow-empty", "-m", "Empty")
        gitcmd.output(you, "push", "--quiet")
        gitcmd.output(you, "push", "--quiet", "--force", "origin", f"{before}:main")
        assert gitcmd.output(lab.github, "rev-parse", "main@{1}").strip() != before
        assert gitcmd.output(lab.github, "rev-parse", "main@{2}").strip() == before


def test_a_level_without_the_playground_builds_the_same_stand_in_github(game_home: Path) -> None:
    lab = Lab(game_home / "labs" / "solo")
    lab.root.mkdir(parents=True)
    playground.setup_github(lab)
    assert gitcmd.output(lab.github, "config", "core.logAllRefUpdates").strip() == "true"
    assert gitcmd.output(lab.github, "symbolic-ref", "HEAD").strip() == "refs/heads/main"
    assert gitcmd.output(lab.github, "rev-parse", "--is-bare-repository").strip() == "true"
