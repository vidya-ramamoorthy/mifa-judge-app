"""
Hybrid Python + JavaScript timer component for the MIFA Tournament Judge App.

Streamlit reruns the entire script on every widget interaction, so a pure Python
timer would block the UI. This module solves that by keeping authoritative
timestamps in Python (via st.session_state) while injecting a JavaScript
countdown through st.components.v1.html() that ticks independently in the
browser between reruns.

Architecture:
    Python side  -- owns start/stop timestamps and max duration (session_state)
    JavaScript side -- receives those values as template literals, computes
                       elapsed / remaining every second, and renders the
                       visual countdown without requiring a Streamlit rerun.
"""

import time
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components


# ---------------------------------------------------------------------------
# 1. Session-state initialisation
# ---------------------------------------------------------------------------

def initialize_timer_state() -> None:
    """Populate st.session_state with timer keys if they are not already set.

    Keys created:
        timer_running (bool):              Whether the timer is currently active.
        timer_start_timestamp (float|None): epoch seconds when Start was pressed.
        timer_stop_timestamp  (float|None): epoch seconds when Stop was pressed.
        timer_event_max_seconds (int):      total allowed time for the event.
    """
    default_values = {
        "timer_running": False,
        "timer_start_timestamp": None,
        "timer_stop_timestamp": None,
        "timer_event_max_seconds": 480,
    }
    for key, default_value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


# ---------------------------------------------------------------------------
# 2. Button callbacks
# ---------------------------------------------------------------------------

def start_timer_callback() -> None:
    """on_click callback for the Start button.

    Records the current wall-clock time as the start timestamp, marks the
    timer as running, and clears any previous stop timestamp.
    """
    st.session_state.timer_start_timestamp = time.time()
    st.session_state.timer_running = True
    st.session_state.timer_stop_timestamp = None


def stop_timer_callback() -> None:
    """on_click callback for the Stop button.

    Records the current wall-clock time as the stop timestamp and marks the
    timer as no longer running.
    """
    st.session_state.timer_stop_timestamp = time.time()
    st.session_state.timer_running = False


# ---------------------------------------------------------------------------
# 3. Pure computation helpers
# ---------------------------------------------------------------------------

def get_elapsed_seconds() -> float:
    """Return how many seconds have elapsed since the timer was started.

    Returns:
        0.0   if the timer has never been started.
        now - start   if the timer is currently running.
        stop - start  if the timer has been stopped.
    """
    start_timestamp: Optional[float] = st.session_state.get("timer_start_timestamp")

    if start_timestamp is None:
        return 0.0

    if st.session_state.get("timer_running", False):
        return time.time() - start_timestamp

    stop_timestamp: Optional[float] = st.session_state.get("timer_stop_timestamp")
    if stop_timestamp is not None:
        return stop_timestamp - start_timestamp

    return 0.0


def get_remaining_display(elapsed_seconds: float, max_seconds: int) -> str:
    """Format the remaining (or overtime) duration as a human-readable string.

    Args:
        elapsed_seconds: How many seconds have passed since the timer started.
        max_seconds:     The total allowed time for the event.

    Returns:
        "8:00"                when elapsed is 0 (full time remaining).
        "5:23 remaining"      when still under the limit.
        "OVERTIME +0:32"      when the limit has been exceeded.
    """
    if elapsed_seconds == 0.0:
        total_minutes = max_seconds // 60
        total_leftover_seconds = max_seconds % 60
        return f"{total_minutes}:{total_leftover_seconds:02d}"

    remaining_seconds = max_seconds - elapsed_seconds

    if remaining_seconds > 0:
        whole_minutes = int(remaining_seconds) // 60
        whole_seconds = int(remaining_seconds) % 60
        return f"{whole_minutes}:{whole_seconds:02d} remaining"

    overtime_seconds = abs(remaining_seconds)
    overtime_minutes = int(overtime_seconds) // 60
    overtime_leftover = int(overtime_seconds) % 60
    return f"OVERTIME +{overtime_minutes}:{overtime_leftover:02d}"


