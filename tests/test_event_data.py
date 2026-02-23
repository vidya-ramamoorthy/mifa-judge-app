"""
Tests for the MIFA event data module.

Validates that all 16 events are defined correctly (14 standard + 2 Original
Interpretation), each event contains the required keys with appropriate types
and values, and that all helper lookup functions behave as expected.
"""

import pytest

from event_data import (
    CATEGORY_ORAL_INTERPRETATION,
    CATEGORY_PUBLIC_ADDRESS,
    EVENT_DATA,
    MIFA_RULES_SUMMARY,
    REQUIRED_EVENT_KEYS,
    VALID_CATEGORIES,
    get_all_event_display_names,
    get_event_by_key,
    get_event_key_by_display_name,
    get_events_by_category,
)

# ---------------------------------------------------------------------------
# Constants for test expectations
# ---------------------------------------------------------------------------
EXPECTED_TOTAL_EVENT_COUNT = 16

EXPECTED_ORAL_INTERPRETATION_EVENT_KEYS = {
    "dramatic_interpretation",
    "duo_interpretation",
    "multiple_interpretation",
    "poetry_interpretation",
    "program_oral_interpretation",
    "prose_interpretation",
    "storytelling",
    "oi_poetry",
    "oi_prose",
}

EXPECTED_PUBLIC_ADDRESS_EVENT_KEYS = {
    "broadcasting",
    "duo_commentary",
    "extemporaneous_speaking",
    "impromptu_speaking",
    "informative_speaking",
    "oratory",
    "sales_speaking",
}

ALL_EXPECTED_EVENT_KEYS = (
    EXPECTED_ORAL_INTERPRETATION_EVENT_KEYS | EXPECTED_PUBLIC_ADDRESS_EVENT_KEYS
)


# ---------------------------------------------------------------------------
# Test: All 16 events are present
# ---------------------------------------------------------------------------
class TestEventPresence:
    """Verify that all 16 expected events exist in EVENT_DATA."""

    def test_total_event_count(self):
        assert len(EVENT_DATA) == EXPECTED_TOTAL_EVENT_COUNT, (
            f"Expected {EXPECTED_TOTAL_EVENT_COUNT} events, "
            f"found {len(EVENT_DATA)}"
        )

    def test_all_expected_event_keys_exist(self):
        actual_event_keys = set(EVENT_DATA.keys())
        missing_event_keys = ALL_EXPECTED_EVENT_KEYS - actual_event_keys
        assert not missing_event_keys, (
            f"Missing event keys: {missing_event_keys}"
        )

    def test_no_unexpected_event_keys(self):
        actual_event_keys = set(EVENT_DATA.keys())
        unexpected_event_keys = actual_event_keys - ALL_EXPECTED_EVENT_KEYS
        assert not unexpected_event_keys, (
            f"Unexpected event keys found: {unexpected_event_keys}"
        )

    def test_oral_interpretation_events_present(self):
        oral_interpretation_keys = {
            event_key
            for event_key, event_details in EVENT_DATA.items()
            if event_details["category"] == CATEGORY_ORAL_INTERPRETATION
        }
        assert oral_interpretation_keys == EXPECTED_ORAL_INTERPRETATION_EVENT_KEYS

    def test_public_address_events_present(self):
        public_address_keys = {
            event_key
            for event_key, event_details in EVENT_DATA.items()
            if event_details["category"] == CATEGORY_PUBLIC_ADDRESS
        }
        assert public_address_keys == EXPECTED_PUBLIC_ADDRESS_EVENT_KEYS


