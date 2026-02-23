"""Tests for data_manager module -- JSON persistence and export formatting."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from data_manager import (
    DATA_DIRECTORY,
    ensure_data_directory_exists,
    format_all_feedback,
    format_student_feedback,
    format_tabroom_summary,
    format_time_display,
    get_round_filepath,
    list_saved_rounds,
    load_most_recent_round,
    load_round_data,
    save_round_data,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _build_sample_student(
    student_name: str = "Jane Doe",
    student_index: int = 0,
    elapsed_seconds: float = 412.7,
    rank: int = 1,
    percentage: int = 100,
) -> dict:
    """Helper to build a single student data dictionary."""
    return {
        "student_name": student_name,
        "student_index": student_index,
        "elapsed_seconds": elapsed_seconds,
        "timer_started": True,
        "timer_stopped": True,
        "ballot_info": {
            "draw_number": "3",
            "code": "AB12",
            "round_number": "1",
            "section": "A",
            "selection_title": "Hamlet",
            "author": "Shakespeare",
            "topic": "",
        },
        "interp_notes": {
            "quality_of_literature": "Excellent selection",
            "physical_performance": "Good character work",
            "vocal_performance": "Strong vocal variety",
            "total_effect": "Very compelling",
            "reason_for_rank_score": "Outstanding overall performance",
        },
        "public_address_notes": {
            "topic_analysis": "",
            "physical_performance": "",
            "vocal_performance": "",
            "organization": "",
            "development": "",
            "total_effect": "",
            "reason_for_rank_score": "",
        },
        "rank": rank,
        "percentage": percentage,
    }


def _build_sample_round_data() -> dict:
    """Helper to build a complete round data dictionary with multiple students."""
    return {
        "event_key": "dramatic_interpretation",
        "event_display_name": "Dramatic Interpretation",
        "round_started_at": "2026-02-06T14:30:00",
        "round_saved_at": "2026-02-06T15:45:00",
        "time_max_seconds": 480,
        "students": [
            _build_sample_student("Jane Doe", 0, 412.7, rank=1, percentage=100),
            _build_sample_student("John Smith", 1, 435.0, rank=2, percentage=97),
            _build_sample_student("Alice Johnson", 2, 348.0, rank=3, percentage=94),
            _build_sample_student("Bob Williams", 3, 482.0, rank=4, percentage=91),
            _build_sample_student("Carol Davis", 4, 453.0, rank=4, percentage=88),
        ],
    }


@pytest.fixture()
def sample_round_data() -> dict:
    """Provide a complete sample round data dictionary."""
    return _build_sample_round_data()


@pytest.fixture()
def sample_student_data() -> dict:
    """Provide a single sample student data dictionary."""
    return _build_sample_student()


# ---------------------------------------------------------------------------
# get_round_filepath
# ---------------------------------------------------------------------------


class TestGetRoundFilepath:
    """Tests for the get_round_filepath helper."""

    def test_colons_are_replaced_with_dashes(self) -> None:
        filepath = get_round_filepath("dramatic_interpretation", "2026-02-06T14:30:00")
        assert ":" not in filepath.name

    def test_filename_contains_event_key_and_timestamp(self) -> None:
        filepath = get_round_filepath("dramatic_interpretation", "2026-02-06T14:30:00")
        assert filepath.name == "dramatic_interpretation_2026-02-06T14-30-00.json"

    def test_filepath_lives_inside_data_directory(self) -> None:
        filepath = get_round_filepath("duo_interpretation", "2026-01-01T09:00:00")
        assert filepath.parent == DATA_DIRECTORY


# ---------------------------------------------------------------------------
# save_round_data / load_round_data  (round-trip)
# ---------------------------------------------------------------------------


class TestSaveAndLoadRoundTrip:
    """Verify that saving then loading preserves all data."""

    def test_round_trip_preserves_data(self, tmp_path: Path, sample_round_data: dict, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("data_manager.DATA_DIRECTORY", tmp_path / "data" / "rounds")

        saved_filepath = save_round_data(sample_round_data)
        loaded_data = load_round_data(saved_filepath)

        assert loaded_data == sample_round_data

    def test_saved_file_is_valid_json(self, tmp_path: Path, sample_round_data: dict, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("data_manager.DATA_DIRECTORY", tmp_path / "data" / "rounds")

        saved_filepath = save_round_data(sample_round_data)

        raw_content = saved_filepath.read_text(encoding="utf-8")
        parsed_json = json.loads(raw_content)
        assert isinstance(parsed_json, dict)

    def test_saved_file_uses_indent(self, tmp_path: Path, sample_round_data: dict, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("data_manager.DATA_DIRECTORY", tmp_path / "data" / "rounds")

        saved_filepath = save_round_data(sample_round_data)
        raw_content = saved_filepath.read_text(encoding="utf-8")

        # Indented JSON should contain lines starting with spaces.
        indented_lines = [line for line in raw_content.splitlines() if line.startswith("  ")]
        assert len(indented_lines) > 0


# ---------------------------------------------------------------------------
# Missing data directory gets created on save
# ---------------------------------------------------------------------------


class TestEnsureDataDirectoryCreation:
    """Verify that the data directory is created automatically."""

    def test_save_creates_missing_directory(self, tmp_path: Path, sample_round_data: dict, monkeypatch: pytest.MonkeyPatch) -> None:
        nonexistent_directory = tmp_path / "brand_new" / "nested" / "rounds"
        monkeypatch.setattr("data_manager.DATA_DIRECTORY", nonexistent_directory)

        assert not nonexistent_directory.exists()

        save_round_data(sample_round_data)

        assert nonexistent_directory.exists()

    def test_ensure_data_directory_is_idempotent(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        target_directory = tmp_path / "idempotent_test"
        monkeypatch.setattr("data_manager.DATA_DIRECTORY", target_directory)

        ensure_data_directory_exists()
        ensure_data_directory_exists()  # second call should not raise

        assert target_directory.is_dir()


# ---------------------------------------------------------------------------
# load_round_data error handling
# ---------------------------------------------------------------------------


class TestLoadRoundDataErrors:
    """Tests for load_round_data when files are missing."""

    def test_raises_file_not_found_for_missing_file(self, tmp_path: Path) -> None:
        nonexistent_filepath = tmp_path / "does_not_exist.json"

        with pytest.raises(FileNotFoundError):
            load_round_data(nonexistent_filepath)


# ---------------------------------------------------------------------------
# load_most_recent_round
# ---------------------------------------------------------------------------


class TestLoadMostRecentRound:
    """Tests for finding the most recently modified round file."""

    def test_returns_none_when_directory_is_empty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        empty_directory = tmp_path / "empty_rounds"
        empty_directory.mkdir(parents=True)
        monkeypatch.setattr("data_manager.DATA_DIRECTORY", empty_directory)

        result = load_most_recent_round()

        assert result is None

    def test_returns_none_when_directory_does_not_exist(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        nonexistent_directory = tmp_path / "nonexistent"
        monkeypatch.setattr("data_manager.DATA_DIRECTORY", nonexistent_directory)

        result = load_most_recent_round()

        assert result is None

    def test_finds_newest_file_by_mtime(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        rounds_directory = tmp_path / "rounds"
        rounds_directory.mkdir(parents=True)
        monkeypatch.setattr("data_manager.DATA_DIRECTORY", rounds_directory)

        older_round_data = _build_sample_round_data()
        older_round_data["event_key"] = "older_event"
        older_round_data["round_started_at"] = "2026-01-01T10:00:00"

        newer_round_data = _build_sample_round_data()
        newer_round_data["event_key"] = "newer_event"
        newer_round_data["round_started_at"] = "2026-02-06T14:30:00"

        older_filepath = rounds_directory / "older_event_2026-01-01T10-00-00.json"
        newer_filepath = rounds_directory / "newer_event_2026-02-06T14-30-00.json"

        older_filepath.write_text(json.dumps(older_round_data), encoding="utf-8")
        # Ensure a measurable mtime difference between the two files.
        time.sleep(0.05)
        newer_filepath.write_text(json.dumps(newer_round_data), encoding="utf-8")

        most_recent = load_most_recent_round()

        assert most_recent is not None
        assert most_recent["event_key"] == "newer_event"

    def test_ignores_non_json_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        rounds_directory = tmp_path / "rounds"
        rounds_directory.mkdir(parents=True)
        monkeypatch.setattr("data_manager.DATA_DIRECTORY", rounds_directory)

        # Write a non-JSON file only.
        (rounds_directory / "notes.txt").write_text("not json")

        result = load_most_recent_round()

        assert result is None


# ---------------------------------------------------------------------------
# list_saved_rounds
# ---------------------------------------------------------------------------


class TestListSavedRounds:
    """Tests for listing saved round files with metadata."""

    def test_returns_empty_list_when_directory_missing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("data_manager.DATA_DIRECTORY", tmp_path / "nonexistent")

        result = list_saved_rounds()

        assert result == []

    def test_returns_empty_list_when_no_json_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        empty_directory = tmp_path / "empty"
        empty_directory.mkdir()
        monkeypatch.setattr("data_manager.DATA_DIRECTORY", empty_directory)

        result = list_saved_rounds()

        assert result == []

    def test_lists_rounds_newest_first(self, tmp_path: Path, sample_round_data: dict, monkeypatch: pytest.MonkeyPatch) -> None:
        rounds_directory = tmp_path / "rounds"
        rounds_directory.mkdir()
        monkeypatch.setattr("data_manager.DATA_DIRECTORY", rounds_directory)

        older_data = dict(sample_round_data, event_display_name="Older Event", round_started_at="2026-01-01T10:00:00")
        newer_data = dict(sample_round_data, event_display_name="Newer Event", round_started_at="2026-02-06T14:30:00")

        (rounds_directory / "older.json").write_text(json.dumps(older_data), encoding="utf-8")
        time.sleep(0.05)
        (rounds_directory / "newer.json").write_text(json.dumps(newer_data), encoding="utf-8")

        result = list_saved_rounds()

        assert len(result) == 2
        assert result[0]["event_display_name"] == "Newer Event"
        assert result[1]["event_display_name"] == "Older Event"

    def test_includes_student_count(self, tmp_path: Path, sample_round_data: dict, monkeypatch: pytest.MonkeyPatch) -> None:
        rounds_directory = tmp_path / "rounds"
        rounds_directory.mkdir()
        monkeypatch.setattr("data_manager.DATA_DIRECTORY", rounds_directory)

        (rounds_directory / "round.json").write_text(json.dumps(sample_round_data), encoding="utf-8")

        result = list_saved_rounds()

        assert result[0]["student_count"] == 5

    def test_skips_corrupt_json(self, tmp_path: Path, sample_round_data: dict, monkeypatch: pytest.MonkeyPatch) -> None:
        rounds_directory = tmp_path / "rounds"
        rounds_directory.mkdir()
        monkeypatch.setattr("data_manager.DATA_DIRECTORY", rounds_directory)

        (rounds_directory / "corrupt.json").write_text("not valid json", encoding="utf-8")
        time.sleep(0.05)
        (rounds_directory / "valid.json").write_text(json.dumps(sample_round_data), encoding="utf-8")

        result = list_saved_rounds()

        assert len(result) == 1
        assert result[0]["event_display_name"] == "Dramatic Interpretation"


# ---------------------------------------------------------------------------
# format_time_display
# ---------------------------------------------------------------------------


class TestFormatTimeDisplay:
    """Tests for elapsed-seconds to M:SS conversion."""

    def test_returns_na_for_none(self) -> None:
        assert format_time_display(None) == "N/A"

    def test_zero_seconds(self) -> None:
        assert format_time_display(0) == "0:00"

    def test_exact_minute(self) -> None:
        assert format_time_display(60.0) == "1:00"

    def test_fractional_seconds_truncated(self) -> None:
        # 412.7 seconds = 6 minutes 52.7 seconds -> "6:52"
        assert format_time_display(412.7) == "6:52"

    def test_large_value(self) -> None:
        # 600 seconds = 10 minutes 0 seconds
        assert format_time_display(600) == "10:00"

    def test_seconds_less_than_ten_are_zero_padded(self) -> None:
        # 65 seconds = 1 minute 5 seconds -> "1:05"
        assert format_time_display(65) == "1:05"

    def test_sub_minute_value(self) -> None:
        assert format_time_display(45) == "0:45"


# ---------------------------------------------------------------------------
# format_tabroom_summary
# ---------------------------------------------------------------------------


class TestFormatTabroomSummary:
    """Tests for plain-text Tabroom summary output."""

    def test_header_contains_event_name(self, sample_round_data: dict) -> None:
        summary_text = format_tabroom_summary(sample_round_data)
        assert "Event: Dramatic Interpretation" in summary_text

    def test_header_contains_date(self, sample_round_data: dict) -> None:
        summary_text = format_tabroom_summary(sample_round_data)
        assert "Date: 2026-02-06" in summary_text

    def test_contains_column_headers(self, sample_round_data: dict) -> None:
        summary_text = format_tabroom_summary(sample_round_data)
        assert "Rank" in summary_text
        assert "Name" in summary_text
        assert "Percentage" in summary_text
        assert "Time" in summary_text

    def test_students_sorted_by_rank(self, sample_round_data: dict) -> None:
        summary_text = format_tabroom_summary(sample_round_data)
        lines = summary_text.splitlines()

        # Find data lines (after the dashed separator line).
        separator_line_index = next(
            index for index, line in enumerate(lines) if line.startswith("----")
        )
        data_lines = lines[separator_line_index + 1:]

        student_names_in_order = []
        for line in data_lines:
            if line.strip():
                # Name starts after the rank column (first 6 chars).
                name_portion = line[6:].split()[0:2]
                student_names_in_order.append(" ".join(name_portion))

        assert student_names_in_order[0] == "Jane Doe"
        assert student_names_in_order[1] == "John Smith"

    def test_all_students_appear(self, sample_round_data: dict) -> None:
        summary_text = format_tabroom_summary(sample_round_data)
        for student in sample_round_data["students"]:
            assert student["student_name"] in summary_text

    def test_time_values_present(self, sample_round_data: dict) -> None:
        summary_text = format_tabroom_summary(sample_round_data)
        # Jane Doe: 412.7s -> "6:52"
        assert "6:52" in summary_text

    def test_tied_ranks_sorted_by_percentage_descending(self, sample_round_data: dict) -> None:
        summary_text = format_tabroom_summary(sample_round_data)
        bob_position = summary_text.index("Bob Williams")
        carol_position = summary_text.index("Carol Davis")
        # Bob (91%) should appear before Carol (88%) since both rank 4.
        assert bob_position < carol_position


# ---------------------------------------------------------------------------
# format_student_feedback
# ---------------------------------------------------------------------------


class TestFormatStudentFeedback:
    """Tests for individual student feedback formatting."""

    def test_includes_student_name(self, sample_student_data: dict) -> None:
        feedback_text = format_student_feedback(sample_student_data, "Dramatic Interpretation")
        assert "Jane Doe" in feedback_text

    def test_includes_rank_and_percentage(self, sample_student_data: dict) -> None:
        feedback_text = format_student_feedback(sample_student_data, "Dramatic Interpretation")
        assert "Rank 1" in feedback_text
        assert "100%" in feedback_text

    def test_includes_time(self, sample_student_data: dict) -> None:
        feedback_text = format_student_feedback(sample_student_data, "Dramatic Interpretation")
        assert "Time: 6:52" in feedback_text

    def test_includes_interp_note_labels(self, sample_student_data: dict) -> None:
        feedback_text = format_student_feedback(sample_student_data, "Dramatic Interpretation")
        assert "Quality of Literature: Excellent selection" in feedback_text
        assert "Physical Performance: Good character work" in feedback_text
        assert "Vocal Performance: Strong vocal variety" in feedback_text
        assert "Total Effect: Very compelling" in feedback_text
        assert "Reason for Rank/Score: Outstanding overall performance" in feedback_text

    def test_includes_ballot_info(self, sample_student_data: dict) -> None:
        feedback_text = format_student_feedback(sample_student_data, "Dramatic Interpretation")
        assert "Code: AB12" in feedback_text
        assert "Draw #: 3" in feedback_text

    def test_handles_missing_notes_gracefully(self) -> None:
        student_without_notes = _build_sample_student()
        student_without_notes["interp_notes"] = {}
        student_without_notes["public_address_notes"] = {}

        feedback_text = format_student_feedback(student_without_notes, "Dramatic Interpretation")

        # Should still have the header line and time.
        assert "Jane Doe" in feedback_text
        assert "Time:" in feedback_text
        # Should NOT have note labels when there are no notes.
        assert "Quality of Literature:" not in feedback_text
        assert "Total Effect:" not in feedback_text

    def test_handles_missing_elapsed_seconds(self) -> None:
        student_without_time = _build_sample_student()
        del student_without_time["elapsed_seconds"]

        feedback_text = format_student_feedback(student_without_time, "Dramatic Interpretation")
        assert "Time: N/A" in feedback_text


# ---------------------------------------------------------------------------
# format_all_feedback
# ---------------------------------------------------------------------------


class TestFormatAllFeedback:
    """Tests for combined feedback output."""

    def test_includes_all_students(self, sample_round_data: dict) -> None:
        all_feedback_text = format_all_feedback(sample_round_data)
        for student in sample_round_data["students"]:
            assert student["student_name"] in all_feedback_text

    def test_students_separated_by_divider(self, sample_round_data: dict) -> None:
        all_feedback_text = format_all_feedback(sample_round_data)
        separator = "=" * 50
        assert separator in all_feedback_text

    def test_students_ordered_by_rank(self, sample_round_data: dict) -> None:
        all_feedback_text = format_all_feedback(sample_round_data)
        jane_position = all_feedback_text.index("Jane Doe")
        john_position = all_feedback_text.index("John Smith")
        alice_position = all_feedback_text.index("Alice Johnson")

        assert jane_position < john_position < alice_position

    def test_single_student_no_separator(self) -> None:
        single_student_round = _build_sample_round_data()
        single_student_round["students"] = [_build_sample_student()]

        all_feedback_text = format_all_feedback(single_student_round)
        separator = "=" * 50
        assert separator not in all_feedback_text
