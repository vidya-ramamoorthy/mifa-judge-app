"""
MIFA Judge Assistant - Streamlit App

A user-friendly tool for first-time MIFA tournament judges to time performances,
take structured notes, score contestants per MIFA rules, and export results
for pasting into Tabroom.
"""

import time
from datetime import datetime

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from event_data import (
    EVENT_DATA,
    MIFA_RULES_SUMMARY,
    CATEGORY_ORAL_INTERPRETATION,
    CATEGORY_PUBLIC_ADDRESS,
    get_all_event_display_names,
    get_event_by_key,
    get_event_key_by_display_name,
    get_events_by_category,
)
from timer_component import (
    initialize_timer_state,
    get_elapsed_seconds,
    get_remaining_display,
    get_minutes_remaining_announcement,
    render_timer_ui,
    start_timer_callback,
    stop_timer_callback,
)
from scoring_engine import validate_all, get_ranked_summary
from data_manager import (
    save_round_data,
    load_round_data,
    load_most_recent_round,
    list_saved_rounds,
    format_tabroom_summary,
    format_student_feedback,
    format_all_feedback,
    format_time_display,
)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="MIFA Judge Assistant",
    page_icon="\U0001F3C6",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Auto-refresh every 60 seconds to keep timer synced and trigger auto-save
auto_refresh_count = st_autorefresh(interval=60000, limit=None, key="auto_refresh")


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
def initialize_session_state():
    """Initialize all session state variables with safe defaults."""
    default_values = {
        "selected_event_key": None,
        "selected_event_display_name": None,
        "student_count": 0,
        "round_started_at": None,
        "round_setup_complete": False,
        "students": [],
        "current_student_index": 0,
        "data_dirty": False,
        "current_save_filepath": None,
        "scoring_warnings": [],
        "resumed_round": False,
        "viewing_past_round": False,
    }
    for key, default_value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


initialize_session_state()
initialize_timer_state()


# ---------------------------------------------------------------------------
# Helper: Build student data structure
# ---------------------------------------------------------------------------
def create_empty_student(student_index, student_name=""):
    """Create a blank student data dict with ballot info and category-specific notes."""
    return {
        "student_name": student_name,
        "student_index": student_index,
        "elapsed_seconds": None,
        "timer_started": False,
        "timer_stopped": False,
        # Ballot header info (from the critique sheet)
        "ballot_info": {
            "draw_number": "",
            "code": "",
            "round_number": "",
            "section": "",
            # Interpretation-specific
            "selection_title": "",
            "author": "",
            # Public address-specific
            "topic": "",
        },
        # Oral Interpretation criteria notes
        "interp_notes": {
            "quality_of_literature": "",
            "physical_performance": "",
            "vocal_performance": "",
            "total_effect": "",
            "reason_for_rank_score": "",
        },
        # Public Address criteria notes
        "public_address_notes": {
            "topic_analysis": "",
            "physical_performance": "",
            "vocal_performance": "",
            "organization": "",
            "development": "",
            "total_effect": "",
            "reason_for_rank_score": "",
        },
        "rank": None,
        "percentage": None,
    }


# ---------------------------------------------------------------------------
# Helper: Collect round data for saving
# ---------------------------------------------------------------------------
def collect_round_data():
    """Gather all current session state into a round data dict for saving."""
    return {
        "event_key": st.session_state.selected_event_key,
        "event_display_name": st.session_state.selected_event_display_name,
        "round_started_at": st.session_state.round_started_at,
        "round_saved_at": datetime.now().isoformat(),
        "time_max_seconds": st.session_state.get("timer_event_max_seconds", 480),
        "students": st.session_state.students,
    }


def trigger_auto_save():
    """Save current round data if there are changes."""
    if st.session_state.get("viewing_past_round"):
        return
    if st.session_state.round_setup_complete and st.session_state.data_dirty:
        round_data = collect_round_data()
        save_round_data(round_data)
        st.session_state.data_dirty = False


# Trigger auto-save on each refresh
if st.session_state.data_dirty:
    trigger_auto_save()


# ---------------------------------------------------------------------------
# Helper: Reset timer state for a new student
# ---------------------------------------------------------------------------
def reset_timer_for_student():
    """Clear timer state when switching to a new student."""
    st.session_state.timer_running = False
    st.session_state.timer_start_timestamp = None
    st.session_state.timer_stop_timestamp = None


