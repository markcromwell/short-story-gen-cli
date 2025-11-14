"""
Predefined story structure templates.

Each template defines a hierarchical act structure with generic descriptions
that can be applied to any story. The AI fills in story_application for each act.
"""

from storygen.iterative.exceptions import ConfigError
from storygen.iterative.models import Act

# =============================================================================
# THREE-ACT STRUCTURE (Classic Hollywood)
# =============================================================================

THREE_ACT_TEMPLATE = [
    Act(
        title="Act 1: Setup",
        description="Introduce the protagonist in their ordinary world. Establish the status quo, their wants/needs, relationships, and the story world. Show what's at stake.",
        story_application="",  # AI fills this
        percentage=0.25,
        order=0,
        sub_acts=[
            Act(
                title="Opening Image",
                description="The protagonist's life before the adventure begins. Shows who they are and what's missing.",
                story_application="",
                percentage=0.05,
                order=0,
            ),
            Act(
                title="Setup & Theme Stated",
                description="Establish the world, supporting characters, and hint at the story's theme or moral question.",
                story_application="",
                percentage=0.10,
                order=1,
            ),
            Act(
                title="Inciting Incident",
                description="The event that disrupts the status quo and sets the story in motion. The protagonist can't ignore this.",
                story_application="",
                percentage=0.10,
                order=2,
            ),
        ],
    ),
    Act(
        title="Act 2: Confrontation",
        description="The protagonist pursues their goal but faces escalating obstacles. Complications arise and stakes increase. Tests and trials reveal character.",
        story_application="",
        percentage=0.50,
        order=1,
        sub_acts=[
            Act(
                title="Rising Action",
                description="The protagonist commits to their goal and enters a new world/situation. Faces initial obstacles and learns new skills.",
                story_application="",
                percentage=0.20,
                order=0,
            ),
            Act(
                title="Midpoint",
                description="A major revelation, victory, or defeat that changes what the protagonist believes or wants. Raises the stakes significantly.",
                story_application="",
                percentage=0.10,
                order=1,
            ),
            Act(
                title="Downward Spiral",
                description="Consequences of the midpoint compound. Enemies close in, allies are tested, and the protagonist's flaws cause problems.",
                story_application="",
                percentage=0.15,
                order=2,
            ),
            Act(
                title="Crisis",
                description="All seems lost—the darkest moment. The protagonist faces their greatest challenge or failure. Forces a crucial decision.",
                story_application="",
                percentage=0.05,
                order=3,
            ),
        ],
    ),
    Act(
        title="Act 3: Resolution",
        description="The final confrontation and its aftermath. The protagonist applies what they've learned. Resolve the main conflict and show the new status quo.",
        story_application="",
        percentage=0.25,
        order=2,
        sub_acts=[
            Act(
                title="Climax",
                description="The final confrontation with the antagonist or challenge. High tension, decisive action, all skills and lessons applied.",
                story_application="",
                percentage=0.15,
                order=0,
            ),
            Act(
                title="Resolution & New World",
                description="The aftermath. Show how the protagonist and world have changed. Tie up loose ends and hint at the future.",
                story_application="",
                percentage=0.10,
                order=1,
            ),
        ],
    ),
]


# =============================================================================
# HERO'S JOURNEY (Joseph Campbell / Christopher Vogler)
# =============================================================================