# ---------------------------------------------------------------------------
# Test: Each event has all required keys
# ---------------------------------------------------------------------------
class TestEventRequiredKeys:
    """Verify that every event entry contains all required keys."""

    @pytest.mark.parametrize("event_key", sorted(ALL_EXPECTED_EVENT_KEYS))
    def test_event_contains_all_required_keys(self, event_key: str):
        event_details = EVENT_DATA[event_key]
        actual_keys = set(event_details.keys())
        missing_keys = REQUIRED_EVENT_KEYS - actual_keys
        assert not missing_keys, (
            f"Event '{event_key}' is missing required keys: {missing_keys}"
        )

    @pytest.mark.parametrize("event_key", sorted(ALL_EXPECTED_EVENT_KEYS))
    def test_display_name_is_nonempty_string(self, event_key: str):
        display_name_value = EVENT_DATA[event_key]["display_name"]
        assert isinstance(display_name_value, str), (
            f"Event '{event_key}': display_name must be a string"
        )
        assert len(display_name_value) > 0, (
            f"Event '{event_key}': display_name must not be empty"
        )

    @pytest.mark.parametrize("event_key", sorted(ALL_EXPECTED_EVENT_KEYS))
    def test_description_is_nonempty_string(self, event_key: str):
        description_value = EVENT_DATA[event_key]["description"]
        assert isinstance(description_value, str)
        assert len(description_value) > 0

    @pytest.mark.parametrize("event_key", sorted(ALL_EXPECTED_EVENT_KEYS))
    def test_judging_criteria_is_nonempty_list(self, event_key: str):
        judging_criteria_value = EVENT_DATA[event_key]["judging_criteria"]
        assert isinstance(judging_criteria_value, list)
        assert len(judging_criteria_value) > 0

    @pytest.mark.parametrize("event_key", sorted(ALL_EXPECTED_EVENT_KEYS))
    def test_dos_is_nonempty_list(self, event_key: str):
        dos_value = EVENT_DATA[event_key]["dos"]
        assert isinstance(dos_value, list)
        assert len(dos_value) > 0

    @pytest.mark.parametrize("event_key", sorted(ALL_EXPECTED_EVENT_KEYS))
    def test_donts_is_nonempty_list(self, event_key: str):
        donts_value = EVENT_DATA[event_key]["donts"]
        assert isinstance(donts_value, list)
        assert len(donts_value) > 0

    @pytest.mark.parametrize("event_key", sorted(ALL_EXPECTED_EVENT_KEYS))
    def test_rules_is_nonempty_list(self, event_key: str):
        rules_value = EVENT_DATA[event_key]["rules"]
        assert isinstance(rules_value, list)
        assert len(rules_value) > 0


# ---------------------------------------------------------------------------
# Test: Time values are valid and min <= max
# ---------------------------------------------------------------------------
class TestEventTimeValues:
    """Validate time constraints for every event."""

    @pytest.mark.parametrize("event_key", sorted(ALL_EXPECTED_EVENT_KEYS))
    def test_time_min_is_nonnegative_integer(self, event_key: str):
        time_min_value = EVENT_DATA[event_key]["time_min_seconds"]
        assert isinstance(time_min_value, int), (
            f"Event '{event_key}': time_min_seconds must be an integer"
        )
        assert time_min_value >= 0, (
            f"Event '{event_key}': time_min_seconds must be non-negative"
        )

    @pytest.mark.parametrize("event_key", sorted(ALL_EXPECTED_EVENT_KEYS))
    def test_time_max_is_positive_integer(self, event_key: str):
        time_max_value = EVENT_DATA[event_key]["time_max_seconds"]
        assert isinstance(time_max_value, int), (
            f"Event '{event_key}': time_max_seconds must be an integer"
        )
        assert time_max_value > 0, (
            f"Event '{event_key}': time_max_seconds must be positive"
        )

    @pytest.mark.parametrize("event_key", sorted(ALL_EXPECTED_EVENT_KEYS))
    def test_time_min_does_not_exceed_time_max(self, event_key: str):
        time_min_value = EVENT_DATA[event_key]["time_min_seconds"]
        time_max_value = EVENT_DATA[event_key]["time_max_seconds"]
        assert time_min_value <= time_max_value, (
            f"Event '{event_key}': time_min_seconds ({time_min_value}) "
            f"exceeds time_max_seconds ({time_max_value})"
        )

    def test_broadcasting_is_fixed_five_minutes(self):
        """Broadcasting is a special case: exactly 5 minutes (300 seconds)."""
        broadcasting_event = EVENT_DATA["broadcasting"]
        assert broadcasting_event["time_min_seconds"] == 300
        assert broadcasting_event["time_max_seconds"] == 300

    def test_impromptu_max_is_six_minutes(self):
        """Impromptu Speaking: 6 minutes total (prep + presentation), min is 0."""
        impromptu_event = EVENT_DATA["impromptu_speaking"]
        assert impromptu_event["time_min_seconds"] == 0
        assert impromptu_event["time_max_seconds"] == 360

    def test_oi_poetry_time_range(self):
        """OI Poetry: 2-4 minutes."""
        oi_poetry_event = EVENT_DATA["oi_poetry"]
        assert oi_poetry_event["time_min_seconds"] == 120
        assert oi_poetry_event["time_max_seconds"] == 240

    def test_oi_prose_time_range(self):
        """OI Prose: 3-5 minutes."""
        oi_prose_event = EVENT_DATA["oi_prose"]
        assert oi_prose_event["time_min_seconds"] == 180
        assert oi_prose_event["time_max_seconds"] == 300