# ---------------------------------------------------------------------------
# Helper: Render judging hints based on event category
# ---------------------------------------------------------------------------
def render_judging_hints(event_key, event_details):
    """Render category-specific judging hints inside an expander."""
    is_interp = event_details["category"] == CATEGORY_ORAL_INTERPRETATION
    is_pa = event_details["category"] == CATEGORY_PUBLIC_ADDRESS

    # -- Time limit --
    time_min = event_details["time_min_seconds"] // 60
    time_max = event_details["time_max_seconds"] // 60
    if time_min == time_max:
        st.markdown(f"**Time:** {time_max} min")
    elif time_min == 0:
        st.markdown(f"**Time:** up to {time_max} min (includes prep)")
    else:
        st.markdown(f"**Time:** {time_min}-{time_max} min")

    st.divider()

    # -- General feedback prompts (all events) --
    st.markdown("**What to comment on:**")
    st.caption(
        "**Content** - Did you like what they included?\n\n"
        "**Flow** - Easy to follow? Good transitions?\n\n"
        "**Interest** - Was it engaging? Grab your attention?\n\n"
        "**Vocal** - Enunciation, volume, tone variety?\n\n"
        "**Physical** - Movement, expressions, eye contact?"
    )

    st.divider()

    # -- Category-specific tips --
    if is_interp:
        st.markdown("**Interp Tips:**")
        st.caption(
            "Do you like the piece? How were scenes put together?\n\n"
            "How well did they become characters? "
            "Could you tell characters apart?"
        )

        if event_key == "duo_interpretation":
            st.caption(
                "Two performers - NO eye contact or touching between them. "
                "How well do they work as a team?"
            )
        elif event_key == "multiple_interpretation":
            st.caption("3-5 participants. Evaluate ensemble cohesion.")
        elif event_key == "program_oral_interpretation":
            st.caption(
                "Binder REQUIRED (solid color, stays in contact). "
                "At least 2 pieces from 2 genres. No chairs/stools/blox."
            )
        elif event_key == "storytelling":
            st.caption("Children's lit. Manuscripts/notes/books ARE allowed.")
        elif event_key in ("oi_poetry", "oi_prose"):
            st.caption("Original composition - student wrote it themselves.")

    elif is_pa:
        st.markdown("**Public Address Tips:**")
        st.caption(
            "Did you respect their sources and research? "
            "Did you believe what they were saying?\n\n"
            "Were visual aids effective and easy to understand (if used)?"
        )

        if event_key == "broadcasting":
            st.markdown("**Broadcasting:**")
            st.caption(
                "How did they organize their broadcast? "
                "Appropriate story length?\n\n"
                "Was the editorial well-argued? "
                "Your personal opinion should NOT affect scoring.\n\n"
                "Goal: hit exactly 5 min. "
                "15-min editorial prep, 8-min staggered draw."
            )
        elif event_key == "impromptu_speaking":
            st.markdown("**Impromptu:**")
            st.caption(
                "Timer starts when they see the prompt. "
                "6 min total = prep + speech.\n\n"
                "Announce aloud: 15s, 30s, 45s, 1 min. "
                "Then use time cards for remaining minutes.\n\n"
                "Don't expect polish - they're thinking on their feet!"
            )
        elif event_key == "extemporaneous_speaking":
            st.markdown("**Extemp:**")
            st.caption(
                "Student had 30 min to research a current events question. "
                "Evaluate depth of knowledge and evidence."
            )
        elif event_key == "duo_commentary":
            st.markdown("**Duo Commentary:**")
            st.caption(
                "Two students, SEATED position required. "
                "30-min prep, may look at each other.\n\n"
                "Evaluate balance between speakers."
            )
        elif event_key == "informative_speaking":
            st.caption("Purpose is to INFORM, not persuade.")
        elif event_key == "oratory":
            st.caption(
                "Persuasive speech. Don't let personal agreement "
                "or disagreement affect scoring."
            )
        elif event_key == "sales_speaking":
            st.caption("Must be an ACTUAL product or service (not invented).")

    # -- Key rules (top 4) --
    st.divider()
    st.markdown("**Key Rules:**")
    rules_to_show = event_details["rules"][:4]
    for rule in rules_to_show:
        st.caption(f"- {rule}")


# ---------------------------------------------------------------------------
# Feedback phrase options for interactive cheat sheet
# ---------------------------------------------------------------------------
INTERP_FEEDBACK_PHRASES = {
    "Quality of Literature": {
        "data_key": "quality_of_literature",
        "widget_key_prefix": "interp_lit",
        "notes_dict_key": "interp_notes",
        "phrases": [
            "Great piece choice, especially the part where",
            "The teaser pulled me in because",
            "This literature really showcases your ability to",
            "Consider a piece that lets you show more of",
            "The cutting could be tighter around",
        ],
    },
    "Physical Performance": {
        "data_key": "physical_performance",
        "widget_key_prefix": "interp_phys",
        "notes_dict_key": "interp_notes",
        "phrases": [
            "Strong character popping, especially between",
            "Your blocking and object work really sold the scene where",
            "Great stage presence, particularly during",
            "Try using more physicality to differentiate between",
            "Plant your feet more during",
            "The movement felt unmotivated when",
        ],
    },
    "Vocal Performance": {
        "data_key": "vocal_performance",
        "widget_key_prefix": "interp_vocal",
        "notes_dict_key": "interp_notes",
        "phrases": [
            "Great vocal variety, loved the shift when",
            "Character voices were distinct, especially",
            "Strong projection throughout, particularly in",
            "Try slowing down during the part where",
            "More vocal contrast between characters would help with",
            "Volume dropped during",
        ],
    },
    "Total Effect": {
        "data_key": "total_effect",
        "widget_key_prefix": "interp_effect",
        "notes_dict_key": "interp_notes",
        "phrases": [
            "Really compelling performance, the moment that stood out was",
            "Strong emotional arc, especially the transition from",
            "I was drawn in from the start because",
            "Save some intensity for the climax by pulling back during",
            "The ending could land harder if you",
            "I wanted to feel more connection during",
        ],
    },
    "Reason for Rank/Score": {
        "data_key": "reason_for_rank_score",
        "widget_key_prefix": "interp_reason",
        "notes_dict_key": "interp_notes",
        "phrases": [
            "Very polished performance overall, stood out because",
            "Competitive piece and delivery, the strength was",
            "Good foundation, the biggest area to improve is",
            "Keep working on this, your strongest moment was",
        ],
    },
}