HEROS_JOURNEY_TEMPLATE = [
    Act(
        title="Act 1: Departure",
        description="The hero is called from their ordinary world into adventure, initially refuses, but is encouraged by a mentor to cross the threshold.",
        story_application="",
        percentage=0.25,
        order=0,
        sub_acts=[
            Act(
                title="Ordinary World",
                description="Show the hero in their normal life before the adventure. Establish what they'll leave behind.",
                story_application="",
                percentage=0.08,
                order=0,
            ),
            Act(
                title="Call to Adventure",
                description="The hero learns of a challenge, problem, or adventure they must undertake.",
                story_application="",
                percentage=0.05,
                order=1,
            ),
            Act(
                title="Refusal of the Call",
                description="The hero hesitates or refuses due to fear, duty, or obligation. Shows what's at stake.",
                story_application="",
                percentage=0.04,
                order=2,
            ),
            Act(
                title="Meeting the Mentor",
                description="An experienced helper provides training, equipment, advice, or confidence to begin the journey.",
                story_application="",
                percentage=0.04,
                order=3,
            ),
            Act(
                title="Crossing the Threshold",
                description="The hero commits to the adventure and enters the special world. There's no turning back.",
                story_application="",
                percentage=0.04,
                order=4,
            ),
        ],
    ),
    Act(
        title="Act 2: Initiation",
        description="The hero faces tests, gains allies and enemies, approaches a dangerous place, and endures a major ordeal that leads to transformation.",
        story_application="",
        percentage=0.50,
        order=1,
        sub_acts=[
            Act(
                title="Tests, Allies, and Enemies",
                description="The hero learns the rules of the special world, makes friends and enemies, and is tested.",
                story_application="",
                percentage=0.15,
                order=0,
            ),
            Act(
                title="Approach to the Inmost Cave",
                description="The hero approaches the place of greatest danger. Preparations are made for the major challenge.",
                story_application="",
                percentage=0.10,
                order=1,
            ),
            Act(
                title="The Ordeal",
                description="The hero faces their greatest fear or most difficult challenge. Often appears to fail or die.",
                story_application="",
                percentage=0.10,
                order=2,
            ),
            Act(
                title="Reward (Seizing the Sword)",
                description="After surviving the ordeal, the hero gains a reward: knowledge, treasure, reconciliation, or power.",
                story_application="",
                percentage=0.10,
                order=3,
            ),
            Act(
                title="The Road Back",
                description="The hero must return to the ordinary world. Often pursued by consequences of the ordeal.",
                story_application="",
                percentage=0.05,
                order=4,
            ),
        ],
    ),
    Act(
        title="Act 3: Return",
        description="The hero returns transformed, faces a final test, and brings the benefit of their journey back to the ordinary world.",
        story_application="",
        percentage=0.25,
        order=2,
        sub_acts=[
            Act(
                title="Resurrection",
                description="A final test where the hero must use everything they've learned. A final moment of death and rebirth.",
                story_application="",
                percentage=0.15,
                order=0,
            ),
            Act(
                title="Return with the Elixir",
                description="The hero returns home transformed, bringing something that will help the ordinary world.",
                story_application="",
                percentage=0.10,
                order=1,
            ),
        ],
    ),
]


# =============================================================================
# FICHTEAN CURVE (Crisis-Driven)
# =============================================================================

FICHTEAN_CURVE_TEMPLATE = [
    Act(
        title="Rising Action: Crisis 1",
        description="The story opens with an immediate crisis. No extended setup—throw the protagonist into action and reveal character through conflict.",
        story_application="",
        percentage=0.15,
        order=0,
    ),
    Act(
        title="Rising Action: Crisis 2",
        description="A second crisis escalates the stakes. The protagonist's situation worsens. Reveal more about relationships and backstory through the conflict.",
        story_application="",
        percentage=0.15,
        order=1,
    ),
    Act(
        title="Rising Action: Crisis 3",
        description="A third crisis further complicates matters. The protagonist's flaws contribute to the problem. Allies may be lost or betrayed.",
        story_application="",
        percentage=0.15,
        order=2,
    ),
    Act(
        title="Climax",
        description="All crises converge into one major confrontation. The protagonist must face their fears and flaws directly. Maximum tension and uncertainty.",
        story_application="",
        percentage=0.30,
        order=3,
    ),
    Act(
        title="Falling Action",
        description="The aftermath of the climax. Deal with consequences, reveal final surprises, and show how the protagonist has changed.",
        story_application="",
        percentage=0.15,
        order=4,
    ),
    Act(
        title="Resolution",
        description="Brief denouement showing the new normal. Tie up remaining threads and provide closure.",
        story_application="",
        percentage=0.10,
        order=5,
    ),
]


# =============================================================================
# SAVE THE CAT BEAT SHEET (Blake Snyder)
# =============================================================================

