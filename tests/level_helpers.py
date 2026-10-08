"""Helpers the tests of single levels share (``tests/levels``): start a level's lab, type in it, find its steps and rules."""

from types import ModuleType

from firstcommit import kit, reactions, runner


def started(module: ModuleType) -> tuple[kit.Lab, kit.State]:
    """
    Start a level's lab, as the game does, without running its events.

    Parameters
    ----------
    module : ModuleType
        The level's module.

    Returns
    -------
    tuple[kit.Lab, kit.State]
        The lab and the level's state.
    """
    entry = runner.load(module)
    state = runner.start_lab(entry)
    return runner.lab_of(entry.id), state


def arrived(module: ModuleType) -> tuple[kit.Lab, kit.State]:
    """
    Start a level's lab and run the events of its first look, as the game does when the page opens it.

    Parameters
    ----------
    module : ModuleType
        The level's module.

    Returns
    -------
    tuple[kit.Lab, kit.State]
        The lab and the level's state.
    """
    lab, state = started(module)
    reached(module, lab, state, "")
    return lab, state


def reached(module: ModuleType, lab: kit.Lab, state: kit.State, goal: str) -> None:
    """
    Run a level's events for a goal just reached, as the game does.

    Parameters
    ----------
    module : ModuleType
        The level's module.
    lab : kit.Lab
        Its lab.
    state : kit.State
        Its state.
    goal : str
        The goal's id, or empty for the first look.
    """
    for event in runner.load(module).events:
        if event.goal == goal:
            event.run(lab, state)


def typed_in(lab: kit.Lab, *lines: str) -> list[kit.Command]:
    """
    Type lines in the lab's project folder, as the player would.

    Parameters
    ----------
    lab : kit.Lab
        The lab.
    *lines : str
        The lines, in order.

    Returns
    -------
    list[kit.Command]
        Each line with its real exit status.
    """
    return [kit.type_line(lab.project, line) for line in lines]


def watch(module: ModuleType, step_id: str) -> kit.WatchStep:
    """
    Give one of a level's watch steps.

    Parameters
    ----------
    module : ModuleType
        The level's module.
    step_id : str
        The step's id.

    Returns
    -------
    kit.WatchStep
        The step.
    """
    found = next(step for step in module.QUEST if step.id == step_id)
    assert isinstance(found, kit.WatchStep)
    return found


def reaction(
    module: ModuleType, line: kit.Command, kinds: set[str], repository: bool, staged: bool, remote: bool = True, ignored: bool = False
) -> kit.ReactionRule | None:
    """
    Find what Rama says about a line in a level: its own rules first, then the shared ones.

    Parameters
    ----------
    module : ModuleType
        The level's module.
    line : kit.Command
        The typed line and its status.
    kinds : set[str]
        The kinds of change it made.
    repository : bool
        Whether a repository is there afterwards.
    staged : bool
        Whether anything is staged afterwards.
    remote : bool
        Whether the repository names a remote afterwards; most levels' repositories do.
    ignored : bool
        Whether the working folder holds ignored files afterwards; most levels' folders do not.

    Returns
    -------
    kit.ReactionRule | None
        The rule that speaks, or None.
    """
    return reactions.react(line, kinds, repository, staged, (*runner.load(module).reactions, *reactions.RULES), remote=remote, ignored=ignored)