PA_FEEDBACK_PHRASES = {
    "Topic": {
        "data_key": "topic_analysis",
        "widget_key_prefix": "pa_topic",
        "notes_dict_key": "public_address_notes",
        "phrases": [
            "Great topic choice, I was interested because",
            "I learned something new about",
            "Unique angle on this subject, especially",
            "Consider narrowing the focus to",
            "The topic would be stronger if you explored",
        ],
    },
    "Physical Performance": {
        "data_key": "physical_performance",
        "widget_key_prefix": "pa_phys",
        "notes_dict_key": "public_address_notes",
        "phrases": [
            "Confident posture and good energy, especially when",
            "Effective gestures that reinforced the point about",
            "Good eye contact with the audience during",
            "Try using the space more during",
            "Plant your feet and use purposeful movement for",
            "More eye contact during the section on",
        ],
    },
    "Vocal Performance": {
        "data_key": "vocal_performance",
        "widget_key_prefix": "pa_vocal",
        "notes_dict_key": "public_address_notes",
        "phrases": [
            "Great projection and vocal energy during",
            "Nice emphasis that highlighted the point about",
            "Clear and easy to follow, especially when",
            "Try varying your tone more when discussing",
            "Slow down during the part about",
            "I had trouble hearing the section on",
        ],
    },
    "Organization": {
        "data_key": "organization",
        "widget_key_prefix": "pa_org",
        "notes_dict_key": "public_address_notes",
        "phrases": [
            "Clear structure, easy to follow because",
            "Smooth transitions, especially between",
            "Strong opening that grabbed attention by",
            "The transition between your points on ___ and ___ needs",
            "Try signposting (First, Next, Finally) around",
            "Circle back to your opening to close stronger by",
        ],
    },
    "Development": {
        "data_key": "development",
        "widget_key_prefix": "pa_dev",
        "notes_dict_key": "public_address_notes",
        "phrases": [
            "Strong evidence, the most convincing part was",
            "Well-researched, especially the detail about",
            "Good examples that made the point about",
            "I wanted more evidence to support the claim about",
            "Expand on the example about",
            "Integrate your sources more smoothly when citing",
        ],
    },
    "Total Effect": {
        "data_key": "total_effect",
        "widget_key_prefix": "pa_effect",
        "notes_dict_key": "public_address_notes",
        "phrases": [
            "Very engaging, the strongest moment was",
            "I found myself convinced by the argument about",
            "Professional delivery throughout, especially",
            "Build to a stronger finish by",
            "I wanted to feel more passion during",
            "The audience connection was strongest when",
        ],
    },
    "Reason for Rank/Score": {
        "data_key": "reason_for_rank_score",
        "widget_key_prefix": "pa_reason",
        "notes_dict_key": "public_address_notes",
        "phrases": [
            "Polished speaker, stood out because",
            "Competitive presentation, the strength was",
            "Good foundation, focus next on improving",
            "Keep refining, your best moment was",
        ],
    },
}


# ---------------------------------------------------------------------------
# Helper: Render interactive feedback cheat sheet
# ---------------------------------------------------------------------------
def render_feedback_cheatsheet(event_key, event_details, student_index, current_student):
    """Render interactive feedback phrase selectors that insert into notes."""
    is_interp = event_details["category"] == CATEGORY_ORAL_INTERPRETATION

    feedback_criteria = INTERP_FEEDBACK_PHRASES if is_interp else PA_FEEDBACK_PHRASES

    # Clear widget keys from a previous insert (before widgets render)
    pending_clear_key = f"cheat_clear_pending_{student_index}"
    if st.session_state.get(pending_clear_key):
        for criteria_config in feedback_criteria.values():
            cheat_key = f"cheat_{criteria_config['widget_key_prefix']}_{student_index}"
            if cheat_key in st.session_state:
                del st.session_state[cheat_key]
            # Also clear text area keys so they re-read from the data dict
            widget_key = f"{criteria_config['widget_key_prefix']}_{student_index}"
            if widget_key in st.session_state:
                del st.session_state[widget_key]
        del st.session_state[pending_clear_key]

    st.caption("Pick starters below, then add your own details in the notes:")

    for criteria_label, criteria_config in feedback_criteria.items():
        cheat_key = f"cheat_{criteria_config['widget_key_prefix']}_{student_index}"
        st.multiselect(
            criteria_label,
            options=criteria_config["phrases"],
            key=cheat_key,
        )

    if st.button(
        "Insert into Notes",
        key=f"insert_feedback_{student_index}",
        type="primary",
        use_container_width=True,
    ):
        inserted_any = False
        for criteria_config in feedback_criteria.values():
            cheat_key = f"cheat_{criteria_config['widget_key_prefix']}_{student_index}"
            selected_phrases = st.session_state.get(cheat_key, [])
            if not selected_phrases:
                continue

            inserted_any = True
            notes_dict_key = criteria_config["notes_dict_key"]
            data_key = criteria_config["data_key"]
            widget_key = f"{criteria_config['widget_key_prefix']}_{student_index}"

            existing_text = current_student[notes_dict_key].get(data_key, "").strip()
            new_phrases_text = ". ".join(selected_phrases) + " -- "

            if existing_text:
                updated_text = f"{existing_text}. {new_phrases_text}"
            else:
                updated_text = new_phrases_text

            # Update student data dict (text area keys are cleared in pending_clear
            # so the widgets re-read from here via their value= parameter)
            current_student[notes_dict_key][data_key] = updated_text

        if inserted_any:
            # Flag to clear multiselects on next rerun (can't modify after render)
            st.session_state[pending_clear_key] = True
            st.session_state.data_dirty = True
            st.rerun()
        else:
            st.warning("Select some phrases first!")


