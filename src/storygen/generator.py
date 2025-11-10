"""
A story generator powered by AI models via LiteLLM.

Supports multiple AI providers:
- OpenAI (GPT models)
- Anthropic (Claude models)
- xAI (Grok models)
- Ollama (local models like llama2, qwen3, mistral)
"""

import litellm

from storygen.models import Story


class StoryGenerator:
    """Generate creative short stories using various AI models."""

    OLLAMA_TIMEOUT_SECONDS = 600
    DEFAULT_TIMEOUT_SECONDS = 120

    def __init__(self, provider: str = "gpt-4o-mini", verbose: bool = False):
        """
        Initialize the story generator.

        Args:
            provider: AI model to use (e.g., "gpt-4o-mini", "claude-3-5-sonnet-20241022",
                     "grok-2-1212", "ollama/llama2", "ollama/qwen3:30b")
            verbose: If True, print detailed debug information about prompts and responses

        Note: Reasoning models (like qwen3) need higher max_tokens (2000+) to complete
        their thinking process before outputting the story.
        """
        self.provider = provider
        self.verbose = verbose

    def generate(
        self,
        prompt: str,
        max_tokens: int | None = 1000,
        structured: bool = False,
        pov: str = "third_person_deep",
        structure: str = "three_act",
    ) -> str:
        """
        Generate a short story from a prompt.

        Args:
            prompt: The story prompt or theme
            max_tokens: Maximum length of the generated story (use 2000+ for reasoning models)
            structured: If True, returns JSON with title and scenes
            pov: Point of view/narrative perspective (e.g., "first_person", "third_person_deep")
            structure: Story structure to use (e.g., "three_act", "freytag", "heros_journey", "fichtean", "seven_point", "ai_choice")

        Returns:
            Generated story as a string (plain text or JSON if structured=True)

        Raises:
            ValueError: If the response is empty or invalid
        """
        # Map POV to human-readable description
        pov_descriptions = {
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

        pov_instruction = pov_descriptions.get(pov, pov)

        # Map structure to detailed instructions
        structure_instructions = {
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

        structure_guide = structure_instructions.get(structure, structure_instructions["three_act"])

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

        if self.verbose:
            print("\n" + "=" * 80)
            print("VERBOSE MODE: Showing AI request details")
            print("=" * 80)
            print(f"\nProvider: {self.provider}")
            print(f"Max Tokens: {max_tokens}")
            print(f"POV: {pov}")
            print(f"Structure: {structure}")
            print(f"Structured Output: {structured}")
            print("\n" + "-" * 80)
            print("SYSTEM PROMPT:")
            print("-" * 80)
            print(system_content)
            print("\n" + "-" * 80)
            print("USER PROMPT:")
            print("-" * 80)
            print(prompt)
            print("\n" + "-" * 80)
            print("Sending request to AI...")
            print("-" * 80 + "\n")

        # Add JSON mode hints for structured output
        extra_args: dict = {}
        if structured:
            # For OpenAI-style / compatible providers (but NOT Ollama)
            # Ollama's format="json" seems to break streaming and reasoning models
            if not self.provider.startswith("ollama/"):
                extra_args["response_format"] = {"type": "json_object"}

        # Generous timeout for heavy local models
        # Ollama models (especially 30B+) can be slow, so give them plenty of time
        timeout_seconds = (
            self.OLLAMA_TIMEOUT_SECONDS
            if self.provider.startswith("ollama/")
            else self.DEFAULT_TIMEOUT_SECONDS
        )

        try:
            # Use streaming for verbose mode to show real-time output
            if self.verbose:
                response = litellm.completion(
                    model=self.provider,
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=max_tokens,
                    timeout=timeout_seconds,
                    stream=True,
                    **extra_args,
                )
            else:
                response = litellm.completion(
                    model=self.provider,
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=max_tokens,
                    timeout=timeout_seconds,
                    **extra_args,
                )
        except Exception as e:
            # Handle timeout and API errors gracefully
            error_name = type(e).__name__
            if "timeout" in error_name.lower() or "timeout" in str(e).lower():
                raise ValueError(
                    f"Model request timed out after {timeout_seconds}s. "
                    f"Try a smaller local model or lower max_tokens. "
                    f"(Provider: {self.provider})"
                ) from e
            elif "api" in error_name.lower() or "connection" in str(e).lower():
                raise ValueError(
                    f"Upstream model/transport error from provider '{self.provider}': {e}"
                ) from e
            else:
                # Re-raise unexpected errors
                raise

        # Handle streaming vs non-streaming responses
        # Check if we requested streaming (verbose mode) - response will be a generator
        if self.verbose:
            # Streaming response - collect chunks and display in real-time
            print("\n" + "=" * 80)
            print("STREAMING RESPONSE (real-time output)")
            print("=" * 80)
            print()

            collected_content = []
            chunk_count = 0
            for chunk in response:
                chunk_count += 1
                if chunk_count == 1:
                    print("[First chunk received]", flush=True)
                if hasattr(chunk, "choices") and chunk.choices:  # type: ignore
                    delta = chunk.choices[0].delta  # type: ignore
                    if hasattr(delta, "content") and delta.content:
                        content_piece = delta.content
                        print(content_piece, end="", flush=True)
                        collected_content.append(content_piece)

            print(f"\n\n[Received {chunk_count} chunks total]")
            print("=" * 80)
            content = "".join(collected_content)
            print(f"\nTotal content length: {len(content)} characters")
            print("=" * 80 + "\n")
        else:
            # Non-streaming response
            if self.verbose:
                print("\n" + "=" * 80)
                print("RESPONSE RECEIVED")
                print("=" * 80)
                if hasattr(response, "usage"):
                    usage = response.usage  # type: ignore
                    print("Token Usage:")
                    if hasattr(usage, "prompt_tokens"):
                        print(f"   - Prompt tokens: {usage.prompt_tokens}")
                    if hasattr(usage, "completion_tokens"):
                        print(f"   - Completion tokens: {usage.completion_tokens}")
                    if hasattr(usage, "total_tokens"):
                        print(f"   - Total tokens: {usage.total_tokens}")
                print("\n" + "-" * 80)
                print("RAW AI RESPONSE:")
                print("-" * 80)

            # Type-safe access to response content
            # Note: LiteLLM returns dynamic types, suppress type checker warnings
            if not response or not hasattr(response, "choices") or not response.choices:  # type: ignore
                raise ValueError("Invalid response from AI provider")

            content = response.choices[0].message.content  # type: ignore
            if content is None:
                raise ValueError("AI provider returned empty content")

            if self.verbose:
                # Show response with proper representation of whitespace/empty content
                content_str = str(content)
                print(f"Content length: {len(content_str)} characters")
                print(f"Content repr: {repr(content_str[:200])}")  # Show escaped version
                print()
                if len(content_str) > 2000:
                    print(content_str[:1000])
                    print(f"\n... ({len(content_str) - 2000} more characters) ...\n")
                    print(content_str[-1000:])
                else:
                    print(content_str)
                print("\n" + "=" * 80 + "\n")

        return str(content)

    def generate_structured(
        self,
        prompt: str,
        max_tokens: int | None = 50000,
        min_words: int | None = None,
        pov: str = "third_person_deep",
        structure: str = "three_act",
    ) -> Story:
        """
        Generate a structured story with title, scenes, and metadata.

        Args:
            prompt: The story prompt or theme
            max_tokens: Maximum length (default 4000 tokens - suitable for short stories)
            min_words: Minimum word count to request (e.g., 1000, 2000, 5000)
            pov: Point of view/narrative perspective (e.g., "first_person", "third_person_deep")
            structure: Story structure to use (e.g., "three_act", "freytag", "heros_journey", "fichtean", "seven_point", "ai_choice")

        Returns:
            Story object with structured data

        Raises:
            ValueError: If the response is empty, invalid, or not valid JSON
        """
        # Enhance prompt with word count requirement if specified
        enhanced_prompt = prompt
        if min_words:
            enhanced_prompt = f"{prompt}\n\nIMPORTANT: Generate at least {min_words} words of narrative content across all scenes."
            # Scale max_tokens based on requested word count
            # Rule of thumb: ~1.3 tokens per word + overhead for JSON structure
            # Add 1000 tokens for metadata (title, summary, etc.)
            estimated_tokens = int(min_words * 1.5) + 1000
            max_tokens = max(max_tokens or 0, estimated_tokens)

        content = self.generate(
            enhanced_prompt, max_tokens=max_tokens, structured=True, pov=pov, structure=structure
        )

        # Use robust JSON parser to handle LLM quirks
        from storygen.parsing import parse_story_json

        try:
            data = parse_story_json(content)
            return Story.from_dict(data)
        except (ValueError, KeyError) as e:
            raise ValueError(
                f"Failed to parse structured story: {e}\n\nRaw content preview: {content[:500]}..."
            )