# ---------------------------------------------------------------------------
# Test: Category values are valid
# ---------------------------------------------------------------------------
class TestEventCategories:
    """Ensure all category values belong to the valid set."""

    @pytest.mark.parametrize("event_key", sorted(ALL_EXPECTED_EVENT_KEYS))
    def test_category_is_valid(self, event_key: str):
        category_value = EVENT_DATA[event_key]["category"]
        assert category_value in VALID_CATEGORIES, (
            f"Event '{event_key}': invalid category '{category_value}'. "
            f"Must be one of {VALID_CATEGORIES}"
        )

    def test_nine_oral_interpretation_events(self):
        oral_interpretation_count = sum(
            1
            for event_details in EVENT_DATA.values()
            if event_details["category"] == CATEGORY_ORAL_INTERPRETATION
        )
        assert oral_interpretation_count == 9

    def test_seven_public_address_events(self):
        public_address_count = sum(
            1
            for event_details in EVENT_DATA.values()
            if event_details["category"] == CATEGORY_PUBLIC_ADDRESS
        )
        assert public_address_count == 7


# ---------------------------------------------------------------------------
# Test: get_event_by_key() returns correct results
# ---------------------------------------------------------------------------
class TestGetEventByKey:
    """Test the get_event_by_key helper function."""

    def test_returns_correct_event_for_valid_key(self):
        dramatic_interp_result = get_event_by_key("dramatic_interpretation")
        assert dramatic_interp_result is not None
        assert dramatic_interp_result["display_name"] == "Dramatic Interpretation"

    def test_returns_correct_event_for_oi_poetry(self):
        oi_poetry_result = get_event_by_key("oi_poetry")
        assert oi_poetry_result is not None
        assert oi_poetry_result["display_name"] == "OI Poetry (Original Interpretation)"

    def test_returns_correct_event_for_oi_prose(self):
        oi_prose_result = get_event_by_key("oi_prose")
        assert oi_prose_result is not None
        assert oi_prose_result["display_name"] == "OI Prose (Original Interpretation)"

    def test_returns_none_for_invalid_key(self):
        nonexistent_result = get_event_by_key("nonexistent_event")
        assert nonexistent_result is None

    def test_returns_none_for_empty_string(self):
        empty_string_result = get_event_by_key("")
        assert empty_string_result is None

    @pytest.mark.parametrize("event_key", sorted(ALL_EXPECTED_EVENT_KEYS))
    def test_returns_dict_for_every_valid_key(self, event_key: str):
        event_result = get_event_by_key(event_key)
        assert isinstance(event_result, dict)
        assert "display_name" in event_result


# ---------------------------------------------------------------------------
# Test: get_events_by_category() returns correct results
# ---------------------------------------------------------------------------
class TestGetEventsByCategory:
    """Test the get_events_by_category helper function."""

    def test_oral_interpretation_returns_nine_events(self):
        oral_interpretation_events = get_events_by_category(
            CATEGORY_ORAL_INTERPRETATION
        )
        assert len(oral_interpretation_events) == 9

    def test_public_address_returns_seven_events(self):
        public_address_events = get_events_by_category(CATEGORY_PUBLIC_ADDRESS)
        assert len(public_address_events) == 7

    def test_oral_interpretation_contains_expected_keys(self):
        oral_interpretation_events = get_events_by_category(
            CATEGORY_ORAL_INTERPRETATION
        )
        assert set(oral_interpretation_events.keys()) == EXPECTED_ORAL_INTERPRETATION_EVENT_KEYS

    def test_public_address_contains_expected_keys(self):
        public_address_events = get_events_by_category(CATEGORY_PUBLIC_ADDRESS)
        assert set(public_address_events.keys()) == EXPECTED_PUBLIC_ADDRESS_EVENT_KEYS

    def test_invalid_category_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid category"):
            get_events_by_category("invalid_category")

    def test_empty_string_category_raises_value_error(self):
        with pytest.raises(ValueError):
            get_events_by_category("")


