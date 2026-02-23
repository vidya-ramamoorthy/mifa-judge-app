"""
MIFA Scoring Validation Engine

Validates judging rules for ranks and percentages in MIFA competitions.
This module has NO Streamlit dependency. It operates purely on student_score
dictionaries and returns validation messages.

Each student_score dict has the shape:
    {
        "student_name": str,
        "student_index": int,
        "rank": int | None,
        "percentage": int | None,
        "elapsed_seconds": float | None,
    }
"""

from __future__ import annotations

from collections import Counter


def _scored_students(student_scores: list[dict]) -> list[dict]:
    """Return only the students that have both a rank and a percentage assigned."""
    return [
        score for score in student_scores
        if score.get("rank") is not None and score.get("percentage") is not None
    ]


def _ranked_students(student_scores: list[dict]) -> list[dict]:
    """Return only the students that have a rank assigned (rank is not None)."""
    return [
        score for score in student_scores
        if score.get("rank") is not None
    ]


def _students_with_percentage(student_scores: list[dict]) -> list[dict]:
    """Return only the students that have a percentage assigned (percentage is not None)."""
    return [
        score for score in student_scores
        if score.get("percentage") is not None
    ]


# ---------------------------------------------------------------------------
# Rank validation
# ---------------------------------------------------------------------------

def validate_ranks(student_scores: list[dict]) -> list[str]:
    """Validate that MIFA rank assignments follow the rules.

    Rules:
    - Exactly one student gets rank 1, one gets rank 2, one gets rank 3.
    - All remaining students get rank 4.
    - No duplicate ranks among 1-3.
    - If fewer than 3 students total, ranks should use 1, 2, ... up to
      the number of students.

    Returns a list of warning/error message strings (empty when valid).
    """
    validation_messages: list[str] = []

    ranked_students = _ranked_students(student_scores)

    # If no students have been ranked yet, nothing to validate.
    if not ranked_students:
        return validation_messages

    total_student_count = len(student_scores)
    assigned_ranks = [student["rank"] for student in ranked_students]
    rank_counts = Counter(assigned_ranks)

    if total_student_count < 3:
        # With fewer than 3 students, valid ranks are 1 .. total_student_count.
        expected_ranks = set(range(1, total_student_count + 1))
        actual_unique_ranks = set(assigned_ranks)

        for expected_rank in expected_ranks:
            count_for_rank = rank_counts.get(expected_rank, 0)
            if count_for_rank == 0:
                validation_messages.append(
                    f"Error: No student assigned rank {expected_rank}."
                )
            elif count_for_rank > 1:
                validation_messages.append(
                    f"Error: Rank {expected_rank} is assigned to {count_for_rank} students (must be exactly 1)."
                )

        unexpected_ranks = actual_unique_ranks - expected_ranks
        for unexpected_rank in sorted(unexpected_ranks):
            validation_messages.append(
                f"Error: Rank {unexpected_rank} is invalid when there are only {total_student_count} student(s)."
            )
    else:
        # Standard case: 3 or more students.
        # Exactly one each of ranks 1, 2, 3.
        for required_rank in (1, 2, 3):
            count_for_rank = rank_counts.get(required_rank, 0)
            if count_for_rank == 0:
                validation_messages.append(
                    f"Error: No student assigned rank {required_rank}."
                )
            elif count_for_rank > 1:
                validation_messages.append(
                    f"Error: Rank {required_rank} is assigned to {count_for_rank} students (must be exactly 1)."
                )

        # All non-top-3 students must have rank 4.
        non_top_three_students = [
            student for student in ranked_students if student["rank"] not in (1, 2, 3)
        ]
        for student in non_top_three_students:
            if student["rank"] != 4:
                student_name = student.get("student_name", "Unknown")
                validation_messages.append(
                    f"Error: {student_name} has rank {student['rank']}; "
                    f"students outside top 3 must have rank 4."
                )

    return validation_messages


# ---------------------------------------------------------------------------
# Percentage validation
# ---------------------------------------------------------------------------

def validate_percentages(student_scores: list[dict]) -> list[str]:
    """Validate that MIFA percentage scores follow the rules.

    Rules:
    - All percentages are integers in range [75, 100].
    - Rank 1 must have percentage 100.
    - No two students have the same percentage.
    - Scores in the 75-79 range trigger a warning (reserved for special
      circumstances).

    Returns a list of warning/error message strings (empty when valid).
    """
    validation_messages: list[str] = []

    students_with_percentage = _students_with_percentage(student_scores)

    # If no percentages assigned yet, nothing to validate.
    if not students_with_percentage:
        return validation_messages

    # --- Range check ---
    for student in students_with_percentage:
        percentage_value = student["percentage"]
        student_name = student.get("student_name", "Unknown")

        if not isinstance(percentage_value, int):
            validation_messages.append(
                f"Error: {student_name} has a non-integer percentage ({percentage_value})."
            )
            continue

        if percentage_value < 75 or percentage_value > 100:
            validation_messages.append(
                f"Error: {student_name} has percentage {percentage_value}, "
                f"which is outside the allowed range [75, 100]."
            )

    # --- Rank 1 must be 100 ---
    rank_one_students = [
        student for student in student_scores
        if student.get("rank") == 1 and student.get("percentage") is not None
    ]
    for student in rank_one_students:
        if student["percentage"] != 100:
            student_name = student.get("student_name", "Unknown")
            validation_messages.append(
                f"Error: {student_name} has rank 1 but percentage {student['percentage']}; "
                f"rank 1 must have 100%."
            )

    # --- Duplicate percentage check ---
    all_percentages = [
        student["percentage"] for student in students_with_percentage
        if isinstance(student["percentage"], int)
    ]
    percentage_counts = Counter(all_percentages)
    for percentage_value, count in sorted(percentage_counts.items(), reverse=True):
        if count > 1:
            duplicated_student_names = [
                student.get("student_name", "Unknown")
                for student in students_with_percentage
                if student["percentage"] == percentage_value
            ]
            names_display = ", ".join(duplicated_student_names)
            validation_messages.append(
                f"Warning: Percentage {percentage_value} is shared by {count} students "
                f"({names_display}). Each student must have a unique percentage."
            )

    # --- Special circumstance warning for 75-79 ---
    for student in students_with_percentage:
        percentage_value = student.get("percentage")
        if isinstance(percentage_value, int) and 75 <= percentage_value <= 79:
            student_name = student.get("student_name", "Unknown")
            validation_messages.append(
                f"Warning: {student_name} has percentage {percentage_value}, "
                f"which is in the 75-79 range reserved for special circumstances."
            )

    return validation_messages


