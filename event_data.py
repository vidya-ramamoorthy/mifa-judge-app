"""
MIFA Event Data Module

Contains definitions for all MIFA (Michigan Interscholastic Forensics Association)
competitive speech events, organized into Oral Interpretation and Public Address categories,
plus Original Interpretation events.

This module has NO Streamlit dependency and serves as the single source of truth
for event metadata, judging criteria, rules, and helper lookup functions.
"""

from typing import Optional

# ---------------------------------------------------------------------------
# Category constants
# ---------------------------------------------------------------------------
CATEGORY_ORAL_INTERPRETATION = "oral_interpretation"
CATEGORY_PUBLIC_ADDRESS = "public_address"

VALID_CATEGORIES = {CATEGORY_ORAL_INTERPRETATION, CATEGORY_PUBLIC_ADDRESS}

# ---------------------------------------------------------------------------
# Event data dictionary -- all MIFA events
# ---------------------------------------------------------------------------
EVENT_DATA: dict = {
    # -----------------------------------------------------------------------
    # ORAL INTERPRETATION EVENTS
    # -----------------------------------------------------------------------
    "dramatic_interpretation": {
        "display_name": "Dramatic Interpretation",
        "category": CATEGORY_ORAL_INTERPRETATION,
        "time_min_seconds": 300,
        "time_max_seconds": 480,
        "description": (
            "Presentation of a serious or humorous selection from a play written "
            "for stage or electronic medium. Adaptations from other genres written "
            "for stage/electronic medium are permitted. Multiple character selections "
            "are permitted. A single published work is required."
        ),
        "judging_criteria": [
            "Quality of literature",
            "Character development and differentiation",
            "Emotional range",
            "Vocal variety and performance",
            "Physical presence and performance",
            "Total effect and dramatic impact",
        ],
        "dos": [
            "Note character differentiation and original characterizations",
            "Reward risk-taking and emotional connection",
            "Evaluate quality of literature selection",
            "Consider how well scenes are put together",
            "Note creative use of chair/stool/blox if used",
        ],
        "donts": [
            "Don't penalize for lack of props (they are prohibited)",
            "Don't expect costumes (street attire only)",
            "Don't let personal taste override performance quality",
            "Don't penalize for using or not using a manuscript",
        ],
        "rules": [
            "No hand props, costumes, decorative scripts, lighting, scenery, reader's stands, benches, platforms, or risers",
            "ONLY chairs, stools, and blox are acceptable platform furnishings",
            "Any physical manipulation of chair/stool/blox is allowable",
            "Manuscript or notes are optional",
            "Script must be available for judge review if requested",
            "Street attire that suggests mood and character is permissible; stage costumes prohibited",
            "Only voice and body sounds allowed; no mechanical aids or instruments",
            "Intro/transitional material included in time limits; may include singing/humming",
            "Original characterizations are encouraged",
            "Editing permitted but author's intent must be preserved",
            "Gender rewriting of primary characters is not permitted",
        ],
    },
    "duo_interpretation": {
        "display_name": "Duo Interpretation",
        "category": CATEGORY_ORAL_INTERPRETATION,
        "time_min_seconds": 420,
        "time_max_seconds": 600,
        "description": (
            "Two participants interpret a single selection of humorous or serious "
            "literature from any genre or a combination of genres. Each performer may "
            "portray one or more characters and perform narration, with performance "
            "responsibility as balanced as possible. Must name the author and source "
            "during the presentation. Direct eye contact and touching between "
            "performers are PROHIBITED. Accidental bumping or eye contact corrected "
            "quickly should not result in disqualification. Direct eye contact with "
            "the audience is at performers' discretion."
        ),
        "judging_criteria": [
            "Quality of literature",
            "Chemistry and teamwork between performers",
            "Character differentiation",
            "Balanced performance responsibility",
            "Vocal performance",
            "Physical performance",
            "Total effect",
        ],
        "dos": [
            "Watch for effective use of 'offstage focus' (not looking at each other)",
            "Note how well they work as a team",
            "Evaluate transitions between characters",
            "Consider how well you can tell characters apart",
            "Assess balance of performance responsibility between the two",
        ],
        "donts": [
            "Don't disqualify for accidental brief eye contact or bumping if corrected quickly",
            "Don't expect them to face each other",
            "Don't penalize for using or not using a manuscript",
        ],
        "rules": [
            "No direct eye contact between performers",
            "No touching between performers",
            "Direct eye contact with the audience is at performers' discretion",
            "No hand props, costumes, decorative scripts, lighting, scenery, reader's stands, benches, platforms, or risers",
            "ONLY chairs, stools, and blox are acceptable",
            "Any physical manipulation of chair/stool/blox is allowable",
            "Script is optional but must be available for judge review if requested",
            "Street attire that suggests mood and character is permissible; stage costumes prohibited",
            "Only voice and body sounds allowed; no mechanical aids or instruments",
            "Intro/transitional material included in time limits; may include singing/humming",
            "Performance responsibility should be as balanced as possible",
            "Must name the author and material source during the presentation",
            "Editing permitted but author's intent must be preserved",
            "Gender rewriting of primary characters is not permitted",
        ],
    },
    "multiple_interpretation": {
        "display_name": "Multiple Interpretation",
        "category": CATEGORY_ORAL_INTERPRETATION,
        "time_min_seconds": 600,
        "time_max_seconds": 900,
        "description": (
            "3-5 participants performing a humorous or serious literary selection. "
            "All participants must be in front of the audience at all times (not "
            "necessarily facing). Presentation of prose, poetry, drama, or a "
            "combination is permitted. Original material may only be used as an "
            "intro or transitional device. In odd State Tournament years: any genre "
            "including musical theater/film. In even years: excludes musical "
            "theater/film."
        ),
        "judging_criteria": [
            "Quality of literature",
            "Ensemble cohesion and teamwork",
            "Creative staging",
            "Vocal variety across the group",
            "Physical performance",
            "Character development and differentiation",
            "Total effect",
        ],
        "dos": [
            "Evaluate group dynamics and cohesion",
            "Note creative use of space",
            "Consider literary merit of selection",
            "Assess how well you can tell characters apart",
        ],
        "donts": [
            "Don't expect elaborate staging or choreography",
            "Don't penalize for not facing audience (they don't have to)",
        ],
        "rules": [
            "3-5 participants required",
            "Maximum section size is 5",
            "All participants must be in front of audience at all times",
            "No direct eye contact or touching between performers",
            "No hand props, costumes, decorative scripts, lighting, scenery, reader's stands, benches, platforms, or risers",
            "ONLY chairs, stools, and blox are acceptable",
            "Any physical manipulation of chair/stool/blox is allowable",
            "Script must be available for judge review if requested",
            "Street attire only; stage costumes prohibited",
            "Only voice and body sounds allowed; no mechanical aids or instruments",
            "Original material only permitted for intro/transitions",
            "Odd State Tournament years: any genre including musical theater/film",
            "Even State Tournament years: excludes musical theater/film",
            "Editing permitted but author's intent must be preserved",
        ],
    },
    "poetry_interpretation": {
        "display_name": "Poetry Interpretation",
        "category": CATEGORY_ORAL_INTERPRETATION,
        "time_min_seconds": 300,
        "time_max_seconds": 480,
        "description": (
            "Performance of a single poem or a compilation of poems. "
            "Either humorous or serious literature is acceptable."
        ),
        "judging_criteria": [
            "Quality of literature",
            "Understanding of poetic elements (rhythm, imagery, metaphor)",
            "Vocal performance and dynamics",
            "Physical performance",
            "Emotional connection and interpretation depth",
            "Total effect",
        ],
        "dos": [
            "Note appreciation for poetic structure",
            "Evaluate vocal variety and pacing",
            "Reward insight into the poem's meaning",
            "Consider quality of literature selection",
            "Note how well scenes/poems are put together",
        ],
        "donts": [
            "Don't penalize for choosing lesser-known poets",
            "Don't expect theatrical performance (this is interpretation)",
            "Don't penalize for using or not using a manuscript",
        ],
        "rules": [
            "No hand props, costumes, decorative scripts, lighting, scenery, reader's stands, benches, platforms, or risers",
            "ONLY chairs, stools, and blox are acceptable",
            "Any physical manipulation of chair/stool/blox is allowable",
            "Manuscript or notes are optional",
            "Script must be available for judge review if requested",
            "Street attire that suggests mood and character is permissible; stage costumes prohibited",
            "Only voice and body sounds allowed; no mechanical aids or instruments",
            "Intro/transitional material included in time limits; may include singing/humming",
            "Editing permitted but author's intent must be preserved",
            "Gender rewriting of primary characters is not permitted",
        ],
    },
    "program_oral_interpretation": {
        "display_name": "Program Oral Interpretation (POI)",
        "category": CATEGORY_ORAL_INTERPRETATION,
        "time_min_seconds": 300,
        "time_max_seconds": 480,
        "description": (
            "Presentation of multiple selections sharing a common theme or message, "
            "chosen from two or three genres: Prose, Poetry, and/or Dramatic. A "
            "minimum of two pieces from at least two separate genres is required. "
            "A binder or folder (one solid color) is REQUIRED and must stay in "
            "contact with the contestant at all times. Creative use of the binder "
            "is allowed and encouraged. Pages may contain the manuscript. Pictures "
            "and illustrations are NOT permitted in the binder."
        ),
        "judging_criteria": [
            "Quality of literature",
            "Thematic unity across selections",
            "Transitions between pieces",
            "Genre variety and even time distribution",
            "Creative use of the binder",
            "Vocal and physical performance",
            "Total effect",
        ],
        "dos": [
            "Evaluate how well the theme connects the pieces",
            "Note creative use of the binder",
            "Assess quality of transitions",
            "Consider even distribution of time between genres",
            "Note quality of literature selections",
        ],
        "donts": [
            "Don't penalize for binder manipulation (it's allowed and encouraged)",
            "Don't forget to check genre requirement (at least 2 pieces from 2 genres)",
            "Don't expect chairs, stools, or blox (they are NOT permitted in POI)",
        ],
        "rules": [
            "Binder/folder is REQUIRED, must be one solid color",
            "Binder must remain in contact with contestant at all times",
            "No chairs, stools, or blox (unique to POI)",
            "No hand props, decorative scripts, lighting, scenery, reader's stands, benches, platforms, or risers",
            "Minimum 2 pieces from at least 2 separate genres (Prose, Poetry, Drama)",
            "Even distribution of time between genres is highly encouraged",
            "No pictures or illustrations in the binder",
            "Script must be available for judge review if requested",
            "Street attire that suggests mood and character is permissible; stage costumes prohibited",
            "Only voice and body sounds allowed; sound from binder is permitted",
            "Intro/transitional material included in time limits; may include singing/humming",
            "Editing permitted but author's intent must be preserved",
        ],
    },
    "prose_interpretation": {
        "display_name": "Prose Interpretation",
        "category": CATEGORY_ORAL_INTERPRETATION,
        "time_min_seconds": 300,
        "time_max_seconds": 480,
        "description": (
            "Presentation of a selection from a work of fiction (novel, short story) "
            "or non-fiction (essay, memoir). The cutting may be from a single "
            "selection or a compilation. Either humorous or serious literature is "
            "acceptable."
        ),
        "judging_criteria": [
            "Quality of literature",
            "Narrative storytelling ability",
            "Character voices and differentiation",
            "Vocal performance and pacing",
            "Physical performance",
            "Emotional engagement",
            "Total effect",
        ],
        "dos": [
            "Evaluate storytelling skill",
            "Note character differentiation in narrated scenes",
            "Consider quality of the prose selection",
            "Assess how well scenes are put together",
        ],
        "donts": [
            "Don't expect full theatrical performance",
            "Don't penalize for using or not using a manuscript",
        ],
        "rules": [
            "No hand props, costumes, decorative scripts, lighting, scenery, reader's stands, benches, platforms, or risers",
            "ONLY chairs, stools, and blox are acceptable",
            "Any physical manipulation of chair/stool/blox is allowable",
            "Manuscript or notes are optional",
            "Script (with cuttings indicated) must be available for judge review if requested",
            "Street attire that suggests mood and character is permissible; stage costumes prohibited",
            "Only voice and body sounds allowed; no mechanical aids or instruments",
            "Intro/transitional material included in time limits; may include singing/humming",
            "Editing permitted but author's intent must be preserved",
            "Gender rewriting of primary characters is not permitted",
        ],
    },
    "storytelling": {
        "display_name": "Storytelling",
        "category": CATEGORY_ORAL_INTERPRETATION,
        "time_min_seconds": 300,
        "time_max_seconds": 480,
        "description": (
            "Delivery of a single selection or compilation of material suitable for "
            "children, including contemporary literature, myths, legends, fairy tales, "
            "and folktales. Acceptable selections must come from children's literature "
            "for any age."
        ),
        "judging_criteria": [
            "Quality of literature",
            "Audience engagement",
            "Vocal characterization and performance",
            "Physical performance",
            "Pacing and dramatic timing",
            "Total effect",
        ],
        "dos": [
            "Note how well they engage the audience",
            "Evaluate vocal character work",
            "Consider if the story choice is appropriate",
            "Assess how well characters are differentiated",
        ],
        "donts": [
            "Don't penalize for choosing simple stories (children's lit is the requirement)",
            "Don't penalize for using or not using a manuscript (both are permitted)",
        ],
        "rules": [
            "The use of manuscripts, notes, or books IS PERMITTED",
            "Must be children's literature for any age",
            "No hand props, costumes, decorative scripts, lighting, scenery, reader's stands, benches, platforms, or risers",
            "ONLY chairs, stools, and blox are acceptable",
            "Any physical manipulation of chair/stool/blox is allowable",
            "Script must be available for judge review if requested",
            "Street attire that suggests mood and character is permissible; stage costumes prohibited",
            "Only voice and body sounds allowed; no mechanical aids or instruments",
            "Intro/transitional material included in time limits; may include singing/humming",
            "Editing permitted but author's intent must be preserved",
        ],
    },
    # -----------------------------------------------------------------------
    # PUBLIC ADDRESS EVENTS
    # -----------------------------------------------------------------------
    "broadcasting": {
        "display_name": "Broadcasting",
        "category": CATEGORY_PUBLIC_ADDRESS,
        "time_min_seconds": 300,
        "time_max_seconds": 300,
        "description": (
            "Student reads broadcast copy with authority, intelligence, and audience "
            "appeal. Must demonstrate visual communication with the audience. Includes "
            "a 1-minute editorial component prepared during a 15-minute limited "
            "preparation period. This is a limited preparation event with an 8-minute "
            "staggered draw. The goal is to hit exactly 5 minutes, as if cutting to "
            "a commercial break on television."
        ),
        "judging_criteria": [
            "Topic analysis and editorial quality",
            "Reading fluency and vocal authority",
            "Physical performance and eye contact",
            "Organization of broadcast segments",
            "Professional demeanor and delivery",
            "Total effect",
        ],
        "dos": [
            "Evaluate how natural the reading sounds",
            "Note eye contact with the audience",
            "Assess editorial conviction and argumentation",
            "Consider organization of news segments and appropriate story length",
            "Note whether broadcast hits close to exactly 5 minutes",
        ],
        "donts": [
            "Don't expect perfection in pronunciation of unfamiliar names",
            "Don't penalize for brief pauses to maintain eye contact",
            "Don't let personal agreement or disagreement with the editorial opinion affect scoring",
        ],
        "rules": [
            "5 minutes total including approximately 1-minute editorial",
            "Limited preparation event: 15-minute editorial prep, 8-minute staggered draw",
            "Stay in the room until all contestants have spoken",
            "Goal is to hit exactly 5 minutes (like a TV broadcast cutting to commercial)",
        ],
    },
    "duo_commentary": {
        "display_name": "Duo Commentary",
        "category": CATEGORY_PUBLIC_ADDRESS,
        "time_min_seconds": 240,
        "time_max_seconds": 420,
        "description": (
            "Two students work together to provide perspective on a given topic. "
            "Topics are often vague and/or use unique wording. Students should explore "
            "the prompt thoroughly with analysis and supporting material. Must present "
            "from a SEATED position. May only use notes made during 30-minute prep "
            "time. Partners may look at each other during the presentation."
        ),
        "judging_criteria": [
            "Topic analysis and exploration",
            "Physical performance",
            "Vocal performance",
            "Organization",
            "Development and supporting material",
            "Chemistry and balanced participation",
            "Total effect",
        ],
        "dos": [
            "Note how well they explore the topic",
            "Evaluate balance between speakers",
            "Assess analytical depth and supporting material",
            "Consider quality of sources and research cited",
        ],
        "donts": [
            "Don't expect them to stand (seated position is required)",
            "Don't penalize for unconventional topic interpretation if well-supported",
            "Don't penalize for looking at each other (it's allowed)",
        ],
        "rules": [
            "Seated position is required",
            "30-minute preparation time with partner",
            "Only notes from prep time are allowed",
            "Partners may look at each other",
            "Topics are presented as plain text, often vague or uniquely worded",
            "Limited preparation event",
        ],
    },
    "extemporaneous_speaking": {
        "display_name": "Extemporaneous Speaking",
        "category": CATEGORY_PUBLIC_ADDRESS,
        "time_min_seconds": 240,
        "time_max_seconds": 420,
        "description": (
            "Questions on current events covering state, national, and international "
            "political and social issues. Topics reflect subjects in popular news "
            "media. This is a limited preparation event with 30 minutes of prep "
            "time to research and create a speech giving the student's stance on "
            "the topic."
        ),
        "judging_criteria": [
            "Topic analysis",
            "Physical performance",
            "Vocal performance",
            "Organization and structure",
            "Development with current evidence and examples",
            "Total effect",
        ],
        "dos": [
            "Evaluate depth of knowledge on the topic",
            "Note organizational structure",
            "Assess use of evidence and source citations",
            "Consider credibility of research included",
        ],
        "donts": [
            "Don't expect memorized speeches",
            "Don't penalize for occasional reference to notes",
            "Don't fact-check minor details in real-time",
        ],
        "rules": [
            "Limited preparation event: 30-minute prep time",
            "Students may use research materials during prep",
            "Stay in the room until all contestants have spoken",
            "Topics cover current events (state, national, international)",
        ],
    },
    "impromptu_speaking": {
        "display_name": "Impromptu Speaking",
        "category": CATEGORY_PUBLIC_ADDRESS,
        "time_min_seconds": 0,
        "time_max_seconds": 360,
        "description": (
            "Develops ability to provide reasoned responses with minimal preparation. "
            "Timing begins when the contestant receives the topic from the judge. "
            "The 6 minutes includes BOTH preparation and presentation. Prompts may "
            "be short quotes, resolutions, images, phrases, and/or visual prompts."
        ),
        "judging_criteria": [
            "Topic analysis and connection to prompt",
            "Physical performance",
            "Vocal performance",
            "Organization and framework",
            "Development and depth of thought",
            "Total effect",
        ],
        "dos": [
            "Consider the difficulty of thinking on one's feet",
            "Note how well they structure their response",
            "Evaluate connection to the prompt",
            "Verbally announce elapsed time at 15 seconds, 30 seconds, 45 seconds, and 1 minute, then switch to time cards for remaining minutes",
        ],
        "donts": [
            "Don't expect the polish of a prepared speech",
            "Don't penalize for brief pauses to collect thoughts",
            "Don't compare to prepared events",
        ],
        "rules": [
            "6 minutes total (preparation + presentation combined)",
            "Timing starts when the topic is received from the judge",
            "Judge provides the topic to the contestant",
            "Judge verbally announces elapsed time at 15s, 30s, 45s, and 1 minute, then uses time cards for remaining minutes",
        ],
    },
    "informative_speaking": {
        "display_name": "Informative Speaking",
        "category": CATEGORY_PUBLIC_ADDRESS,
        "time_min_seconds": 300,
        "time_max_seconds": 480,
        "description": (
            "Original speech to clearly explain, define, or illustrate a subject. "
            "The purpose is to inform, not to persuade. Argumentative, persuasive, "
            "or entertaining material may only be used to illustrate or enliven. "
            "Must have manuscript or outline in possession."
        ),
        "judging_criteria": [
            "Topic analysis and clarity",
            "Physical performance",
            "Vocal performance",
            "Organization and structure",
            "Development and depth of research",
            "Visual aids effectiveness (if used)",
            "Total effect",
        ],
        "dos": [
            "Evaluate how well the audience would learn from this speech",
            "Note organizational clarity",
            "Assess source citation and research credibility",
            "Consider effectiveness of visual aids if used",
        ],
        "donts": [
            "Don't expect persuasion (this is an informative event)",
            "Don't penalize for lack of emotional appeals",
            "Don't let visual aids overshadow the speech content",
        ],
        "rules": [
            "Original work is required",
            "Manuscript or outline must be available for judge review if requested",
            "Must be primarily informative in nature",
            "Visual aids, audiovisual projections, or demonstrations are permitted",
            "Only one easel or electronic display monitor allowed; no other display equipment",
            "Set-up time limited to 2 minutes",
            "No procedures endangering health/safety; no live animals",
            "Plagiarism is grounds for disqualification; all sources must be properly cited",
        ],
    },
    "oratory": {
        "display_name": "Oratory",
        "category": CATEGORY_PUBLIC_ADDRESS,
        "time_min_seconds": 300,
        "time_max_seconds": 480,
        "description": (
            "Original, persuasive speech. May eulogize, alert to danger, strengthen "
            "devotion to a cause, or present solutions. Must have manuscript or "
            "outline in possession."
        ),
        "judging_criteria": [
            "Topic analysis",
            "Physical performance",
            "Vocal performance and passion",
            "Organization and logical argumentation",
            "Development and persuasive effectiveness",
            "Total effect",
        ],
        "dos": [
            "Evaluate persuasive impact",
            "Note passion and conviction",
            "Assess the strength of the argument and evidence",
            "Consider credibility of sources cited",
        ],
        "donts": [
            "Don't let personal agreement or disagreement with the topic affect scoring",
            "Don't let visual aids overshadow the speech content",
        ],
        "rules": [
            "Original work is required",
            "Manuscript or outline must be available for judge review if requested",
            "Must be persuasive in nature",
            "Visual aids, audiovisual projections, or demonstrations are permitted",
            "Only one easel or electronic display monitor allowed; no other display equipment",
            "Set-up time limited to 2 minutes",
            "No procedures endangering health/safety; no live animals",
            "Plagiarism is grounds for disqualification; all sources must be properly cited",
        ],
    },
    "sales_speaking": {
        "display_name": "Sales Speaking",
        "category": CATEGORY_PUBLIC_ADDRESS,
        "time_min_seconds": 300,
        "time_max_seconds": 480,
        "description": (
            "Combines informative and persuasive techniques to encourage the audience "
            "to respond favorably to the appeal. The speaker must carefully analyze "
            "the audience and develop an appropriate persuasive message for an ACTUAL "
            "product or service. The speaker should not invent the product/service "
            "or the intended consumer. Must have manuscript or outline in possession."
        ),
        "judging_criteria": [
            "Topic analysis and audience awareness",
            "Physical performance and professionalism",
            "Vocal performance and enthusiasm",
            "Organization and clarity",
            "Development and persuasive techniques",
            "Visual aids effectiveness (if used)",
            "Total effect",
        ],
        "dos": [
            "Evaluate if you'd actually want the product",
            "Note audience awareness and directness",
            "Assess creativity of the sales approach",
            "Consider effectiveness of visual aids if used",
            "Note source documentation and credibility",
        ],
        "donts": [
            "Don't penalize for choosing unusual products",
            "Don't expect actual product samples",
            "Don't let visual aids overshadow the speech content",
        ],
        "rules": [
            "Original work is required",
            "Must be for an ACTUAL product or service (not invented)",
            "Manuscript or outline must be available for judge review if requested",
            "Visual aids, audiovisual projections, or demonstrations are permitted",
            "Only one easel or electronic display monitor allowed; no other display equipment",
            "Set-up time limited to 2 minutes",
            "No procedures endangering health/safety; no live animals",
            "Caution with distributing consumable products to audience",
            "Plagiarism is grounds for disqualification; all sources must be properly cited",
        ],
    },
    # -----------------------------------------------------------------------
    # ORIGINAL INTERPRETATION EVENTS
    # -----------------------------------------------------------------------
    "oi_poetry": {
        "display_name": "OI Poetry (Original Interpretation)",
        "category": CATEGORY_ORAL_INTERPRETATION,
        "time_min_seconds": 120,
        "time_max_seconds": 240,
        "description": (
            "Original Interpretation of Poetry. Contestant performs their OWN "
            "original poetry composition. This is an interpretation event where "
            "the student is both the author and performer of the piece."
        ),
        "judging_criteria": [
            "Quality of original literature",
            "Vocal performance",
            "Physical performance",
            "Emotional connection and interpretation",
            "Total effect",
        ],
        "dos": [
            "Evaluate both the quality of writing and the performance",
            "Note original voice and creativity",
            "Consider poetic structure and artistry",
        ],
        "donts": [
            "Don't compare to published poets",
            "Don't penalize for unconventional poetic style",
        ],
        "rules": [
            "Must be contestant's own original composition",
            "No hand props, costumes, or staging",
            "Street attire only; stage costumes prohibited",
            "Script must be available for judge review if requested",
        ],
    },
    "oi_prose": {
        "display_name": "OI Prose (Original Interpretation)",
        "category": CATEGORY_ORAL_INTERPRETATION,
        "time_min_seconds": 180,
        "time_max_seconds": 300,
        "description": (
            "Original Interpretation of Prose. Contestant performs their OWN "
            "original prose composition. This is an interpretation event where "
            "the student is both the author and performer of the piece."
        ),
        "judging_criteria": [
            "Quality of original literature",
            "Narrative storytelling",
            "Vocal performance",
            "Physical performance",
            "Total effect",
        ],
        "dos": [
            "Evaluate both the quality of writing and the performance",
            "Note original voice and narrative skill",
            "Consider story structure and creativity",
        ],
        "donts": [
            "Don't compare to published authors",
            "Don't penalize for unconventional narrative style",
        ],
        "rules": [
            "Must be contestant's own original composition",
            "No hand props, costumes, or staging",
            "Street attire only; stage costumes prohibited",
            "Script must be available for judge review if requested",
        ],
    },
}

