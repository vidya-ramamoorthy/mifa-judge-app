"""
Data persistence and export formatting for the MIFA Judge App.

This module handles saving/loading round data as JSON and formatting
output for copying to Tabroom. It has NO Streamlit dependency.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIRECTORY: Path = Path(__file__).parent / "data" / "rounds"

INTERP_NOTE_LABELS: dict[str, str] = {
    "quality_of_literature": "Quality of Literature",
    "physical_performance": "Physical Performance",
    "vocal_performance": "Vocal Performance",
    "total_effect": "Total Effect",
    "reason_for_rank_score": "Reason for Rank/Score",
}

PUBLIC_ADDRESS_NOTE_LABELS: dict[str, str] = {
    "topic_analysis": "Topic",
    "physical_performance": "Physical Performance",
    "vocal_performance": "Vocal Performance",
    "organization": "Organization",
    "development": "Development",
    "total_effect": "Total Effect",
    "reason_for_rank_score": "Reason for Rank/Score",
}


def ensure_data_directory_exists() -> None:
    """Create the DATA_DIRECTORY and any missing parents if they do not exist."""
    DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)


def get_round_filepath(event_key: str, round_timestamp: str) -> Path:
    """Build a filesystem-safe filepath for a round JSON file.

    Colons in the ISO timestamp are replaced with dashes so the filename
    is valid on all major operating systems.

    Args:
        event_key: Snake-case identifier for the event (e.g. "dramatic_interpretation").
        round_timestamp: ISO-8601 timestamp string from round_started_at.

    Returns:
        Path like ``data/rounds/dramatic_interpretation_2026-02-06T14-30-00.json``.
    """
    sanitized_timestamp = round_timestamp.replace(":", "-")
    filename = f"{event_key}_{sanitized_timestamp}.json"
    return DATA_DIRECTORY / filename


def save_round_data(round_data: dict) -> Path:
    """Persist a round data dictionary to a JSON file on disk.

    The filename is derived from the event_key and round_started_at fields
    inside *round_data*.  The data directory is created automatically if it
    does not already exist.

    Args:
        round_data: Complete round dictionary matching the expected JSON schema.

    Returns:
        The Path that was written to.
    """
    ensure_data_directory_exists()

    event_key: str = round_data["event_key"]
    round_started_at: str = round_data["round_started_at"]
    output_filepath: Path = get_round_filepath(event_key, round_started_at)

    with open(output_filepath, "w", encoding="utf-8") as json_file:
        json.dump(round_data, json_file, indent=2, ensure_ascii=False)

    return output_filepath


def load_round_data(filepath: Path) -> dict:
    """Load a round data dictionary from a JSON file.

    Args:
        filepath: Path to the JSON file to read.

    Returns:
        The parsed dictionary.

    Raises:
        FileNotFoundError: If *filepath* does not exist on disk.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Round data file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as json_file:
        loaded_round_data: dict = json.load(json_file)

    return loaded_round_data


def load_most_recent_round() -> dict | None:
    """Load the most recently modified round JSON file from DATA_DIRECTORY.

    Files are compared by filesystem modification time (mtime).

    Returns:
        The parsed dictionary for the newest round, or ``None`` if the
        data directory is empty or does not exist.
    """
    if not DATA_DIRECTORY.exists():
        return None

    json_filepaths: list[Path] = sorted(
        DATA_DIRECTORY.glob("*.json"),
        key=lambda filepath: filepath.stat().st_mtime,
    )

    if not json_filepaths:
        return None

    most_recent_filepath: Path = json_filepaths[-1]
    return load_round_data(most_recent_filepath)


def list_saved_rounds() -> list[dict]:
    """List all saved round files with basic metadata, newest first.

    Each entry contains the filepath, event name, timestamp, and student count
    so the UI can display a browsable list without loading full round data.

    Returns:
        A list of metadata dicts sorted by file modification time (newest first).
        Returns an empty list if the data directory is missing or empty.
    """
    if not DATA_DIRECTORY.exists():
        return []

    json_filepaths: list[Path] = sorted(
        DATA_DIRECTORY.glob("*.json"),
        key=lambda filepath: filepath.stat().st_mtime,
        reverse=True,
    )

    saved_rounds: list[dict] = []
    for filepath in json_filepaths:
        try:
            with open(filepath, "r", encoding="utf-8") as json_file:
                round_data: dict = json.load(json_file)
            saved_rounds.append({
                "filepath": filepath,
                "event_display_name": round_data.get("event_display_name", "Unknown Event"),
                "round_started_at": round_data.get("round_started_at", ""),
                "student_count": len(round_data.get("students", [])),
            })
        except (json.JSONDecodeError, KeyError):
            continue

    return saved_rounds


def format_time_display(elapsed_seconds: float | None) -> str:
    """Convert an elapsed-seconds value to a human-readable ``M:SS`` string.

    Args:
        elapsed_seconds: Total seconds (may include fractional part), or
            ``None`` if no time was recorded.

    Returns:
        A string like ``"6:53"`` or ``"N/A"`` when the input is None.
    """
    if elapsed_seconds is None:
        return "N/A"

    total_whole_seconds = int(elapsed_seconds)
    minutes = total_whole_seconds // 60
    remaining_seconds = total_whole_seconds % 60

    return f"{minutes}:{remaining_seconds:02d}"


