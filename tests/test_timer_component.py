"""
Unit tests for the pure-computation helpers in timer_component.

The rendering functions (render_javascript_timer, render_timer_ui) depend on
Streamlit's runtime and st.components.v1.html(), so they are tested manually.
This file covers the deterministic logic that can be exercised with pytest and
standard mocking.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

# We need to mock Streamlit before importing the module under test, because
# timer_component.py performs ``import streamlit as st`` at the top level.
# In a CI environment where Streamlit is installed this isn't strictly
# required, but the mock ensures tests stay isolated from Streamlit internals.

import sys

# Provide a lightweight stand-in so the import succeeds even without Streamlit.
_mock_streamlit = MagicMock()
_mock_streamlit.session_state = {}
sys.modules.setdefault("streamlit", _mock_streamlit)
sys.modules.setdefault("streamlit.components", MagicMock())
sys.modules.setdefault("streamlit.components.v1", MagicMock())

from timer_component import (  # noqa: E402
    get_elapsed_seconds,
    get_minutes_remaining_announcement,
    get_remaining_display,
    initialize_timer_state,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_session_state():
    """Ensure a clean session_state dict for every test."""
    import streamlit as st
    st.session_state = {}
    yield
    st.session_state = {}


def _set_session(**kwargs):
    """Convenience: bulk-set keys on the mocked session_state."""
    import streamlit as st
    st.session_state.update(kwargs)


# ---------------------------------------------------------------------------
# Tests: initialize_timer_state
# ---------------------------------------------------------------------------

class TestInitializeTimerState:
    """Verify that initialize_timer_state populates the correct defaults."""

    def test_sets_default_keys_when_session_state_is_empty(self):
        initialize_timer_state()

        import streamlit as st
        assert st.session_state["timer_running"] is False
        assert st.session_state["timer_start_timestamp"] is None
        assert st.session_state["timer_stop_timestamp"] is None
        assert st.session_state["timer_event_max_seconds"] == 480

    def test_does_not_overwrite_existing_values(self):
        _set_session(
            timer_running=True,
            timer_start_timestamp=1000.0,
            timer_stop_timestamp=1100.0,
            timer_event_max_seconds=300,
        )

        initialize_timer_state()

        import streamlit as st
        assert st.session_state["timer_running"] is True
        assert st.session_state["timer_start_timestamp"] == 1000.0
        assert st.session_state["timer_stop_timestamp"] == 1100.0
        assert st.session_state["timer_event_max_seconds"] == 300


# ---------------------------------------------------------------------------
# Tests: get_elapsed_seconds
# ---------------------------------------------------------------------------

class TestGetElapsedSeconds:
    """Verify elapsed-time computation under various timer states."""

    def test_returns_zero_when_timer_not_started(self):
        initialize_timer_state()
        assert get_elapsed_seconds() == 0.0

    def test_returns_zero_when_start_timestamp_is_none(self):
        _set_session(timer_start_timestamp=None, timer_running=False)
        assert get_elapsed_seconds() == 0.0

    @patch("timer_component.time")
    def test_calculates_elapsed_while_running(self, mock_time_module):
        mock_time_module.time.return_value = 1000.0 + 123.45
        _set_session(
            timer_start_timestamp=1000.0,
            timer_running=True,
            timer_stop_timestamp=None,
        )

        elapsed = get_elapsed_seconds()
        assert elapsed == pytest.approx(123.45)

    def test_calculates_elapsed_when_stopped_with_known_timestamps(self):
        start = 1700000000.0
        stop = 1700000247.5  # 247.5 seconds later
        _set_session(
            timer_start_timestamp=start,
            timer_running=False,
            timer_stop_timestamp=stop,
        )

        elapsed = get_elapsed_seconds()
        assert elapsed == pytest.approx(247.5)

    def test_returns_zero_when_stopped_but_no_stop_timestamp(self):
        """Edge case: timer_running=False, start set, but stop is None."""
        _set_session(
            timer_start_timestamp=1000.0,
            timer_running=False,
            timer_stop_timestamp=None,
        )
        assert get_elapsed_seconds() == 0.0


# ---------------------------------------------------------------------------
# Tests: get_remaining_display
# ---------------------------------------------------------------------------

class TestGetRemainingDisplay:
    """Verify human-readable remaining-time formatting."""

    def test_full_time_when_elapsed_is_zero(self):
        result = get_remaining_display(elapsed_seconds=0.0, max_seconds=480)
        assert result == "8:00"

    def test_full_time_for_five_minute_event(self):
        result = get_remaining_display(elapsed_seconds=0.0, max_seconds=300)
        assert result == "5:00"

    def test_remaining_format_mid_event(self):
        # 480 - 157 = 323 seconds remaining = 5 min 23 sec
        result = get_remaining_display(elapsed_seconds=157.0, max_seconds=480)
        assert result == "5:23 remaining"

    def test_remaining_format_under_one_minute(self):
        # 480 - 435 = 45 seconds remaining
        result = get_remaining_display(elapsed_seconds=435.0, max_seconds=480)
        assert result == "0:45 remaining"

    def test_overtime_display(self):
        # 512 - 480 = 32 seconds over
        result = get_remaining_display(elapsed_seconds=512.0, max_seconds=480)
        assert result == "OVERTIME +0:32"

    def test_overtime_display_minutes(self):
        # 600 - 480 = 120 seconds over = 2:00
        result = get_remaining_display(elapsed_seconds=600.0, max_seconds=480)
        assert result == "OVERTIME +2:00"

    def test_exactly_at_limit(self):
        result = get_remaining_display(elapsed_seconds=480.0, max_seconds=480)
        assert result == "OVERTIME +0:00"

    def test_one_second_remaining(self):
        result = get_remaining_display(elapsed_seconds=479.0, max_seconds=480)
        assert result == "0:01 remaining"


# ---------------------------------------------------------------------------
# Tests: get_minutes_remaining_announcement
# ---------------------------------------------------------------------------

class TestGetMinutesRemainingAnnouncement:
    """Verify judge-facing announcement strings."""

    def test_full_event_announcement(self):
        result = get_minutes_remaining_announcement(
            elapsed_seconds=0.0, max_seconds=480
        )
        assert result == "8 minutes left"

    def test_seven_minutes_left(self):
        # After 60 seconds of a 480 second event -> 420 remaining -> 7 min
        result = get_minutes_remaining_announcement(
            elapsed_seconds=60.0, max_seconds=480
        )
        assert result == "7 minutes left"

    def test_one_minute_left_singular(self):
        # 420 elapsed of 480 -> 60 remaining -> ceil(60/60) = 1
        # But 60 remaining is not < 60, so the "Less than 1 minute" branch
        # should NOT fire.  ceil(60/60) = 1 -> singular.
        result = get_minutes_remaining_announcement(
            elapsed_seconds=420.0, max_seconds=480
        )
        assert result == "1 minute left"

    def test_less_than_one_minute_left(self):
        result = get_minutes_remaining_announcement(
            elapsed_seconds=430.0, max_seconds=480
        )
        assert result == "Less than 1 minute left"

    def test_overtime_announcement(self):
        result = get_minutes_remaining_announcement(
            elapsed_seconds=512.0, max_seconds=480
        )
        assert result == "OVERTIME by 32 seconds"

    def test_overtime_large(self):
        result = get_minutes_remaining_announcement(
            elapsed_seconds=600.0, max_seconds=480
        )
        assert result == "OVERTIME by 120 seconds"

    def test_two_minutes_left(self):
        # 360 elapsed of 480 -> 120 remaining -> 2 minutes
        result = get_minutes_remaining_announcement(
            elapsed_seconds=360.0, max_seconds=480
        )
        assert result == "2 minutes left"

    def test_partial_minute_rounds_up(self):
        # 350 elapsed of 480 -> 130 remaining -> ceil(130/60) = 3
        result = get_minutes_remaining_announcement(
            elapsed_seconds=350.0, max_seconds=480
        )
        assert result == "3 minutes left"