# ---------------------------------------------------------------------------
# MIFA Rules Summary
# ---------------------------------------------------------------------------
MIFA_RULES_SUMMARY: str = """SCORING RULES:
- Rank top 3 as 1, 2, 3. Everyone else gets rank 4.
- Percentage: 100 for rank 1, 99-75 for others. No duplicates. Whole integers only.
- 75-79 reserved for special circumstances (incomplete performance, inappropriate behavior).
- Recommended scoring convention: 1/100, 2/99, 3/98, 4/97, 4/96, 4/95, etc.

TIMING:
- Time violations may be penalized at judge's discretion (not mandatory).
- Announce actual time to contestant after each performance.
- Use time cards showing minutes remaining (visible to contestant unless they prefer not).
- Timing starts when the first word is spoken or first motion starts.
- Do not cut them off, even if they go over the suggested time.
- For Impromptu: verbally announce 15s, 30s, 45s, 1 minute, then use time cards.

JUDGE PROCEDURES:
- Competitor should ask "judge and timer ready?" before beginning.
- Write/type feedback DURING the performance (you won't have time after).
- Do NOT give oral critiques. If you say "nice job," say it to everyone.
- "REASON FOR RANK/SCORE" section is visible to ALL competitors in the round.
- Fill out ballot in SPEAKER ORDER, not the order you ranked them.
- Return ballots and critique sheets to collection room after each round.

GENERAL RULES:
- 15-minute rule: contestant disqualified if not present within 15 min of scheduled start.
- No audio/video recording allowed.
- Read Code of Conduct at start of each round.
- In interpretation events: no hand props, no costumes, no touching/eye contact in duo/multiple.
- In public address: original work expected, plagiarism = disqualification.
- Prompting from audience = disqualification.
- Consult Tournament Director before any disqualification.
- If judging a student you know personally, report to tournament directors before starting."""