# ---------------------------------------------------------------------------
# Sidebar: Round Setup
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Round Setup")

    # Check for previous round on first load
    if not st.session_state.round_setup_complete and not st.session_state.resumed_round:
        previous_round = load_most_recent_round()
        if previous_round is not None:
            st.warning("Found a previous unsaved round.")
            resume_col, fresh_col = st.columns(2)
            with resume_col:
                if st.button("Resume", use_container_width=True):
                    st.session_state.selected_event_key = previous_round.get("event_key")
                    st.session_state.selected_event_display_name = previous_round.get(
                        "event_display_name"
                    )
                    st.session_state.round_started_at = previous_round.get(
                        "round_started_at"
                    )
                    st.session_state.students = previous_round.get("students", [])
                    st.session_state.student_count = len(st.session_state.students)
                    st.session_state.round_setup_complete = True
                    st.session_state.resumed_round = True
                    st.session_state.timer_event_max_seconds = previous_round.get(
                        "time_max_seconds", 480
                    )
                    st.rerun()
            with fresh_col:
                if st.button("Start Fresh", use_container_width=True):
                    st.session_state.resumed_round = True
                    st.rerun()

    # Event selection
    all_event_names = get_all_event_display_names()
    selected_display_name = st.selectbox(
        "Event Category",
        options=["-- Select Event --"] + all_event_names,
        index=0
        if st.session_state.selected_event_display_name is None
        else all_event_names.index(st.session_state.selected_event_display_name) + 1,
        disabled=st.session_state.round_setup_complete,
    )

    if selected_display_name != "-- Select Event --":
        selected_event_key = get_event_key_by_display_name(selected_display_name)
        st.session_state.selected_event_key = selected_event_key
        st.session_state.selected_event_display_name = selected_display_name
    else:
        selected_event_key = None

    # Number of students
    student_count = st.number_input(
        "Number of Students",
        min_value=1,
        max_value=20,
        value=max(st.session_state.student_count, 1),
        step=1,
        disabled=st.session_state.round_setup_complete,
    )

    # Student name inputs (only before round starts)
    if not st.session_state.round_setup_complete and selected_event_key:
        st.subheader("Student Names")

        # Initialize students list if count changed
        if len(st.session_state.students) != student_count:
            new_students = []
            for student_idx in range(student_count):
                if student_idx < len(st.session_state.students):
                    new_students.append(st.session_state.students[student_idx])
                else:
                    new_students.append(create_empty_student(student_idx))
            st.session_state.students = new_students
            st.session_state.student_count = student_count

        for student_idx in range(student_count):
            student_name = st.text_input(
                f"Student {student_idx + 1}",
                value=st.session_state.students[student_idx]["student_name"],
                key=f"student_name_{student_idx}",
            )
            st.session_state.students[student_idx]["student_name"] = student_name
            st.session_state.students[student_idx]["student_index"] = student_idx

        # Start round button
        if st.button("Start Round", type="primary", use_container_width=True):
            # Validate at least one name
            has_any_name = any(
                student["student_name"].strip()
                for student in st.session_state.students
            )
            if has_any_name:
                st.session_state.round_setup_complete = True
                st.session_state.round_started_at = datetime.now().isoformat()
                st.session_state.student_count = student_count

                # Set timer max from event
                event_details = get_event_by_key(selected_event_key)
                st.session_state.timer_event_max_seconds = event_details[
                    "time_max_seconds"
                ]

                st.session_state.data_dirty = True
                st.rerun()
            else:
                st.error("Enter at least one student name.")

    # Show current round info if setup complete
    if st.session_state.round_setup_complete:
        st.success(
            f"Judging: {st.session_state.selected_event_display_name}"
        )
        st.caption(f"Students: {st.session_state.student_count}")

        # Reset round button
        st.divider()
        if st.button("Reset Round", type="secondary", use_container_width=True):
            # Save current data first
            trigger_auto_save()
            # Reset all state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Quick rules reference
    st.divider()
    with st.expander("MIFA Quick Reference"):
        st.markdown(MIFA_RULES_SUMMARY)

    # Past rounds browser
    st.divider()
    with st.expander("Past Rounds"):
        saved_rounds = list_saved_rounds()
        if not saved_rounds:
            st.caption("No saved rounds yet.")
        else:
            round_display_options = [
                f"{r['event_display_name']} - {r['round_started_at'][:10]} "
                f"({r['student_count']} students)"
                for r in saved_rounds
            ]
            selected_past_round_index = st.selectbox(
                "Select a round",
                options=range(len(round_display_options)),
                format_func=lambda idx: round_display_options[idx],
                key="past_round_selector",
            )

            view_col, edit_col = st.columns(2)
            with view_col:
                if st.button("View & Export", use_container_width=True):
                    selected_round_meta = saved_rounds[selected_past_round_index]
                    past_round_data = load_round_data(selected_round_meta["filepath"])
                    st.session_state.selected_event_key = past_round_data["event_key"]
                    st.session_state.selected_event_display_name = past_round_data[
                        "event_display_name"
                    ]
                    st.session_state.round_started_at = past_round_data["round_started_at"]
                    st.session_state.students = past_round_data.get("students", [])
                    st.session_state.student_count = len(st.session_state.students)
                    st.session_state.round_setup_complete = True
                    st.session_state.resumed_round = True
                    st.session_state.timer_event_max_seconds = past_round_data.get(
                        "time_max_seconds", 480
                    )
                    st.session_state.viewing_past_round = True
                    st.session_state.data_dirty = False
                    st.rerun()

            with edit_col:
                if st.button("Continue Editing", use_container_width=True):
                    selected_round_meta = saved_rounds[selected_past_round_index]
                    past_round_data = load_round_data(selected_round_meta["filepath"])
                    st.session_state.selected_event_key = past_round_data["event_key"]
                    st.session_state.selected_event_display_name = past_round_data[
                        "event_display_name"
                    ]
                    st.session_state.round_started_at = past_round_data["round_started_at"]
                    st.session_state.students = past_round_data.get("students", [])
                    st.session_state.student_count = len(st.session_state.students)
                    st.session_state.round_setup_complete = True
                    st.session_state.resumed_round = True
                    st.session_state.timer_event_max_seconds = past_round_data.get(
                        "time_max_seconds", 480
                    )
                    st.session_state.viewing_past_round = False
                    st.session_state.data_dirty = False
                    st.rerun()