SAVE_THE_CAT_TEMPLATE = [
    Act(
        title="Opening Image",
        description="Show the protagonist's life before the story begins. Establish their 'before' state and hint at what they want.",
        story_application="",
        percentage=0.01,
        order=0,
    ),
    Act(
        title="Theme Stated",
        description="Introduce the story's theme or moral through dialogue or action. Often 'stated' by a secondary character.",
        story_application="",
        percentage=0.05,
        order=1,
    ),
    Act(
        title="Setup",
        description="Introduce the protagonist, their world, and their wants. Show what they need to change.",
        story_application="",
        percentage=0.10,
        order=2,
    ),
    Act(
        title="Catalyst",
        description="The inciting incident that forces the protagonist out of their comfort zone. Life will never be the same.",
        story_application="",
        percentage=0.10,
        order=3,
    ),
    Act(
        title="Debate",
        description="The protagonist resists the call to adventure. Shows their reluctance and the stakes of staying the same.",
        story_application="",
        percentage=0.10,
        order=4,
    ),
    Act(
        title="Break into Two",
        description="The protagonist commits to the adventure and enters Act 2. Crosses the threshold into the new world.",
        story_application="",
        percentage=0.05,
        order=5,
    ),
    Act(
        title="B Story",
        description="Introduce the love story, friendship, or thematic mirror that will help the protagonist grow.",
        story_application="",
        percentage=0.05,
        order=6,
    ),
    Act(
        title="Fun and Games",
        description="The promise of the premise. Show what the audience came for - the adventure, romance, or spectacle.",
        story_application="",
        percentage=0.10,
        order=7,
    ),
    Act(
        title="Midpoint",
        description="A major shift. The protagonist gets what they wanted... but not what they needed. Stakes rise dramatically.",
        story_application="",
        percentage=0.05,
        order=8,
    ),
    Act(
        title="Bad Guys Close In",
        description="Everything unravels. The antagonist's plan advances. Allies are lost. The protagonist's flaws cause problems.",
        story_application="",
        percentage=0.10,
        order=9,
    ),
    Act(
        title="All Is Lost",
        description="The lowest point. The protagonist fails. Everything they believed is wrong. They must change or die.",
        story_application="",
        percentage=0.05,
        order=10,
    ),
    Act(
        title="Dark Night of the Soul",
        description="The protagonist reflects on their failure. Considers giving up. Finds inner strength or receives help.",
        story_application="",
        percentage=0.05,
        order=11,
    ),
    Act(
        title="Break into Three",
        description="The protagonist finds new resolve. Has a new plan based on what they've learned. Stakes are now personal.",
        story_application="",
        percentage=0.05,
        order=12,
    ),
    Act(
        title="Finale",
        description="The final confrontation. Gather allies, face the antagonist, use everything learned to win.",
        story_application="",
        percentage=0.10,
        order=13,
    ),
    Act(
        title="Final Image",
        description="Show how the protagonist has changed. Mirror the opening image but show the 'after' state.",
        story_application="",
        percentage=0.04,
        order=14,
    ),
]


# =============================================================================
# SEVEN-POINT STRUCTURE (Dan Wells)
# =============================================================================

SEVEN_POINT_TEMPLATE = [
    Act(
        title="Hook",
        description="Grab the reader's attention immediately. Introduce the protagonist and their immediate problem or situation.",
        story_application="",
        percentage=0.10,
        order=0,
    ),
    Act(
        title="Plot Turn 1",
        description="The inciting incident that changes everything. The protagonist is forced into the main conflict.",
        story_application="",
        percentage=0.15,
        order=1,
    ),
    Act(
        title="Pinch 1",
        description="Show the antagonist's power. The protagonist faces a major obstacle that reveals the true stakes.",
        story_application="",
        percentage=0.15,
        order=2,
    ),
    Act(
        title="Midpoint",
        description="A major turning point. The protagonist gains new information or ability that changes their approach.",
        story_application="",
        percentage=0.15,
        order=3,
    ),
    Act(
        title="Pinch 2",
        description="The antagonist strikes back harder. The protagonist faces their greatest challenge yet.",
        story_application="",
        percentage=0.15,
        order=4,
    ),
    Act(
        title="Plot Turn 2",
        description="The protagonist makes a crucial decision that leads to the final confrontation. No turning back.",
        story_application="",
        percentage=0.15,
        order=5,
    ),
    Act(
        title="Resolution",
        description="The final confrontation and aftermath. Resolve the conflict and show the new status quo.",
        story_application="",
        percentage=0.15,
        order=6,
    ),
]