def format_tabroom_summary(round_data: dict) -> str:
    """Format ranked results as a plain-text table suitable for Tabroom.

    Students are sorted by rank ascending, then by percentage descending
    within the same rank.

    Args:
        round_data: Complete round dictionary.

    Returns:
        A multi-line plain-text string with header and aligned columns.
    """
    event_display_name: str = round_data["event_display_name"]
    round_started_at: str = round_data["round_started_at"]

    # Extract just the date portion from the ISO timestamp.
    round_date: str = round_started_at[:10]

    sorted_students: list[dict] = sorted(
        round_data["students"],
        key=lambda student: (
            student["rank"] if student.get("rank") is not None else 99,
            -(student["percentage"] if student.get("percentage") is not None else 0),
        ),
    )

    # Determine column widths dynamically based on content.
    header_name = "Name"
    header_rank = "Rank"
    header_percentage = "Percentage"
    header_time = "Time"

    student_names: list[str] = [
        student.get("student_name") or f"Student {i + 1}"
        for i, student in enumerate(sorted_students)
    ]
    name_column_width: int = max(len(header_name), *(len(name) for name in student_names))

    formatted_lines: list[str] = [
        f"Event: {event_display_name}",
        f"Date: {round_date}",
        "",
        f"{header_rank:<6}{header_name:<{name_column_width + 2}}{header_percentage:<12}{header_time}",
        f"{'----':<6}{'----':<{name_column_width + 2}}{'-' * 10:<12}{'----'}",
    ]

    for idx, student in enumerate(sorted_students):
        student_name: str = student.get("student_name") or f"Student {idx + 1}"
        rank_value = student.get("rank")
        rank_display: str = str(rank_value) if rank_value is not None else "--"
        percentage_value = student.get("percentage")
        percentage_display: str = str(percentage_value) if percentage_value is not None else "--"
        elapsed_seconds: float | None = student.get("elapsed_seconds")
        time_display: str = format_time_display(elapsed_seconds)

        formatted_lines.append(
            f"{rank_display:<6}{student_name:<{name_column_width + 2}}{percentage_display:<12}{time_display}"
        )

    return "\n".join(formatted_lines)


def format_student_feedback(student_data: dict, event_display_name: str) -> str:
    """Format feedback for a single student as readable plain text.

    Args:
        student_data: A single student entry from the round's students list.
        event_display_name: Human-readable event name (currently unused in
            output but accepted for future flexibility).

    Returns:
        Multi-line plain-text feedback block.
    """
    student_name: str = student_data.get("student_name") or "Unknown"
    rank_value = student_data.get("rank")
    rank_display: str = str(rank_value) if rank_value is not None else "--"
    percentage_value = student_data.get("percentage")
    percentage_display: str = f"{percentage_value}%" if percentage_value is not None else "--%"
    elapsed_seconds: float | None = student_data.get("elapsed_seconds")
    time_display: str = format_time_display(elapsed_seconds)

    # Ballot info
    ballot_info: dict = student_data.get("ballot_info", {})

    feedback_lines: list[str] = [
        f"--- {student_name} (Rank {rank_display}, {percentage_display}) ---",
        f"Code: {ballot_info.get('code', '')}  Draw #: {ballot_info.get('draw_number', '')}",
        f"Time: {time_display}",
    ]

    # Add selection/author for interp or topic for public address
    if ballot_info.get("selection_title"):
        feedback_lines.append(
            f"Selection: {ballot_info['selection_title']}  "
            f"Author: {ballot_info.get('author', '')}"
        )
    if ballot_info.get("topic"):
        feedback_lines.append(f"Topic: {ballot_info['topic']}")

    feedback_lines.append("")

    # Category-specific criteria notes
    interp_notes: dict = student_data.get("interp_notes", {})
    pa_notes: dict = student_data.get("public_address_notes", {})

    # Try interpretation notes first
    has_interp_notes = any(
        interp_notes.get(key, "") for key in INTERP_NOTE_LABELS
    )
    has_pa_notes = any(
        pa_notes.get(key, "") for key in PUBLIC_ADDRESS_NOTE_LABELS
    )

    if has_interp_notes:
        for note_key, note_label in INTERP_NOTE_LABELS.items():
            note_value = interp_notes.get(note_key, "")
            if note_value:
                feedback_lines.append(f"{note_label}: {note_value}")

    if has_pa_notes:
        for note_key, note_label in PUBLIC_ADDRESS_NOTE_LABELS.items():
            note_value = pa_notes.get(note_key, "")
            if note_value:
                feedback_lines.append(f"{note_label}: {note_value}")

    return "\n".join(feedback_lines)


def format_all_feedback(round_data: dict) -> str:
    """Format feedback for every student in the round, sorted by rank.

    Args:
        round_data: Complete round dictionary.

    Returns:
        All individual feedback blocks joined by separator lines.
    """
    event_display_name: str = round_data["event_display_name"]

    sorted_students: list[dict] = sorted(
        round_data["students"],
        key=lambda student: (
            student["rank"] if student.get("rank") is not None else 99,
            -(student["percentage"] if student.get("percentage") is not None else 0),
        ),
    )

    feedback_separator = "\n\n" + "=" * 50 + "\n\n"

    individual_feedback_blocks: list[str] = [
        format_student_feedback(student, event_display_name)
        for student in sorted_students
    ]

    return feedback_separator.join(individual_feedback_blocks)