# ---------------------------------------------------------------------------
# Main content area with tabs
# ---------------------------------------------------------------------------
if st.session_state.get("viewing_past_round"):
    st.info(
        "Viewing a saved round (read-only). "
        "Go to Summary / Export to copy your feedback. "
        "Use 'Continue Editing' in Past Rounds to make changes."
    )

tab_event_ref, tab_judge, tab_scores, tab_summary = st.tabs(
    ["Event Reference", "Judge", "Scores", "Summary / Export"]
)


# ===========================================================================
# TAB 1: Event Reference
# ===========================================================================
with tab_event_ref:
    st.header("Event Reference Guide")
    st.caption("Select any event to see its description, rules, and judging tips.")

    # Group events by category
    oral_interp_events = get_events_by_category(CATEGORY_ORAL_INTERPRETATION)
    public_address_events = get_events_by_category(CATEGORY_PUBLIC_ADDRESS)

    reference_event_names = []
    reference_event_keys = []

    # Build grouped options
    oral_interp_names = sorted(
        [(v["display_name"], k) for k, v in oral_interp_events.items()]
    )
    public_address_names = sorted(
        [(v["display_name"], k) for k, v in public_address_events.items()]
    )

    for display_name, event_key in oral_interp_names:
        reference_event_names.append(f"[Interp] {display_name}")
        reference_event_keys.append(event_key)
    for display_name, event_key in public_address_names:
        reference_event_names.append(f"[Public Address] {display_name}")
        reference_event_keys.append(event_key)

    selected_reference_index = st.selectbox(
        "Choose an event to review",
        options=range(len(reference_event_names)),
        format_func=lambda idx: reference_event_names[idx],
        key="reference_event_selector",
    )

    if selected_reference_index is not None:
        reference_event_key = reference_event_keys[selected_reference_index]
        reference_event = get_event_by_key(reference_event_key)

        if reference_event:
            # Header
            st.subheader(reference_event["display_name"])

            # Time limits
            time_min_minutes = reference_event["time_min_seconds"] // 60
            time_max_minutes = reference_event["time_max_seconds"] // 60
            if time_min_minutes == time_max_minutes:
                st.metric("Time Limit", f"{time_max_minutes} minutes")
            else:
                st.metric(
                    "Time Limit", f"{time_min_minutes} - {time_max_minutes} minutes"
                )

            # Description
            st.markdown("**Description**")
            st.info(reference_event["description"])

            # Judging criteria, dos, don'ts in columns
            criteria_col, dos_col, donts_col = st.columns(3)

            with criteria_col:
                st.markdown("**What to Evaluate**")
                for criterion in reference_event["judging_criteria"]:
                    st.markdown(f"- {criterion}")

            with dos_col:
                st.markdown("**DO**")
                for do_item in reference_event["dos"]:
                    st.markdown(f"- {do_item}")

            with donts_col:
                st.markdown("**DON'T**")
                for dont_item in reference_event["donts"]:
                    st.markdown(f"- {dont_item}")

            # Rules
            st.markdown("**Key Rules**")
            for rule in reference_event["rules"]:
                st.markdown(f"- {rule}")