# =============================================================================
# SHORT STORY ARC (Simplified for Short Fiction)
# =============================================================================

SHORT_STORY_TEMPLATE = [
    Act(
        title="Setup",
        description="Introduce the protagonist, their world, and the initial situation. Establish what's normal and hint at conflict.",
        story_application="",
        percentage=0.20,
        order=0,
    ),
    Act(
        title="Inciting Incident",
        description="The event that disrupts the status quo and sets the story in motion. The protagonist must respond.",
        story_application="",
        percentage=0.20,
        order=1,
    ),
    Act(
        title="Rising Action",
        description="Build tension through complications and obstacles. The protagonist faces challenges and learns about themselves.",
        story_application="",
        percentage=0.30,
        order=2,
    ),
    Act(
        title="Climax",
        description="The moment of highest tension. The protagonist confronts the main conflict or makes a crucial decision.",
        story_application="",
        percentage=0.20,
        order=3,
    ),
    Act(
        title="Resolution",
        description="Resolve the conflict and show the aftermath. The protagonist's life is changed in some meaningful way.",
        story_application="",
        percentage=0.10,
        order=4,
    ),
]


# =============================================================================
# FREYTAG'S PYRAMID (Gustav Freytag)
# =============================================================================

FREYTAG_PYRAMID_TEMPLATE = [
    Act(
        title="Exposition",
        description="Introduce characters, setting, and initial situation. Establish the status quo and hint at potential conflict.",
        story_application="",
        percentage=0.15,
        order=0,
    ),
    Act(
        title="Rising Action",
        description="Build tension through complications and increasing stakes. Introduce conflicts and obstacles.",
        story_application="",
        percentage=0.25,
        order=1,
    ),
    Act(
        title="Climax",
        description="The turning point of highest tension. The protagonist faces their greatest challenge or makes a decisive choice.",
        story_application="",
        percentage=0.25,
        order=2,
    ),
    Act(
        title="Falling Action",
        description="Consequences of the climax unfold. Loose ends are tied up and the situation begins to resolve.",
        story_application="",
        percentage=0.20,
        order=3,
    ),
    Act(
        title="Denouement",
        description="Final resolution and reflection. Show the new normal and how characters have changed.",
        story_application="",
        percentage=0.15,
        order=4,
    ),
]


# =============================================================================
# FIVE-POINT PLOT STRUCTURE
# =============================================================================

FIVE_POINT_TEMPLATE = [
    Act(
        title="Exposition",
        description="Introduce the protagonist, setting, and initial conflict. Establish the story world and what's at stake.",
        story_application="",
        percentage=0.15,
        order=0,
    ),
    Act(
        title="Rising Action",
        description="Build tension through complications and obstacles. The protagonist faces challenges and grows.",
        story_application="",
        percentage=0.25,
        order=1,
    ),
    Act(
        title="Climax",
        description="The moment of highest tension and decisive action. The protagonist confronts the main conflict.",
        story_application="",
        percentage=0.25,
        order=2,
    ),
    Act(
        title="Falling Action",
        description="Deal with the aftermath of the climax. Begin resolving subplots and showing consequences.",
        story_application="",
        percentage=0.20,
        order=3,
    ),
    Act(
        title="Resolution",
        description="Final outcome and closure. Show how the protagonist and world have changed.",
        story_application="",
        percentage=0.15,
        order=4,
    ),
]


# =============================================================================
# EPIPHANY STRUCTURE (For Character-Driven Stories)
# =============================================================================

EPIPHANY_TEMPLATE = [
    Act(
        title="Setup",
        description="Introduce the protagonist in their current life. Show their habits, relationships, and the situation that feels 'stuck'.",
        story_application="",
        percentage=0.25,
        order=0,
    ),
    Act(
        title="Inciting Incident",
        description="An event or encounter that disrupts the protagonist's routine and forces them to question their life.",
        story_application="",
        percentage=0.20,
        order=1,
    ),
    Act(
        title="Rising Action",
        description="The protagonist explores new possibilities, faces challenges, and begins to change. Build toward the moment of insight.",
        story_application="",
        percentage=0.30,
        order=2,
    ),
    Act(
        title="Epiphany",
        description="The moment of realization or insight that changes everything. The protagonist sees themselves or their situation clearly.",
        story_application="",
        percentage=0.15,
        order=3,
    ),
    Act(
        title="Resolution",
        description="Show the consequences of the epiphany. The protagonist acts on their insight and finds new direction.",
        story_application="",
        percentage=0.10,
        order=4,
    ),
]


