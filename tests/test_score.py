import pytest
from hypothesis import given
from hypothesis import strategies as st

from firstcommit import score

xps = st.integers(min_value=0, max_value=10**6)
level_xps = st.integers(min_value=0, max_value=1000)
hint_counts = st.integers(min_value=0, max_value=10)


def test_a_new_player_starts_at_the_first_rank_with_the_next_one_in_sight() -> None:
    first_floor, first_title = score.RANKS[0]
    next_floor, next_title = score.RANKS[1]
    assert first_floor == 0
    assert score.rank(0) == {"title": first_title, "floor": 0, "next_title": next_title, "next_at": next_floor}


def test_reaching_a_floor_gives_that_rank() -> None:
    floor, title = score.RANKS[3]
    assert score.rank(floor)["title"] == title
    assert score.rank(floor - 1)["title"] == score.RANKS[2][1]


def test_the_top_rank_has_no_next_rank() -> None:
    floor, title = score.RANKS[-1]
    assert score.rank(floor + 10**6) == {"title": title, "floor": floor, "next_title": None, "next_at": None}


def test_ranks_are_between_seven_and_nine_titles_with_rising_floors() -> None:
    floors = [floor for floor, _ in score.RANKS]
    titles = [title for _, title in score.RANKS]
    assert 7 <= len(score.RANKS) <= 9
    assert floors == sorted(set(floors))
    assert len(set(titles)) == len(titles)


@given(xps)
def test_the_rank_floor_is_reached_and_the_next_rank_is_not(xp: int) -> None:
    current = score.rank(xp)
    assert current["floor"] <= xp
    assert current["next_at"] is None or current["next_at"] > xp


def test_a_negative_xp_total_is_a_bug() -> None:
    with pytest.raises(ValueError, match="xp"):
        score.rank(-1)


def test_a_level_solved_without_hints_pays_its_full_xp() -> None:
    assert score.level_reward(200, hints=0, first_time=True) == 200


def test_a_level_solved_with_any_hint_pays_no_xp() -> None:
    assert score.level_reward(100, hints=1, first_time=True) == 0
    assert score.level_reward(300, hints=4, first_time=True) == 0


def test_a_replay_pays_nothing() -> None:
    assert score.level_reward(200, hints=0, first_time=False) == 0


@given(level_xps, hint_counts)
def test_more_hints_never_pay_more(xp: int, hints: int) -> None:
    assert score.level_reward(xp, hints + 1, first_time=True) <= score.level_reward(xp, hints, first_time=True)


@given(level_xps, hint_counts, st.booleans())
def test_a_solve_pays_all_of_the_level_xp_or_nothing(xp: int, hints: int, first_time: bool) -> None:
    assert score.level_reward(xp, hints, first_time) in (0, xp)


def test_the_first_hint_costs_the_whole_reward_and_later_ones_nothing_more() -> None:
    assert score.hint_cost(200, used=1, first_time=True) == 200
    assert score.hint_cost(200, used=2, first_time=True) == 0
    assert score.hint_cost(100, used=4, first_time=True) == 0


def test_a_hint_costs_nothing_on_a_replay() -> None:
    assert score.hint_cost(200, used=1, first_time=False) == 0


@given(level_xps, st.integers(min_value=1, max_value=10))
def test_the_hint_costs_add_up_to_what_the_hints_took(xp: int, used: int) -> None:
    costs = sum(score.hint_cost(xp, number, first_time=True) for number in range(1, used + 1))
    assert costs == xp - score.level_reward(xp, used, first_time=True)


def test_a_negative_hint_count_is_a_bug() -> None:
    with pytest.raises(ValueError, match="hints"):
        score.level_reward(100, hints=-1, first_time=True)


def test_a_right_answer_on_a_new_or_due_card_pays_by_card_level() -> None:
    assert [score.card_score(level, correct=True, pays=True, streak=0).xp for level in (1, 2, 3)] == [10, 20, 30]


def test_a_card_that_is_not_due_pays_nothing() -> None:
    assert score.card_score(3, correct=True, pays=False, streak=0).xp == 0


def test_a_wrong_answer_pays_nothing_and_breaks_the_streak() -> None:
    result = score.card_score(1, correct=False, pays=True, streak=4)
    assert (result.xp, result.streak, result.bonus) == (0, 0, 0)


def answer_run(answers: list[tuple[bool, bool]]) -> list[score.CardScore]:
    """
    Score a run of answers to level-1 cards, carrying the streak from one to the next.

    Parameters
    ----------
    answers : list[tuple[bool, bool]]
        ``(correct, pays)`` for each answer, in order.

    Returns
    -------
    list[score.CardScore]
        The score of each answer.
    """
    results = []
    streak = 0
    for correct, pays in answers:
        result = score.card_score(1, correct=correct, pays=pays, streak=streak)
        streak = result.streak
        results.append(result)
    return results


def test_every_fifth_paying_right_answer_in_a_row_earns_the_streak_bonus() -> None:
    results = answer_run([(True, True)] * 10)
    assert [result.bonus for result in results] == [0, 0, 0, 0, 25, 0, 0, 0, 0, 25]
    assert results[-1].streak == 10


def test_right_answers_on_cards_that_are_not_due_break_the_streak() -> None:
    results = answer_run([(True, True)] * 4 + [(True, False)] + [(True, True)] * 4)
    assert results[4].streak == 0
    assert all(result.bonus == 0 for result in results)


@given(st.lists(st.tuples(st.booleans(), st.booleans()), max_size=40))
def test_only_paying_right_answers_ever_earn_xp_or_a_bonus(answers: list[tuple[bool, bool]]) -> None:
    for (correct, pays), result in zip(answers, answer_run(answers), strict=True):
        if not (correct and pays):
            assert (result.xp, result.bonus, result.streak) == (0, 0, 0)


def test_a_level_played_without_hints_within_par_and_three_keeps_three_stars() -> None:
    assert score.stars(hints=0, commands=7, par=4) == 3


def test_a_hint_costs_one_star_however_many_are_used() -> None:
    assert score.stars(hints=1, commands=0, par=4) == 2
    assert score.stars(hints=3, commands=0, par=4) == 2


def test_typing_more_than_par_and_three_lines_costs_one_star() -> None:
    assert score.stars(hints=0, commands=8, par=4) == 2
    assert score.stars(hints=0, commands=80, par=4) == 2


def test_hints_and_too_many_lines_together_leave_one_star() -> None:
    assert score.stars(hints=2, commands=9, par=4) == 1


@given(hint_counts, st.integers(min_value=0, max_value=1000), st.integers(min_value=1, max_value=50))
def test_stars_are_always_between_one_and_three(hints: int, commands: int, par: int) -> None:
    assert 1 <= score.stars(hints, commands, par) <= 3


def test_a_negative_hint_or_line_count_is_a_bug() -> None:
    with pytest.raises(ValueError, match="commands"):
        score.stars(hints=0, commands=-1, par=4)