def get_minutes_remaining_announcement(
    elapsed_seconds: float, max_seconds: int
) -> str:
    """Return an announcement string suitable for the judge to read aloud.

    The announcement changes at each whole-minute boundary so the judge can
    inform the student how much time is left.

    Args:
        elapsed_seconds: How many seconds have passed.
        max_seconds:     The total allowed time for the event.

    Returns:
        "8 minutes left"          at the start of an 8-minute event.
        "1 minute left"           (singular).
        "Less than 1 minute left" when under 60 seconds remain.
        "OVERTIME by 32 seconds"  when over the limit.
    """
    remaining_seconds = max_seconds - elapsed_seconds

    if remaining_seconds <= 0:
        overtime_whole_seconds = int(abs(remaining_seconds))
        return f"OVERTIME by {overtime_whole_seconds} seconds"

    import math
    minutes_left = math.ceil(remaining_seconds / 60)

    if remaining_seconds < 60:
        return "Less than 1 minute left"

    if minutes_left == 1:
        return "1 minute left"

    return f"{minutes_left} minutes left"


# ---------------------------------------------------------------------------
# 4. JavaScript timer renderer
# ---------------------------------------------------------------------------

_TIMER_HTML_TEMPLATE = """
<div id="timer-card" style="
    background: #1e1e2e;
    border-radius: 12px;
    padding: 24px 32px;
    text-align: center;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    max-width: 520px;
    margin: 0 auto;
">
    <!-- Top row: Stopwatch (elapsed) and Countdown side by side -->
    <div style="display: flex; justify-content: center; gap: 32px; margin-bottom: 8px;">

        <!-- Stopwatch (elapsed time counting UP) -->
        <div style="flex: 1; text-align: center;">
            <div style="
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 2px;
                text-transform: uppercase;
                color: #888;
                margin-bottom: 4px;
            ">ELAPSED</div>
            <div id="stopwatch-display" style="
                font-family: 'Courier New', 'Consolas', monospace;
                font-size: 40px;
                font-weight: 700;
                color: #3498db;
                line-height: 1.1;
            ">0:00</div>
        </div>

        <!-- Divider -->
        <div style="width: 1px; background: rgba(255,255,255,0.15); margin: 4px 0;"></div>

        <!-- Countdown timer (remaining time counting DOWN) -->
        <div style="flex: 1; text-align: center;">
            <div id="timer-status" style="
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 2px;
                text-transform: uppercase;
                color: #aaa;
                margin-bottom: 4px;
            ">REMAINING</div>
            <div id="timer-display" style="
                font-family: 'Courier New', 'Consolas', monospace;
                font-size: 40px;
                font-weight: 700;
                color: #2ecc71;
                line-height: 1.1;
            ">--:--</div>
        </div>
    </div>

    <!-- Flash card: minutes remaining announcement -->
    <div id="minute-announce" style="
        font-size: 18px;
        font-weight: 600;
        color: #fff;
        padding: 8px 16px;
        background: rgba(46, 204, 113, 0.15);
        border: 1px solid rgba(46, 204, 113, 0.3);
        border-radius: 8px;
        display: inline-block;
        margin-top: 8px;
        min-width: 200px;
    "></div>
</div>

<script>
(function() {
    const startTimestamp = __START_TIMESTAMP__;
    const maxSeconds = __MAX_SECONDS__;
    const isRunning = __IS_RUNNING__;

    function formatTime(totalSeconds) {
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = Math.floor(totalSeconds % 60);
        return minutes + ':' + ('0' + seconds).slice(-2);
    }

    function updateTimer() {
        const nowEpochSeconds = Date.now() / 1000;
        const elapsedSeconds = nowEpochSeconds - startTimestamp;
        const remainingSeconds = maxSeconds - elapsedSeconds;

        const stopwatchDisplay = document.getElementById('stopwatch-display');
        const timerDisplay = document.getElementById('timer-display');
        const statusDisplay = document.getElementById('timer-status');
        const minuteAnnounce = document.getElementById('minute-announce');

        // Stopwatch: always counts up
        stopwatchDisplay.textContent = formatTime(elapsedSeconds);

        if (remainingSeconds > 0) {
            timerDisplay.textContent = formatTime(remainingSeconds);

            const ceilingMinutesLeft = Math.ceil(remainingSeconds / 60);
            minuteAnnounce.textContent = ceilingMinutesLeft + ' minute' + (ceilingMinutesLeft !== 1 ? 's' : '') + ' remaining';

            if (remainingSeconds < 30) {
                timerDisplay.style.color = '#e74c3c';
                statusDisplay.textContent = 'FINISHING';
                statusDisplay.style.color = '#e74c3c';
                stopwatchDisplay.style.color = '#e74c3c';
                minuteAnnounce.style.background = 'rgba(231, 76, 60, 0.15)';
                minuteAnnounce.style.borderColor = 'rgba(231, 76, 60, 0.3)';
                minuteAnnounce.style.color = '#e74c3c';
            } else if (remainingSeconds < 60) {
                timerDisplay.style.color = '#f39c12';
                statusDisplay.textContent = 'UNDER 1 MINUTE';
                statusDisplay.style.color = '#f39c12';
                stopwatchDisplay.style.color = '#f39c12';
                minuteAnnounce.style.background = 'rgba(243, 156, 18, 0.15)';
                minuteAnnounce.style.borderColor = 'rgba(243, 156, 18, 0.3)';
                minuteAnnounce.style.color = '#f39c12';
            } else {
                timerDisplay.style.color = '#2ecc71';
                statusDisplay.textContent = 'REMAINING';
                statusDisplay.style.color = '#aaa';
                stopwatchDisplay.style.color = '#3498db';
                minuteAnnounce.style.background = 'rgba(46, 204, 113, 0.15)';
                minuteAnnounce.style.borderColor = 'rgba(46, 204, 113, 0.3)';
                minuteAnnounce.style.color = '#fff';
            }
        } else {
            const overtimeTotal = Math.abs(remainingSeconds);
            timerDisplay.textContent = 'OVERTIME +' + formatTime(overtimeTotal);
            timerDisplay.style.color = '#e74c3c';
            statusDisplay.textContent = 'OVER TIME LIMIT';
            statusDisplay.style.color = '#e74c3c';
            stopwatchDisplay.style.color = '#e74c3c';
            minuteAnnounce.textContent = 'Over by ' + Math.ceil(overtimeTotal) + ' seconds';
            minuteAnnounce.style.background = 'rgba(231, 76, 60, 0.2)';
            minuteAnnounce.style.borderColor = 'rgba(231, 76, 60, 0.4)';
            minuteAnnounce.style.color = '#e74c3c';
        }
    }

    if (isRunning) {
        updateTimer();
        setInterval(updateTimer, 1000);
    } else {
        const finalElapsed = __ELAPSED_SECONDS__;
        const stopwatchDisplay = document.getElementById('stopwatch-display');
        const timerDisplay = document.getElementById('timer-display');
        const statusDisplay = document.getElementById('timer-status');
        const minuteAnnounce = document.getElementById('minute-announce');

        stopwatchDisplay.textContent = formatTime(finalElapsed);
        stopwatchDisplay.style.color = '#888';

        const finalRemaining = maxSeconds - finalElapsed;
        if (finalRemaining > 0) {
            timerDisplay.textContent = formatTime(finalRemaining);
        } else {
            timerDisplay.textContent = 'OVERTIME +' + formatTime(Math.abs(finalRemaining));
        }
        timerDisplay.style.color = '#888';
        statusDisplay.textContent = 'STOPPED';
        statusDisplay.style.color = '#888';
        minuteAnnounce.textContent = 'Final time: ' + formatTime(finalElapsed);
        minuteAnnounce.style.background = 'rgba(255,255,255,0.06)';
        minuteAnnounce.style.borderColor = 'rgba(255,255,255,0.1)';
        minuteAnnounce.style.color = '#aaa';
    }
})();
</script>
"""