# ===========================================================================
# TAB 2: Judge (Active Judging)
# ===========================================================================
with tab_judge:
    if not st.session_state.round_setup_complete:
        st.info(
            "Set up your round first using the sidebar: select an event, "
            "enter the number of students, fill in their names, and click "
            "'Start Round'."
        )
    else:
        # Determine if this is an interpretation or public address event
        event_details = get_event_by_key(st.session_state.selected_event_key)
        is_interpretation_event = (
            event_details["category"] == CATEGORY_ORAL_INTERPRETATION
        )
        is_public_address_event = (
            event_details["category"] == CATEGORY_PUBLIC_ADDRESS
        )
        event_max_seconds = event_details["time_max_seconds"]

        # Top row: Student selector (left) + Judging Hints (right)
        student_selector_column, hints_column = st.columns([3, 2])

        student_names_list = [
            f"{idx + 1}. {student['student_name'] or f'Student {idx + 1}'}"
            for idx, student in enumerate(st.session_state.students)
        ]

        with student_selector_column:
            selected_student_display = st.selectbox(
                "Current Student",
                options=range(len(student_names_list)),
                format_func=lambda idx: student_names_list[idx],
                index=st.session_state.current_student_index,
                key="judge_student_selector",
            )

        with hints_column:
            with st.expander("Judging Hints", expanded=False):
                render_judging_hints(
                    st.session_state.selected_event_key, event_details
                )
            with st.expander("Feedback Cheat Sheet", expanded=False):
                cheatsheet_student_idx = st.session_state.current_student_index
                cheatsheet_student = st.session_state.students[cheatsheet_student_idx]
                render_feedback_cheatsheet(
                    st.session_state.selected_event_key, event_details,
                    cheatsheet_student_idx, cheatsheet_student,
                )

        # Handle student switch
        if selected_student_display != st.session_state.current_student_index:
            previous_student_idx = st.session_state.current_student_index
            if st.session_state.timer_running:
                st.session_state.timer_stop_timestamp = time.time()
                st.session_state.timer_running = False
                elapsed = (
                    st.session_state.timer_stop_timestamp
                    - st.session_state.timer_start_timestamp
                )
                st.session_state.students[previous_student_idx][
                    "elapsed_seconds"
                ] = elapsed
                st.session_state.students[previous_student_idx][
                    "timer_stopped"
                ] = True

            st.session_state.current_student_index = selected_student_display

            new_student = st.session_state.students[selected_student_display]
            if new_student.get("timer_stopped") and new_student.get("elapsed_seconds"):
                st.session_state.timer_start_timestamp = 0
                st.session_state.timer_stop_timestamp = new_student["elapsed_seconds"]
                st.session_state.timer_running = False
            else:
                reset_timer_for_student()

            st.session_state.data_dirty = True

        current_student = st.session_state.students[
            st.session_state.current_student_index
        ]
        student_index = st.session_state.current_student_index

        # Ensure ballot_info and note dicts exist (for resumed/legacy data)
        if "ballot_info" not in current_student:
            current_student["ballot_info"] = {
                "draw_number": "", "code": "", "round_number": "",
                "section": "", "selection_title": "", "author": "", "topic": "",
            }
        if "interp_notes" not in current_student:
            current_student["interp_notes"] = {
                "quality_of_literature": "", "physical_performance": "",
                "vocal_performance": "", "total_effect": "",
                "reason_for_rank_score": "",
            }
        if "public_address_notes" not in current_student:
            current_student["public_address_notes"] = {
                "topic_analysis": "", "physical_performance": "",
                "vocal_performance": "", "organization": "",
                "development": "", "total_effect": "",
                "reason_for_rank_score": "",
            }

        ballot_info = current_student["ballot_info"]

        # =================================================================
        # TOP SECTION: Ballot Info (matches the critique sheet header)
        # =================================================================
        if is_interpretation_event:
            st.subheader("Interpretation Critique Sheet")
        else:
            st.subheader("Public Address Critique Sheet")

        st.caption(f"EVENT: {st.session_state.selected_event_display_name}")

        # Row 1: Draw #, Round, Section, Code
        ballot_row1 = st.columns(4)
        with ballot_row1[0]:
            ballot_info["draw_number"] = st.text_input(
                "Draw #",
                value=ballot_info.get("draw_number", ""),
                key=f"draw_{student_index}",
            )
        with ballot_row1[1]:
            ballot_info["round_number"] = st.text_input(
                "Round",
                value=ballot_info.get("round_number", ""),
                key=f"round_{student_index}",
            )
        with ballot_row1[2]:
            ballot_info["section"] = st.text_input(
                "Section",
                value=ballot_info.get("section", ""),
                key=f"section_{student_index}",
            )
        with ballot_row1[3]:
            ballot_info["code"] = st.text_input(
                "Code",
                value=ballot_info.get("code", ""),
                key=f"code_{student_index}",
            )

        # Row 2: Name + event-specific fields (Selection/Author or Topic)
        if is_interpretation_event:
            ballot_row2 = st.columns(3)
            with ballot_row2[0]:
                st.text_input(
                    "Name",
                    value=current_student["student_name"],
                    key=f"ballot_name_{student_index}",
                    disabled=True,
                )
            with ballot_row2[1]:
                ballot_info["selection_title"] = st.text_input(
                    "Selection",
                    value=ballot_info.get("selection_title", ""),
                    key=f"selection_{student_index}",
                )
            with ballot_row2[2]:
                ballot_info["author"] = st.text_input(
                    "Author",
                    value=ballot_info.get("author", ""),
                    key=f"author_{student_index}",
                )
        else:
            ballot_row2 = st.columns(2)
            with ballot_row2[0]:
                st.text_input(
                    "Name",
                    value=current_student["student_name"],
                    key=f"ballot_name_{student_index}",
                    disabled=True,
                )
            with ballot_row2[1]:
                ballot_info["topic"] = st.text_input(
                    "Topic",
                    value=ballot_info.get("topic", ""),
                    key=f"topic_{student_index}",
                )

        # Row 3: Points, Rank, Time (read-only summary)
        ballot_row3 = st.columns(4)
        with ballot_row3[0]:
            rank_display = current_student.get("rank") or "--"
            st.metric("Rank (1-4)", rank_display)
        with ballot_row3[1]:
            pct_display = (
                f"{current_student['percentage']}%"
                if current_student.get("percentage")
                else "--"
            )
            st.metric("Points (100-75)", pct_display)
        with ballot_row3[2]:
            time_val = format_time_display(current_student.get("elapsed_seconds"))
            st.metric("Time", time_val)
        with ballot_row3[3]:
            timed_count = sum(
                1
                for s in st.session_state.students
                if s.get("timer_stopped")
            )
            st.metric(
                "Progress",
                f"{timed_count}/{len(st.session_state.students)} timed",
            )

        st.divider()

        # =================================================================
        # MIDDLE SECTION: Timer + Stopwatch
        # =================================================================
        st.subheader("Timer & Stopwatch")

        timer_result = render_timer_ui(event_max_seconds)

        # Save elapsed time when timer stops
        if timer_result["is_stopped"] and not current_student.get("timer_stopped"):
            current_student["elapsed_seconds"] = timer_result["elapsed_seconds"]
            current_student["timer_started"] = True
            current_student["timer_stopped"] = True
            st.session_state.data_dirty = True

        st.divider()

        # =================================================================
        # BOTTOM SECTION: Category-Specific Criteria Notes
        # =================================================================
        if is_interpretation_event:
            st.subheader("Interpretation Criteria")
            st.caption(
                "QUALITY OF LITERATURE, PHYSICAL PERFORMANCE, "
                "VOCAL PERFORMANCE, AND TOTAL EFFECT"
            )

            interp_notes = current_student["interp_notes"]

            interp_col_left, interp_col_right = st.columns(2)

            with interp_col_left:
                interp_notes["quality_of_literature"] = st.text_area(
                    "Quality of Literature",
                    value=interp_notes.get("quality_of_literature", ""),
                    height=100,
                    key=f"interp_lit_{student_index}",
                    help="Is the selection of good literary merit? Appropriate for competition?",
                )
                interp_notes["physical_performance"] = st.text_area(
                    "Physical Performance",
                    value=interp_notes.get("physical_performance", ""),
                    height=100,
                    key=f"interp_phys_{student_index}",
                    help="Gestures, movement, character physicality, use of space",
                )

            with interp_col_right:
                interp_notes["vocal_performance"] = st.text_area(
                    "Vocal Performance",
                    value=interp_notes.get("vocal_performance", ""),
                    height=100,
                    key=f"interp_vocal_{student_index}",
                    help="Vocal variety, clarity, volume, pacing, character voices",
                )
                interp_notes["total_effect"] = st.text_area(
                    "Total Effect",
                    value=interp_notes.get("total_effect", ""),
                    height=100,
                    key=f"interp_effect_{student_index}",
                    help="Overall impact, emotional connection, audience engagement",
                )

            interp_notes["reason_for_rank_score"] = st.text_area(
                "Reason for Rank/Score",
                value=interp_notes.get("reason_for_rank_score", ""),
                height=150,
                key=f"interp_reason_{student_index}",
                help="Explain why you gave this rank and score",
            )

            current_student["interp_notes"] = interp_notes

        else:
            st.subheader("Public Address Criteria")
            st.caption(
                "TOPIC, PHYSICAL PERFORMANCE, VOCAL PERFORMANCE, "
                "ORGANIZATION, DEVELOPMENT, AND TOTAL EFFECT"
            )

            pa_notes = current_student["public_address_notes"]

            pa_col_left, pa_col_right = st.columns(2)

            with pa_col_left:
                pa_notes["topic_analysis"] = st.text_area(
                    "Topic",
                    value=pa_notes.get("topic_analysis", ""),
                    height=80,
                    key=f"pa_topic_{student_index}",
                    help="Suitability, originality, depth of topic",
                )
                pa_notes["physical_performance"] = st.text_area(
                    "Physical Performance",
                    value=pa_notes.get("physical_performance", ""),
                    height=80,
                    key=f"pa_phys_{student_index}",
                    help="Eye contact, gestures, movement, confidence",
                )
                pa_notes["vocal_performance"] = st.text_area(
                    "Vocal Performance",
                    value=pa_notes.get("vocal_performance", ""),
                    height=80,
                    key=f"pa_vocal_{student_index}",
                    help="Projection, clarity, pacing, emphasis",
                )

            with pa_col_right:
                pa_notes["organization"] = st.text_area(
                    "Organization",
                    value=pa_notes.get("organization", ""),
                    height=80,
                    key=f"pa_org_{student_index}",
                    help="Structure, transitions, logical flow",
                )
                pa_notes["development"] = st.text_area(
                    "Development",
                    value=pa_notes.get("development", ""),
                    height=80,
                    key=f"pa_dev_{student_index}",
                    help="Evidence, examples, supporting material",
                )
                pa_notes["total_effect"] = st.text_area(
                    "Total Effect",
                    value=pa_notes.get("total_effect", ""),
                    height=80,
                    key=f"pa_effect_{student_index}",
                    help="Overall impact, persuasiveness, audience engagement",
                )

            pa_notes["reason_for_rank_score"] = st.text_area(
                "Reason for Rank/Score",
                value=pa_notes.get("reason_for_rank_score", ""),
                height=150,
                key=f"pa_reason_{student_index}",
                help="Explain why you gave this rank and score",
            )

            current_student["public_address_notes"] = pa_notes

        st.session_state.data_dirty = True

        # Navigation buttons
        st.divider()
        nav_col_prev, nav_col_save, nav_col_next = st.columns(3)

        with nav_col_prev:
            if student_index > 0:
                if st.button("Previous Student", use_container_width=True):
                    st.session_state.current_student_index -= 1
                    reset_timer_for_student()
                    prev_student = st.session_state.students[
                        st.session_state.current_student_index
                    ]
                    if prev_student.get("timer_stopped") and prev_student.get(
                        "elapsed_seconds"
                    ):
                        st.session_state.timer_start_timestamp = 0
                        st.session_state.timer_stop_timestamp = prev_student[
                            "elapsed_seconds"
                        ]
                    st.rerun()

        with nav_col_save:
            if st.button("Save Notes", type="primary", use_container_width=True):
                st.session_state.data_dirty = True
                trigger_auto_save()
                st.success("Saved!")

        with nav_col_next:
            if student_index < len(st.session_state.students) - 1:
                if st.button("Next Student", use_container_width=True):
                    st.session_state.current_student_index += 1
                    reset_timer_for_student()
                    next_student = st.session_state.students[
                        st.session_state.current_student_index
                    ]
                    if next_student.get("timer_stopped") and next_student.get(
                        "elapsed_seconds"
                    ):
                        st.session_state.timer_start_timestamp = 0
                        st.session_state.timer_stop_timestamp = next_student[
                            "elapsed_seconds"
                        ]
                    st.rerun()


