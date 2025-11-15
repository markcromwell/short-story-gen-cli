"""Prompt building utilities for story generation."""


class PromptBuilder:
    """Builds system and user prompts for story generation."""

    POV_DESCRIPTIONS = {
        "first_person": "first person (I/we)",
        "first_person_plural": "first person plural (we)",
        "second_person": "second person (you)",
        "third_person_limited": "third person limited (he/she/they, single character's perspective)",
        "third_person_deep": "third person deep POV (he/she/they, intimate access to character's thoughts)",
        "third_person_omniscient": "third person omniscient (he/she/they, all-knowing narrator)",
        "third_person_objective": "third person objective (he/she/they, external observations only)",
        "multiple_pov": "multiple POV (switching between different characters' perspectives)",
        "epistolary": "epistolary (letters, diary entries, documents)",
        "free_indirect": "free indirect discourse (blending narrator and character voice)",
        "stream_of_consciousness": "stream of consciousness (unfiltered character thoughts)",
    }

    STRUCTURE_INSTRUCTIONS = {
        "three_act": """
STRUCTURE: Three-Act Structure
- Act 1 (Setup, 10-20%): Introduce characters, world, and inciting incident
- Act 2 (Confrontation, 60-70%): Build conflict with rising action and turning points
- Act 3 (Resolution, 20%): Climax and fallout""",
        "freytag": """
STRUCTURE: Freytag's Pyramid
- Exposition: Establish normalcy and stakes
- Rising Action: Inciting incident leads to complications
- Climax: Peak conflict at the pyramid's apex
- Falling Action: Consequences unfold
- Denouement: Quick resolution or twist""",
        "heros_journey": """
STRUCTURE: Hero's Journey (Simplified)
- Ordinary World: Protagonist's status quo
- Call to Adventure & Trials: Disruption and challenges
- Climax & Return: Ordeal and transformation with a lesson or boon""",
        "fichtean": """
STRUCTURE: Fichtean Curve
- Immediate Crisis: Jump into conflict, skip heavy exposition
- Rising Crises: 3-5 escalating obstacles building tension
- Climax: Final showdown
- Falling Action: Brief wrap-up with reflection""",
        "seven_point": """
STRUCTURE: Seven-Point Story Structure
- Hook: Grab attention with a compelling question
- Plot Turn 1: Shift from status quo to conflict
- Pinch 1: Raise stakes, show antagonistic force
- Midpoint: Major revelation that changes everything
- Pinch 2: Darkest moment, all seems lost
- Plot Turn 2: Discovery of path to victory
- Resolution: Satisfying close that answers the hook""",
        "ai_choice": """
STRUCTURE: AI's Choice
Choose the most appropriate story structure (Three-Act, Freytag's Pyramid, Hero's Journey,
Fichtean Curve, or Seven-Point) based on the prompt's genre, tone, and content. Apply it
naturally without announcing your choice.""",
    }

    @classmethod
    def build_system_prompt(cls, pov: str, structure: str, structured: bool = False) -> str:
        """Build the system prompt for story generation."""
        pov_instruction = cls.POV_DESCRIPTIONS.get(pov, pov)
        structure_guide = cls.STRUCTURE_INSTRUCTIONS.get(
            structure, cls.STRUCTURE_INSTRUCTIONS["three_act"]
        )

        system_content = (
            f"You are a creative writer. Write engaging short stories based on the user's prompt. "
            f"Use {pov_instruction} narrative perspective throughout the story.\n\n"
            f"{structure_guide}"
        )

        if structured:
            system_content += r"""

IMPORTANT: You MUST return ONLY valid JSON. Do not include any text before or after the JSON. Do not write narrative descriptions.

CRITICAL JSON RULES:
- Use standard double quotes ("...") for ALL strings
- Use \n for line breaks within strings (NOT triple quotes)
- Do NOT use Python triple-quotes, Markdown code fences, or any non-JSON syntax
- Each string must be a single double-quoted value

Return the story as JSON in this EXACT format:
{
    "title": "Story Title",
    "genre": "Genre (e.g., Sci-Fi, Fantasy, Mystery)",
    "summary": "Brief teaser-style summary that sets up the premise WITHOUT spoiling the ending or major twists",
    "characters": ["Full Name1", "Full Name2", "Full Name3"],
    "scenes": [
        {
            "number": 1,
            "title": "Internal scene title (for reference only, not displayed)",
            "pov_character": "Character Name (whose perspective/POV this scene is from)",
            "location": "Where this scene takes place",
            "time_hours": 0.0,
            "content": "The actual scene content/narrative. You may use markdown: *text* for italics, **text** for bold, ***text*** for bold+italic."
        },
        {
            "number": 2,
            "title": "Next scene title",
            "pov_character": "Character Name",
            "location": "Location name",
            "time_hours": 2.5,
            "content": "Scene content..."
        }
    ]
}

STORY QUALITY REQUIREMENTS:

Follow the structure specified above naturally and effectively. Your story should be:

- COMPLETE: Have a clear beginning (establish characters/situation), middle (develop conflict), and end (resolve conflict)
- VIVID: Use specific details and sensory descriptions, not vague summaries
- CHARACTER-DRIVEN: Show emotions and motivations through actions and dialogue
- ENGAGING: Create scenes with concrete actions, not just exposition
- DISTINCTIVE: Give each character a unique voice and clear purpose
- PURPOSEFUL: Make every scene advance either plot or character development
- TENSE: Use conflict and challenges to drive the narrative forward

Apply the structure's specific guidelines (immediate crisis for Fichtean, ordinary world for Hero's Journey, etc.)
while maintaining these quality standards throughout."""

        return system_content

    @classmethod
    def enhance_user_prompt(cls, prompt: str, min_words: int | None = None) -> str:
        """Enhance the user prompt with additional requirements."""
        if min_words:
            return f"{prompt}\n\nIMPORTANT: Generate at least {min_words} words of narrative content across all scenes."
        return prompt