# =============================================================================
# SNOWFLAKE METHOD (Randy Ingermanson)
# =============================================================================

SNOWFLAKE_TEMPLATE = [
    Act(
        title="Act 1: Setup",
        description="Introduce the protagonist, their goal, and the initial conflict. Establish the story world and stakes.",
        story_application="",
        percentage=0.25,
        order=0,
        sub_acts=[
            Act(
                title="Introduction",
                description="Present the protagonist in their ordinary world and introduce the initial problem.",
                story_application="",
                percentage=0.10,
                order=0,
            ),
            Act(
                title="Development",
                description="Build the protagonist's motivation and show why they must act.",
                story_application="",
                percentage=0.15,
                order=1,
            ),
        ],
    ),
    Act(
        title="Act 2: Confrontation",
        description="The protagonist faces escalating challenges and learns important lessons. External and internal conflicts build.",
        story_application="",
        percentage=0.50,
        order=1,
        sub_acts=[
            Act(
                title="Rising Action",
                description="The protagonist enters the adventure and faces initial obstacles.",
                story_application="",
                percentage=0.20,
                order=0,
            ),
            Act(
                title="Crisis",
                description="Major complications arise. The protagonist faces their greatest fears and doubts.",
                story_application="",
                percentage=0.15,
                order=1,
            ),
            Act(
                title="Climax Build",
                description="All conflicts converge toward the final confrontation.",
                story_application="",
                percentage=0.15,
                order=2,
            ),
        ],
    ),
    Act(
        title="Act 3: Resolution",
        description="The final confrontation and aftermath. The protagonist applies what they've learned and achieves transformation.",
        story_application="",
        percentage=0.25,
        order=2,
        sub_acts=[
            Act(
                title="Climax",
                description="The decisive confrontation where the protagonist uses everything they've learned.",
                story_application="",
                percentage=0.15,
                order=0,
            ),
            Act(
                title="Resolution",
                description="Show the new status quo and how the protagonist has changed.",
                story_application="",
                percentage=0.10,
                order=1,
            ),
        ],
    ),
]

STRUCTURE_TEMPLATES = {
    "three-act": THREE_ACT_TEMPLATE,
    "hero-journey": HEROS_JOURNEY_TEMPLATE,
    "fichtean": FICHTEAN_CURVE_TEMPLATE,
    "save-the-cat": SAVE_THE_CAT_TEMPLATE,
    "seven-point": SEVEN_POINT_TEMPLATE,
    "short-story": SHORT_STORY_TEMPLATE,
    "freytag": FREYTAG_PYRAMID_TEMPLATE,
    "five-point": FIVE_POINT_TEMPLATE,
    "epiphany": EPIPHANY_TEMPLATE,
    "snowflake": SNOWFLAKE_TEMPLATE,
}


def get_template(structure_type: str) -> list[Act]:
    """
    Get a copy of the outline template for the specified structure type.

    Args:
        structure_type: One of "three-act", "hero-journey", "fichtean", "save-the-cat",
            "seven-point", "short-story", "freytag", "five-point", "epiphany", "snowflake"

    Returns:
        List of top-level Act objects (deep copy so modifications don't affect template)

    Raises:
        ValueError: If structure_type is not recognized
    """
    import copy

    if structure_type not in STRUCTURE_TEMPLATES:
        valid = ", ".join(STRUCTURE_TEMPLATES.keys())
        raise ConfigError(f"Unknown structure type '{structure_type}'. Valid options: {valid}")

    # Deep copy so modifications don't affect the template
    return copy.deepcopy(STRUCTURE_TEMPLATES[structure_type])


def list_available_structures() -> list[str]:
    """Get list of available structure templates."""
    return list(STRUCTURE_TEMPLATES.keys())
