"""
Tests for the MIFA Scoring Validation Engine.

Covers rank validation, percentage validation, rank-percentage consistency,
the combined validate_all function, the get_ranked_summary sorter,
and edge cases including small student counts and None (unscored) values.
"""

from __future__ import annotations

import pytest
import sys
import os

# Ensure the project root is on the path so we can import scoring_engine.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scoring_engine import (
    validate_ranks,
    validate_percentages,
    validate_rank_percentage_consistency,
    validate_all,
    get_ranked_summary,
)


# ---------------------------------------------------------------------------
# Helpers for building student_score dicts
# ---------------------------------------------------------------------------

def _make_student(
    name: str,
    index: int,
    rank: int | None = None,
    percentage: int | None = None,
    elapsed_seconds: float | None = None,
) -> dict:
    """Convenience factory for student_score dicts."""
    return {
        "student_name": name,
        "student_index": index,
        "rank": rank,
        "percentage": percentage,
        "elapsed_seconds": elapsed_seconds,
    }


def _build_valid_five_student_scores() -> list[dict]:
    """Return a fully valid set of 5 scored students."""
    return [
        _make_student("Alice", 0, rank=1, percentage=100, elapsed_seconds=300.0),
        _make_student("Bob", 1, rank=2, percentage=95, elapsed_seconds=320.0),
        _make_student("Carol", 2, rank=3, percentage=90, elapsed_seconds=310.0),
        _make_student("Dave", 3, rank=4, percentage=85, elapsed_seconds=350.0),
        _make_student("Eve", 4, rank=4, percentage=80, elapsed_seconds=340.0),
    ]


# ===================================================================
# Tests for validate_ranks
# ===================================================================

class TestValidateRanks:
    """Tests for the validate_ranks function."""

    def test_valid_ranking_produces_no_messages(self):
        student_scores = _build_valid_five_student_scores()
        validation_messages = validate_ranks(student_scores)
        assert validation_messages == []

    def test_missing_rank_one_produces_error(self):
        student_scores = [
            _make_student("Alice", 0, rank=2, percentage=100),
            _make_student("Bob", 1, rank=2, percentage=95),
            _make_student("Carol", 2, rank=3, percentage=90),
        ]
        validation_messages = validate_ranks(student_scores)
        assert any("rank 1" in message.lower() for message in validation_messages)

    def test_duplicate_top_three_rank_produces_error(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=1, percentage=95),
            _make_student("Carol", 2, rank=3, percentage=90),
        ]
        validation_messages = validate_ranks(student_scores)
        assert any("rank 1" in message.lower() and "2 students" in message.lower()
                    for message in validation_messages)

    def test_non_top_three_must_be_rank_four(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=2, percentage=95),
            _make_student("Carol", 2, rank=3, percentage=90),
            _make_student("Dave", 3, rank=5, percentage=85),
        ]
        validation_messages = validate_ranks(student_scores)
        assert any("rank 5" in message.lower() and "rank 4" in message.lower()
                    for message in validation_messages)

    def test_no_ranked_students_returns_empty(self):
        student_scores = [
            _make_student("Alice", 0, rank=None, percentage=None),
            _make_student("Bob", 1, rank=None, percentage=None),
        ]
        validation_messages = validate_ranks(student_scores)
        assert validation_messages == []


# ===================================================================
# Tests for validate_percentages
# ===================================================================

class TestValidatePercentages:
    """Tests for the validate_percentages function."""

    def test_valid_percentages_produce_no_errors(self):
        student_scores = _build_valid_five_student_scores()
        validation_messages = validate_percentages(student_scores)
        assert validation_messages == []

    def test_rank_one_without_100_percent_produces_error(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=98),
            _make_student("Bob", 1, rank=2, percentage=95),
            _make_student("Carol", 2, rank=3, percentage=90),
        ]
        validation_messages = validate_percentages(student_scores)
        error_messages = [m for m in validation_messages if m.startswith("Error")]
        assert any("rank 1" in message.lower() and "100" in message
                    for message in error_messages)

    def test_percentage_below_75_produces_error(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=2, percentage=74),
        ]
        validation_messages = validate_percentages(student_scores)
        error_messages = [m for m in validation_messages if m.startswith("Error")]
        assert any("74" in message and "outside" in message.lower()
                    for message in error_messages)

    def test_percentage_above_100_produces_error(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=101),
        ]
        validation_messages = validate_percentages(student_scores)
        error_messages = [m for m in validation_messages if m.startswith("Error")]
        assert any("101" in message and "outside" in message.lower()
                    for message in error_messages)

    def test_duplicate_percentages_produce_warning(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=2, percentage=90),
            _make_student("Carol", 2, rank=3, percentage=90),
        ]
        validation_messages = validate_percentages(student_scores)
        warning_messages = [m for m in validation_messages if m.startswith("Warning")]
        assert any("90" in message and "shared" in message.lower()
                    for message in warning_messages)

    def test_percentage_75_to_79_triggers_special_circumstance_warning(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=2, percentage=95),
            _make_student("Carol", 2, rank=3, percentage=90),
            _make_student("Dave", 3, rank=4, percentage=77),
        ]
        validation_messages = validate_percentages(student_scores)
        warning_messages = [m for m in validation_messages if m.startswith("Warning")]
        assert any("77" in message and "special circumstances" in message.lower()
                    for message in warning_messages)

    def test_percentage_75_boundary_triggers_special_warning(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=4, percentage=75),
        ]
        validation_messages = validate_percentages(student_scores)
        warning_messages = [m for m in validation_messages if m.startswith("Warning")]
        assert any("75" in message and "special circumstances" in message.lower()
                    for message in warning_messages)

    def test_percentage_79_boundary_triggers_special_warning(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=4, percentage=79),
        ]
        validation_messages = validate_percentages(student_scores)
        warning_messages = [m for m in validation_messages if m.startswith("Warning")]
        assert any("79" in message and "special circumstances" in message.lower()
                    for message in warning_messages)

    def test_percentage_80_does_not_trigger_special_warning(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=4, percentage=80),
        ]
        validation_messages = validate_percentages(student_scores)
        special_warnings = [
            m for m in validation_messages
            if "special circumstances" in m.lower()
        ]
        assert special_warnings == []

    def test_no_percentages_returns_empty(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=None),
        ]
        validation_messages = validate_percentages(student_scores)
        assert validation_messages == []