# ---------------------------------------------------------------------------
# Test: get_all_event_display_names() returns correct results
# ---------------------------------------------------------------------------
class TestGetAllEventDisplayNames:
    """Test the get_all_event_display_names helper function."""

    def test_returns_correct_count_of_display_names(self):
        all_display_names = get_all_event_display_names()
        assert len(all_display_names) == EXPECTED_TOTAL_EVENT_COUNT

    def test_returns_sorted_list(self):
        all_display_names = get_all_event_display_names()
        assert all_display_names == sorted(all_display_names)

    def test_all_entries_are_nonempty_strings(self):
        all_display_names = get_all_event_display_names()
        for display_name in all_display_names:
            assert isinstance(display_name, str)
            assert len(display_name) > 0

    def test_display_names_are_unique(self):
        all_display_names = get_all_event_display_names()
        unique_display_names = set(all_display_names)
        assert len(unique_display_names) == len(all_display_names), (
            "Display names are not unique"
        )

    def test_oi_events_in_display_names(self):
        all_display_names = get_all_event_display_names()
        assert "OI Poetry (Original Interpretation)" in all_display_names
        assert "OI Prose (Original Interpretation)" in all_display_names


# ---------------------------------------------------------------------------
# Test: get_event_key_by_display_name() returns correct results
# ---------------------------------------------------------------------------
class TestGetEventKeyByDisplayName:
    """Test the get_event_key_by_display_name helper function."""

    def test_returns_correct_key_for_valid_display_name(self):
        result_key = get_event_key_by_display_name("Dramatic Interpretation")
        assert result_key == "dramatic_interpretation"

    def test_returns_correct_key_for_poi(self):
        result_key = get_event_key_by_display_name(
            "Program Oral Interpretation (POI)"
        )
        assert result_key == "program_oral_interpretation"

    def test_returns_correct_key_for_oi_poetry(self):
        result_key = get_event_key_by_display_name(
            "OI Poetry (Original Interpretation)"
        )
        assert result_key == "oi_poetry"

    def test_returns_correct_key_for_oi_prose(self):
        result_key = get_event_key_by_display_name(
            "OI Prose (Original Interpretation)"
        )
        assert result_key == "oi_prose"

    def test_returns_none_for_nonexistent_display_name(self):
        result_key = get_event_key_by_display_name("Nonexistent Event")
        assert result_key is None

    def test_returns_none_for_empty_string(self):
        result_key = get_event_key_by_display_name("")
        assert result_key is None

    def test_roundtrip_for_every_event(self):
        """For each event, verify display_name -> key -> event -> display_name."""
        for original_event_key, event_details in EVENT_DATA.items():
            original_display_name = event_details["display_name"]
            looked_up_key = get_event_key_by_display_name(original_display_name)
            assert looked_up_key == original_event_key, (
                f"Roundtrip failed for '{original_display_name}': "
                f"expected key '{original_event_key}', got '{looked_up_key}'"
            )


# ---------------------------------------------------------------------------
# Test: Display names are unique across all events
# ---------------------------------------------------------------------------
class TestDisplayNameUniqueness:
    """Ensure no two events share the same display name."""

    def test_no_duplicate_display_names(self):
        all_display_names = [
            event_details["display_name"]
            for event_details in EVENT_DATA.values()
        ]
        seen_display_names = set()
        duplicate_display_names = []
        for name in all_display_names:
            if name in seen_display_names:
                duplicate_display_names.append(name)
            seen_display_names.add(name)
        assert not duplicate_display_names, (
            f"Duplicate display names found: {duplicate_display_names}"
        )