TIMER_COMPONENT_HEIGHT_PX = 220


def render_javascript_timer(
    start_timestamp: float,
    max_seconds: int,
    is_running: bool,
) -> None:
    """Inject a self-updating JavaScript countdown timer into the Streamlit page.

    The JavaScript receives the authoritative Python-side values as template
    literals and then independently computes elapsed / remaining every second,
    so the visual countdown runs smoothly without Streamlit reruns.

    Args:
        start_timestamp: Epoch seconds when the timer was started.
        max_seconds:     Total allowed time for the event.
        is_running:      Whether the timer is currently ticking.
    """
    elapsed_for_static_display = get_elapsed_seconds()

    rendered_html = (
        _TIMER_HTML_TEMPLATE
        .replace("__START_TIMESTAMP__", str(start_timestamp))
        .replace("__MAX_SECONDS__", str(max_seconds))
        .replace("__IS_RUNNING__", "true" if is_running else "false")
        .replace("__ELAPSED_SECONDS__", str(elapsed_for_static_display))
    )

    components.html(rendered_html, height=TIMER_COMPONENT_HEIGHT_PX)


# ---------------------------------------------------------------------------
# 5. Complete timer UI
# ---------------------------------------------------------------------------

def render_timer_ui(event_max_seconds: int) -> dict:
    """Render the full timer interface: buttons, countdown, and status text.

    This is the main entry point that a Streamlit page should call.  It wires
    up Start / Stop buttons with their callbacks, renders the JavaScript
    countdown while the timer is running, and shows a static result when the
    timer has been stopped.

    Args:
        event_max_seconds: The total allowed time for the event in seconds.

    Returns:
        A dict with the current timer state::

            {
                "elapsed_seconds": float,
                "is_running": bool,
                "is_stopped": bool,
            }
    """
    initialize_timer_state()
    st.session_state.timer_event_max_seconds = event_max_seconds

    is_timer_running = st.session_state.timer_running
    has_timer_been_started = st.session_state.timer_start_timestamp is not None
    has_timer_been_stopped = (
        not is_timer_running and st.session_state.timer_stop_timestamp is not None
    )

    # -- Control buttons -------------------------------------------------------
    button_column_left, button_column_right = st.columns(2)

    with button_column_left:
        st.button(
            "Start Timer",
            on_click=start_timer_callback,
            disabled=is_timer_running,
            use_container_width=True,
        )

    with button_column_right:
        st.button(
            "Stop Timer",
            on_click=stop_timer_callback,
            disabled=not is_timer_running,
            use_container_width=True,
        )

    # -- Timer display ---------------------------------------------------------
    current_elapsed_seconds = get_elapsed_seconds()

    if is_timer_running and has_timer_been_started:
        render_javascript_timer(
            start_timestamp=st.session_state.timer_start_timestamp,
            max_seconds=event_max_seconds,
            is_running=True,
        )
    elif has_timer_been_stopped:
        render_javascript_timer(
            start_timestamp=st.session_state.timer_start_timestamp,
            max_seconds=event_max_seconds,
            is_running=False,
        )
        final_display_text = get_remaining_display(
            current_elapsed_seconds, event_max_seconds
        )
        st.info(f"Timer stopped -- {final_display_text}")
    else:
        # Timer has not been started yet; show full duration.
        full_duration_display = get_remaining_display(0.0, event_max_seconds)
        st.caption(f"Event duration: {full_duration_display}")

    return {
        "elapsed_seconds": current_elapsed_seconds,
        "is_running": is_timer_running,
        "is_stopped": has_timer_been_stopped,
    }