# ===================================================================
# Tests for validate_rank_percentage_consistency
# ===================================================================

class TestValidateRankPercentageConsistency:
    """Tests for the validate_rank_percentage_consistency function."""

    def test_valid_consistency_produces_no_messages(self):
        student_scores = _build_valid_five_student_scores()
        validation_messages = validate_rank_percentage_consistency(student_scores)
        assert validation_messages == []

    def test_rank_one_less_than_rank_two_produces_error(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=2, percentage=100),
            _make_student("Carol", 2, rank=3, percentage=90),
        ]
        validation_messages = validate_rank_percentage_consistency(student_scores)
        assert any("rank 1" in message.lower() and "rank 2" in message.lower()
                    for message in validation_messages)

    def test_rank_two_less_than_rank_three_produces_error(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=2, percentage=88),
            _make_student("Carol", 2, rank=3, percentage=90),
        ]
        validation_messages = validate_rank_percentage_consistency(student_scores)
        assert any("rank 2" in message.lower() and "rank 3" in message.lower()
                    for message in validation_messages)

    def test_rank_four_exceeding_rank_three_produces_error(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=2, percentage=95),
            _make_student("Carol", 2, rank=3, percentage=85),
            _make_student("Dave", 3, rank=4, percentage=90),
        ]
        validation_messages = validate_rank_percentage_consistency(student_scores)
        assert any("Dave" in message and "rank 4" in message.lower()
                    for message in validation_messages)

    def test_rank_three_equal_to_rank_four_is_acceptable(self):
        """Rank 3 >= Rank 4, so equality is fine."""
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=2, percentage=95),
            _make_student("Carol", 2, rank=3, percentage=85),
            _make_student("Dave", 3, rank=4, percentage=85),
        ]
        # Note: this will trigger a duplicate-percentage warning in
        # validate_percentages, but consistency itself is fine.
        validation_messages = validate_rank_percentage_consistency(student_scores)
        assert validation_messages == []

    def test_single_scored_student_returns_empty(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
        ]
        validation_messages = validate_rank_percentage_consistency(student_scores)
        assert validation_messages == []


# ===================================================================
# Tests for validate_all
# ===================================================================

class TestValidateAll:
    """Tests for the combined validate_all function."""

    def test_valid_scoring_passes_with_no_messages(self):
        student_scores = _build_valid_five_student_scores()
        all_messages = validate_all(student_scores)
        assert all_messages == []

    def test_combines_rank_and_percentage_errors(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=98),   # rank 1 not 100
            _make_student("Bob", 1, rank=1, percentage=95),     # duplicate rank 1
            _make_student("Carol", 2, rank=3, percentage=90),
        ]
        all_messages = validate_all(student_scores)
        # Should have rank errors AND percentage errors.
        assert len(all_messages) >= 2

    def test_all_none_values_return_empty(self):
        """Completely unscored students should produce no validation messages."""
        student_scores = [
            _make_student("Alice", 0, rank=None, percentage=None),
            _make_student("Bob", 1, rank=None, percentage=None),
            _make_student("Carol", 2, rank=None, percentage=None),
        ]
        all_messages = validate_all(student_scores)
        assert all_messages == []


# ===================================================================
# Tests for get_ranked_summary
# ===================================================================