# ---------------------------------------------------------------------------
# Required keys that every event entry must contain
# ---------------------------------------------------------------------------
REQUIRED_EVENT_KEYS: set = {
    "display_name",
    "category",
    "time_min_seconds",
    "time_max_seconds",
    "description",
    "judging_criteria",
    "dos",
    "donts",
    "rules",
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def get_event_by_key(event_key: str) -> Optional[dict]:
    """
    Retrieve a single event's data dictionary by its key.

    Args:
        event_key: The snake_case identifier for the event
                   (e.g. "dramatic_interpretation").

    Returns:
        The event data dictionary if found, or None if the key does not exist.
    """
    return EVENT_DATA.get(event_key)


def get_events_by_category(category: str) -> dict:
    """
    Return a filtered dictionary of events belonging to the given category.

    Args:
        category: Either "oral_interpretation" or "public_address".

    Returns:
        A dictionary of {event_key: event_data} for all matching events.

    Raises:
        ValueError: If the supplied category is not one of the valid values.
    """
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"Invalid category '{category}'. Must be one of {VALID_CATEGORIES}."
        )
    filtered_events = {
        event_key: event_details
        for event_key, event_details in EVENT_DATA.items()
        if event_details["category"] == category
    }
    return filtered_events


def get_all_event_display_names() -> list[str]:
    """
    Return a sorted list of all event display names.

    Returns:
        A list of display name strings, sorted alphabetically.
    """
    all_display_names = [
        event_details["display_name"]
        for event_details in EVENT_DATA.values()
    ]
    return sorted(all_display_names)


def get_event_key_by_display_name(display_name: str) -> Optional[str]:
    """
    Look up an event's dictionary key by its human-readable display name.

    Args:
        display_name: The full display name of the event
                      (e.g. "Dramatic Interpretation").

    Returns:
        The event key string if a matching display name is found, or None.
    """
    for event_key, event_details in EVENT_DATA.items():
        if event_details["display_name"] == display_name:
            return event_key
    return None