# ===========================================================================
# TAB 3: Scores
# ===========================================================================
with tab_scores:
    if not st.session_state.round_setup_complete:
        st.info("Set up your round first using the sidebar.")
    else:
        st.header("Scoring")
        st.caption(
            "Rank top 3 as 1, 2, 3. Everyone else gets 4. "
            "Rank 1 must receive 100%. No duplicate percentages. Range: 75-100."
        )

        # Scoring table
        for student_idx, student in enumerate(st.session_state.students):
            student_display_name = (
                student["student_name"] or f"Student {student_idx + 1}"
            )
            time_display = format_time_display(student.get("elapsed_seconds"))

            with st.container():
                score_cols = st.columns([3, 1, 1, 1])

                with score_cols[0]:
                    st.markdown(
                        f"**{student_idx + 1}. {student_display_name}** "
                        f"({time_display})"
                    )

                with score_cols[1]:
                    rank_options = [None, 1, 2, 3, 4]
                    current_rank = student.get("rank")
                    rank_index = (
                        rank_options.index(current_rank)
                        if current_rank in rank_options
                        else 0
                    )
                    selected_rank = st.selectbox(
                        "Rank",
                        options=rank_options,
                        index=rank_index,
                        format_func=lambda x: "-- Rank --" if x is None else str(x),
                        key=f"rank_{student_idx}",
                        label_visibility="collapsed",
                    )
                    student["rank"] = selected_rank

                with score_cols[2]:
                    current_percentage = student.get("percentage")
                    selected_percentage = st.number_input(
                        "Percentage",
                        min_value=0,
                        max_value=100,
                        value=current_percentage if current_percentage else 0,
                        step=1,
                        key=f"percentage_{student_idx}",
                        label_visibility="collapsed",
                    )
                    student["percentage"] = (
                        selected_percentage if selected_percentage > 0 else None
                    )

                with score_cols[3]:
                    if student.get("rank") and student.get("percentage"):
                        st.markdown(
                            f"Rank **{student['rank']}** / **{student['percentage']}%**"
                        )

        st.session_state.data_dirty = True

        # Validation
        st.divider()
        st.subheader("Validation")

        # Build scores list for validation
        score_entries = []
        for student in st.session_state.students:
            score_entries.append(
                {
                    "student_name": student["student_name"],
                    "student_index": student["student_index"],
                    "rank": student.get("rank"),
                    "percentage": student.get("percentage"),
                    "elapsed_seconds": student.get("elapsed_seconds"),
                }
            )

        validation_messages = validate_all(score_entries)

        if validation_messages:
            for message in validation_messages:
                if "warning" in message.lower():
                    st.warning(message)
                else:
                    st.error(message)
        else:
            scored_students = [
                student
                for student in score_entries
                if student.get("rank") is not None and student.get("percentage") is not None
            ]
            if len(scored_students) == len(score_entries):
                st.success("All scores are valid per MIFA rules!")
            else:
                st.info("Enter ranks and percentages for all students to validate.")

        # Save scores button
        if st.button(
            "Save Scores", type="primary", use_container_width=True, key="save_scores"
        ):
            st.session_state.data_dirty = True
            trigger_auto_save()
            st.success("Scores saved!")