class TestGetRankedSummary:
    """Tests for the get_ranked_summary sorting function."""

    def test_sorts_by_rank_ascending(self):
        student_scores = [
            _make_student("Carol", 2, rank=3, percentage=90),
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=2, percentage=95),
        ]
        sorted_students = get_ranked_summary(student_scores)
        sorted_names = [s["student_name"] for s in sorted_students]
        assert sorted_names == ["Alice", "Bob", "Carol"]

    def test_same_rank_sorts_by_percentage_descending(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=2, percentage=95),
            _make_student("Carol", 2, rank=3, percentage=90),
            _make_student("Eve", 4, rank=4, percentage=80),
            _make_student("Dave", 3, rank=4, percentage=85),
        ]
        sorted_students = get_ranked_summary(student_scores)
        # Rank-4 students should be Dave (85) before Eve (80).
        rank_four_names = [
            s["student_name"] for s in sorted_students if s["rank"] == 4
        ]
        assert rank_four_names == ["Dave", "Eve"]

    def test_none_ranks_sort_to_end(self):
        student_scores = [
            _make_student("Unranked", 3, rank=None, percentage=None),
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=2, percentage=95),
        ]
        sorted_students = get_ranked_summary(student_scores)
        assert sorted_students[-1]["student_name"] == "Unranked"

    def test_none_percentage_sorts_after_scored_at_same_rank(self):
        student_scores = [
            _make_student("Alice", 0, rank=4, percentage=None),
            _make_student("Bob", 1, rank=4, percentage=85),
        ]
        sorted_students = get_ranked_summary(student_scores)
        sorted_names = [s["student_name"] for s in sorted_students]
        assert sorted_names == ["Bob", "Alice"]

    def test_empty_input_returns_empty(self):
        assert get_ranked_summary([]) == []

    def test_full_sort_order(self):
        student_scores = [
            _make_student("Eve", 4, rank=4, percentage=80),
            _make_student("Carol", 2, rank=3, percentage=90),
            _make_student("Dave", 3, rank=4, percentage=85),
            _make_student("Bob", 1, rank=2, percentage=95),
            _make_student("Alice", 0, rank=1, percentage=100),
        ]
        sorted_students = get_ranked_summary(student_scores)
        sorted_names = [s["student_name"] for s in sorted_students]
        assert sorted_names == ["Alice", "Bob", "Carol", "Dave", "Eve"]


# ===================================================================
# Edge cases: fewer than 3 students
# ===================================================================

class TestEdgeCaseSmallStudentCount:
    """Edge cases when there are only 2 or 3 students."""

    def test_two_students_valid_ranks(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=2, percentage=95),
        ]
        rank_messages = validate_ranks(student_scores)
        assert rank_messages == []

    def test_two_students_invalid_rank_three(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=3, percentage=95),
        ]
        rank_messages = validate_ranks(student_scores)
        assert any("rank 3" in message.lower() and "invalid" in message.lower()
                    for message in rank_messages)

    def test_single_student_rank_one(self):
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
        ]
        rank_messages = validate_ranks(student_scores)
        assert rank_messages == []

    def test_three_students_valid_ranks(self):
        """Three students is exactly the standard case threshold."""
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=2, percentage=95),
            _make_student("Carol", 2, rank=3, percentage=90),
        ]
        rank_messages = validate_ranks(student_scores)
        assert rank_messages == []

    def test_three_students_all_valid(self):
        """Full validation with exactly 3 students, all correct."""
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=2, percentage=95),
            _make_student("Carol", 2, rank=3, percentage=90),
        ]
        all_messages = validate_all(student_scores)
        assert all_messages == []


# ===================================================================
# Edge cases: None / unscored values
# ===================================================================

class TestEdgeCaseNoneValues:
    """Edge cases when some or all values are None (not yet scored)."""

    def test_all_ranks_none_validates_clean(self):
        student_scores = [
            _make_student("Alice", 0, rank=None, percentage=None),
            _make_student("Bob", 1, rank=None, percentage=None),
            _make_student("Carol", 2, rank=None, percentage=None),
            _make_student("Dave", 3, rank=None, percentage=None),
        ]
        assert validate_ranks(student_scores) == []
        assert validate_percentages(student_scores) == []
        assert validate_rank_percentage_consistency(student_scores) == []
        assert validate_all(student_scores) == []

    def test_partial_ranks_assigned(self):
        """Only some students ranked -- validate what is present."""
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=100),
            _make_student("Bob", 1, rank=None, percentage=None),
            _make_student("Carol", 2, rank=None, percentage=None),
            _make_student("Dave", 3, rank=None, percentage=None),
        ]
        # Rank validation should flag missing rank 2 and rank 3 since
        # there are 4 students total (standard case applies).
        rank_messages = validate_ranks(student_scores)
        assert any("rank 2" in m.lower() for m in rank_messages)
        assert any("rank 3" in m.lower() for m in rank_messages)

    def test_percentage_none_with_rank_set(self):
        """A student has a rank but no percentage yet -- percentage
        validation should skip them, consistency should skip them."""
        student_scores = [
            _make_student("Alice", 0, rank=1, percentage=None),
        ]
        assert validate_percentages(student_scores) == []
        assert validate_rank_percentage_consistency(student_scores) == []

    def test_get_ranked_summary_with_all_none(self):
        student_scores = [
            _make_student("Alice", 0, rank=None, percentage=None),
            _make_student("Bob", 1, rank=None, percentage=None),
        ]
        sorted_students = get_ranked_summary(student_scores)
        # Both have None rank/percentage -- order is stable (original order).
        assert len(sorted_students) == 2
