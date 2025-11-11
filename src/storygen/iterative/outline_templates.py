"""
Predefined story structure templates.

Each template defines a hierarchical act structure with generic descriptions
that can be applied to any story. The AI fills in story_application for each act.
"""

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
# Template Registry
# =============================================================================

STRUCTURE_TEMPLATES = {
    "three-act": THREE_ACT_TEMPLATE,
    "hero-journey": HEROS_JOURNEY_TEMPLATE,
    "fichtean": FICHTEAN_CURVE_TEMPLATE,
}


def get_template(structure_type: str) -> list[Act]:
    """
    Get a copy of the outline template for the specified structure type.

    Args:
        structure_type: One of "three-act", "hero-journey", "fichtean"

    Returns:
        List of top-level Act objects (deep copy so modifications don't affect template)

    Raises:
        ValueError: If structure_type is not recognized
    """
    import copy

    if structure_type not in STRUCTURE_TEMPLATES:
        valid = ", ".join(STRUCTURE_TEMPLATES.keys())
        raise ValueError(f"Unknown structure type '{structure_type}'. Valid options: {valid}")

    # Deep copy so modifications don't affect the template
    return copy.deepcopy(STRUCTURE_TEMPLATES[structure_type])


def list_available_structures() -> list[str]:
    """Get list of available structure templates."""
    return list(STRUCTURE_TEMPLATES.keys())