# ===========================================================================
# TAB 4: Summary / Export
# ===========================================================================
with tab_summary:
    if not st.session_state.round_setup_complete:
        st.info("Set up your round first using the sidebar.")
    else:
        st.header("Summary & Export")
        st.caption("Review your results and copy them for Tabroom.")

        # Build round data
        round_data = collect_round_data()

        # Check if scoring is complete
        all_scored = all(
            student.get("rank") is not None and student.get("percentage") is not None
            for student in st.session_state.students
        )

        if not all_scored:
            st.warning(
                "Not all students have been scored yet. "
                "Go to the Scores tab to complete scoring."
            )

        # Ranked summary table
        st.subheader("Ranked Results")

        # Sort students by rank then percentage
        ranked_students = sorted(
            st.session_state.students,
            key=lambda student: (
                student.get("rank") or 99,
                -(student.get("percentage") or 0),
            ),
        )

        # Display as a table
        table_header_cols = st.columns([1, 3, 1, 1, 1])
        with table_header_cols[0]:
            st.markdown("**Rank**")
        with table_header_cols[1]:
            st.markdown("**Name**")
        with table_header_cols[2]:
            st.markdown("**%**")
        with table_header_cols[3]:
            st.markdown("**Time**")
        with table_header_cols[4]:
            st.markdown("**Status**")

        for student in ranked_students:
            row_cols = st.columns([1, 3, 1, 1, 1])
            with row_cols[0]:
                rank_display = student.get("rank") or "--"
                st.write(rank_display)
            with row_cols[1]:
                st.write(
                    student["student_name"]
                    or f"Student {student['student_index'] + 1}"
                )
            with row_cols[2]:
                percentage_display = (
                    f"{student.get('percentage')}%" if student.get("percentage") else "--"
                )
                st.write(percentage_display)
            with row_cols[3]:
                st.write(format_time_display(student.get("elapsed_seconds")))
            with row_cols[4]:
                if student.get("rank") and student.get("percentage"):
                    st.write("Done")
                else:
                    st.write("Pending")

        # Copy-friendly export sections
        st.divider()

        # Tabroom summary
        st.subheader("Copy for Tabroom")
        st.caption("Click the copy icon in the top-right of the box below.")
        tabroom_summary_text = format_tabroom_summary(round_data)
        st.code(tabroom_summary_text, language=None)

        # Per-student feedback
        st.subheader("Student Feedback")
        event_display_name = st.session_state.selected_event_display_name or ""

        for student in ranked_students:
            student_display_name = (
                student["student_name"]
                or f"Student {student['student_index'] + 1}"
            )
            with st.expander(
                f"{student_display_name} "
                f"(Rank {student.get('rank', '--')}, "
                f"{student.get('percentage', '--')}%)"
            ):
                feedback_text = format_student_feedback(student, event_display_name)
                st.code(feedback_text, language=None)

        # Copy all feedback
        st.subheader("Copy All Feedback")
        all_feedback_text = format_all_feedback(round_data)
        st.code(all_feedback_text, language=None)

        # Final save
        if st.button(
            "Save Everything",
            type="primary",
            use_container_width=True,
            key="final_save",
        ):
            st.session_state.data_dirty = True
            trigger_auto_save()
            st.success("All data saved successfully!")