# ---------------------------------------------------------------------------
# Test: MIFA_RULES_SUMMARY constant
# ---------------------------------------------------------------------------
class TestMifaRulesSummary:
    """Validate the MIFA_RULES_SUMMARY constant."""

    def test_rules_summary_is_nonempty_string(self):
        assert isinstance(MIFA_RULES_SUMMARY, str)
        assert len(MIFA_RULES_SUMMARY) > 0

    def test_rules_summary_contains_scoring_section(self):
        assert "SCORING RULES:" in MIFA_RULES_SUMMARY

    def test_rules_summary_contains_timing_section(self):
        assert "TIMING:" in MIFA_RULES_SUMMARY

    def test_rules_summary_contains_general_rules_section(self):
        assert "GENERAL RULES:" in MIFA_RULES_SUMMARY

    def test_rules_summary_contains_judge_procedures_section(self):
        assert "JUDGE PROCEDURES:" in MIFA_RULES_SUMMARY

    def test_rules_summary_mentions_rank_system(self):
        assert "Rank top 3" in MIFA_RULES_SUMMARY

    def test_rules_summary_mentions_fifteen_minute_rule(self):
        assert "15-minute rule" in MIFA_RULES_SUMMARY

    def test_rules_summary_mentions_tournament_director(self):
        assert "Tournament Director" in MIFA_RULES_SUMMARY

    def test_rules_summary_mentions_scoring_convention(self):
        assert "1/100, 2/99, 3/98" in MIFA_RULES_SUMMARY

    def test_rules_summary_mentions_judge_ready_protocol(self):
        assert "judge and timer ready" in MIFA_RULES_SUMMARY


# ---------------------------------------------------------------------------
# Test: Storytelling manuscript rule is correct
# ---------------------------------------------------------------------------
class TestStorytellingManuscriptRule:
    """Verify the Storytelling event correctly allows manuscripts."""

    def test_storytelling_permits_manuscripts(self):
        storytelling_rules = EVENT_DATA["storytelling"]["rules"]
        manuscript_rule_found = any(
            "PERMITTED" in rule.upper() and "manuscript" in rule.lower()
            for rule in storytelling_rules
        )
        assert manuscript_rule_found, (
            "Storytelling rules should indicate manuscripts are permitted"
        )


# ---------------------------------------------------------------------------
# Test: Ballot-specific details are captured
# ---------------------------------------------------------------------------
class TestBallotDetails:
    """Verify key ballot details from official MIFA ballots are present."""

    def test_broadcasting_mentions_editorial_prep(self):
        broadcasting_rules = EVENT_DATA["broadcasting"]["rules"]
        has_editorial_prep = any("15-minute" in rule for rule in broadcasting_rules)
        assert has_editorial_prep

    def test_duo_interpretation_prohibits_eye_contact(self):
        duo_rules = EVENT_DATA["duo_interpretation"]["rules"]
        has_eye_contact_rule = any("eye contact" in rule.lower() for rule in duo_rules)
        assert has_eye_contact_rule

    def test_poi_requires_binder(self):
        poi_rules = EVENT_DATA["program_oral_interpretation"]["rules"]
        has_binder_rule = any("binder" in rule.lower() for rule in poi_rules)
        assert has_binder_rule

    def test_poi_no_chairs(self):
        poi_rules = EVENT_DATA["program_oral_interpretation"]["rules"]
        has_no_chairs_rule = any(
            "no chairs" in rule.lower() for rule in poi_rules
        )
        assert has_no_chairs_rule

    def test_impromptu_timing_starts_on_topic_receipt(self):
        impromptu_rules = EVENT_DATA["impromptu_speaking"]["rules"]
        has_timing_rule = any(
            "topic is received" in rule.lower() for rule in impromptu_rules
        )
        assert has_timing_rule

    def test_sales_speaking_requires_actual_product(self):
        sales_rules = EVENT_DATA["sales_speaking"]["rules"]
        has_actual_product_rule = any(
            "ACTUAL" in rule for rule in sales_rules
        )
        assert has_actual_product_rule

    def test_informative_allows_visual_aids(self):
        informative_rules = EVENT_DATA["informative_speaking"]["rules"]
        has_visual_aids_rule = any(
            "visual aids" in rule.lower() for rule in informative_rules
        )
        assert has_visual_aids_rule

    def test_duo_commentary_seated(self):
        duo_commentary_rules = EVENT_DATA["duo_commentary"]["rules"]
        has_seated_rule = any("seated" in rule.lower() for rule in duo_commentary_rules)
        assert has_seated_rule

    def test_multiple_interpretation_participant_count(self):
        multiple_rules = EVENT_DATA["multiple_interpretation"]["rules"]
        has_count_rule = any("3-5" in rule for rule in multiple_rules)
        assert has_count_rule

    def test_oi_events_require_original_composition(self):
        for oi_key in ("oi_poetry", "oi_prose"):
            oi_rules = EVENT_DATA[oi_key]["rules"]
            has_original_rule = any(
                "original composition" in rule.lower() for rule in oi_rules
            )
            assert has_original_rule, (
                f"{oi_key} should require original composition"
            )