# ---------------------------------------------------------------------------
# Rank-percentage consistency validation
# ---------------------------------------------------------------------------

def validate_rank_percentage_consistency(student_scores: list[dict]) -> list[str]:
    """Validate that rank ordering is consistent with percentage ordering.

    Rules:
    - Higher rank (lower rank number) must have a higher percentage.
    - Rank 1 (100%) > Rank 2 > Rank 3 >= any Rank 4.

    Returns a list of warning/error message strings (empty when valid).
    """
    validation_messages: list[str] = []

    fully_scored_students = _scored_students(student_scores)

    if len(fully_scored_students) < 2:
        return validation_messages

    # Group by rank.
    students_by_rank: dict[int, list[dict]] = {}
    for student in fully_scored_students:
        rank_value = student["rank"]
        students_by_rank.setdefault(rank_value, []).append(student)

    # Get the percentage for a unique rank (1, 2, or 3). Returns None if
    # that rank is not present or has no percentage.
    def _get_unique_rank_percentage(target_rank: int) -> int | None:
        students_at_rank = students_by_rank.get(target_rank, [])
        if len(students_at_rank) == 1:
            return students_at_rank[0]["percentage"]
        return None

    rank_one_percentage = _get_unique_rank_percentage(1)
    rank_two_percentage = _get_unique_rank_percentage(2)
    rank_three_percentage = _get_unique_rank_percentage(3)

    # Rank 1 > Rank 2
    if rank_one_percentage is not None and rank_two_percentage is not None:
        if rank_one_percentage <= rank_two_percentage:
            validation_messages.append(
                f"Error: Rank 1 percentage ({rank_one_percentage}) must be "
                f"strictly greater than rank 2 percentage ({rank_two_percentage})."
            )

    # Rank 2 > Rank 3
    if rank_two_percentage is not None and rank_three_percentage is not None:
        if rank_two_percentage <= rank_three_percentage:
            validation_messages.append(
                f"Error: Rank 2 percentage ({rank_two_percentage}) must be "
                f"strictly greater than rank 3 percentage ({rank_three_percentage})."
            )

    # Rank 3 >= any Rank 4
    if rank_three_percentage is not None:
        rank_four_students = students_by_rank.get(4, [])
        for rank_four_student in rank_four_students:
            rank_four_percentage = rank_four_student["percentage"]
            if rank_four_percentage is not None and rank_four_percentage > rank_three_percentage:
                student_name = rank_four_student.get("student_name", "Unknown")
                validation_messages.append(
                    f"Error: {student_name} (rank 4) has percentage {rank_four_percentage}, "
                    f"which exceeds rank 3 percentage ({rank_three_percentage})."
                )

    return validation_messages


# ---------------------------------------------------------------------------
# Combined validation
# ---------------------------------------------------------------------------

def validate_all(student_scores: list[dict]) -> list[str]:
    """Run all validations and return the combined list of messages."""
    all_validation_messages: list[str] = []
    all_validation_messages.extend(validate_ranks(student_scores))
    all_validation_messages.extend(validate_percentages(student_scores))
    all_validation_messages.extend(validate_rank_percentage_consistency(student_scores))
    return all_validation_messages


# ---------------------------------------------------------------------------
# Summary / sorting
# ---------------------------------------------------------------------------

def get_ranked_summary(student_scores: list[dict]) -> list[dict]:
    """Return students sorted by rank (ascending) then percentage (descending).

    Students without a rank are placed at the end. Among those without a rank,
    students are sorted by percentage descending. Students with no percentage
    are placed after those with one.
    """
    # Provide large sentinel values so that None sorts to the end.
    RANK_SENTINEL = 999
    PERCENTAGE_SENTINEL = -1

    def _sort_key(student: dict) -> tuple[int, int]:
        rank_value = student.get("rank") if student.get("rank") is not None else RANK_SENTINEL
        # Negate percentage so that higher percentages sort first (ascending on negated value).
        percentage_value = student.get("percentage") if student.get("percentage") is not None else PERCENTAGE_SENTINEL
        return (rank_value, -percentage_value)

    sorted_students = sorted(student_scores, key=_sort_key)
    return sorted_students
