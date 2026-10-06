import pytest

from firstcommit import demos, guide
from firstcommit.repomap import Snapshot


def drawn(section: str) -> tuple[Snapshot, Snapshot, list[str]]:
    """
    Run one guide figure's lesson on real git.

    Parameters
    ----------
    section : str
        The guide section the figure illustrates.

    Returns
    -------
    tuple[Snapshot, Snapshot, list[str]]
        The repository before and after the change, and the commands the change ran.
    """
    figure = next(figure for figure in guide.FIGURES if figure.section == section)
    before, after = demos.frames(guide.lesson(figure))
    return before["map"], after["map"], [line["command"] for line in after["transcript"]]


def ref(snapshot: Snapshot, name: str) -> str:
    """
    Give the commit a branch, tag or remote-tracking branch points at.

    Parameters
    ----------
    snapshot : Snapshot
        A repository.
    name : str
        The label, such as ``main``, ``v1`` or ``origin/main``.

    Returns
    -------
    str
        Its commit's hash.
    """
    return next(label["target"] for label in snapshot["refs"] if label["name"] == name)


def tip(snapshot: Snapshot) -> str:
    """
    Give the commit HEAD is on.

    Parameters
    ----------
    snapshot : Snapshot
        A repository with at least one commit.

    Returns
    -------
    str
        HEAD's commit's hash.
    """
    head = snapshot["head"]
    assert head is not None
    return head


def parents(snapshot: Snapshot, hash_: str) -> list[str]:
    """
    Give a commit's parents.

    Parameters
    ----------
    snapshot : Snapshot
        A repository that holds the commit.
    hash_ : str
        The commit.

    Returns
    -------
    list[str]
        Its parents' hashes, first parent first.
    """
    return next(commit["parents"] for commit in snapshot["commits"] if commit["hash"] == hash_)


def test_there_is_one_figure_for_each_picture_the_guide_draws() -> None:
    sections = [figure.section for figure in guide.FIGURES]
    assert sections == ["commit", "parents", "branch", "now", "detached", "merge", "tag", "archive", "seen"]


@pytest.mark.parametrize("section", [figure.section for figure in guide.FIGURES])
def test_each_figure_changes_its_repository_with_one_git_command(section: str) -> None:
    before, after, commands = drawn(section)
    assert len([command for command in commands if command.startswith("git ")]) == 1
    assert before != after


def test_the_first_commit_makes_the_first_save_point() -> None:
    before, after, _ = drawn("commit")
    assert before["commits"] == []
    assert len(after["commits"]) == 1
    assert (after["branch"], after["head"]) == ("main", ref(after, "main"))


def test_a_new_commit_is_drawn_on_top_of_its_parent() -> None:
    before, after, _ = drawn("parents")
    assert parents(after, tip(after)) == [tip(before)]


def test_committing_on_a_branch_moves_only_that_branch() -> None:
    before, after, _ = drawn("branch")
    assert after["branch"] == "idea"
    assert parents(after, ref(after, "idea")) == [ref(before, "idea")]
    assert ref(after, "main") == ref(before, "main")


def test_switching_moves_head_to_the_other_branch_and_no_commit() -> None:
    before, after, _ = drawn("now")
    assert (before["branch"], after["branch"]) == ("main", "idea")
    assert after["head"] == ref(after, "idea")
    assert before["commits"] == after["commits"]
    assert before["refs"] == after["refs"]


def test_a_commit_on_a_detached_head_moves_no_branch() -> None:
    before, after, _ = drawn("detached")
    assert before["branch"] is None and after["branch"] is None
    assert parents(after, tip(after)) == [tip(before)]
    assert ref(after, "main") == ref(before, "main")


def test_a_merge_commit_joins_the_two_timelines() -> None:
    before, after, _ = drawn("merge")
    assert parents(after, tip(after)) == [ref(before, "main"), ref(before, "idea")]
    assert ref(after, "idea") == ref(before, "idea")


def test_a_tag_stays_put_when_main_moves_on() -> None:
    before, after, _ = drawn("tag")
    assert ref(after, "v1") == ref(before, "v1") == ref(before, "main")
    assert parents(after, ref(after, "main")) == [ref(before, "main")]


def test_the_archive_figure_draws_the_practice_copy_whose_main_a_push_moved() -> None:
    before, after, commands = drawn("archive")
    assert before["bare"] and after["bare"]
    assert parents(after, ref(after, "main")) == [ref(before, "main")]
    assert "git push" in commands


def test_fetching_moves_origin_main_and_leaves_main_and_head_where_they_were() -> None:
    before, after, _ = drawn("seen")
    assert ref(after, "origin/main") != ref(before, "origin/main")
    assert parents(after, ref(after, "origin/main")) == [ref(before, "origin/main")]
    assert (ref(after, "main"), after["head"]) == (ref(before, "main"), before["head"])


def test_a_figure_is_a_two_slide_lesson_the_game_can_run() -> None:
    figure = guide.FIGURES[0]
    slides = guide.lesson(figure)
    assert [slide.id for slide in slides] == ["commit-before", "commit-after"]
    assert [slide.run for slide in slides] == [figure.setup, figure.change]
