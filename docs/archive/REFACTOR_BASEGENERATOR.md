# BaseGenerator Refactoring Example

## Current State (Duplicated Code)

### IdeaGenerator.generate() - 107 lines
```python
def generate(self, user_prompt: str, story_type: str = "short-story") -> StoryIdea:
    """Generate a story idea with retry logic."""
    last_error = None

    for attempt in range(self.max_retries):
        try:
            if self.verbose:
                print(f"\n🔄 Attempt {attempt + 1}/{self.max_retries}")

            system_prompt = self._build_prompt(user_prompt, story_type)

            if self.verbose:
                print("\n" + "=" * 80)
                print("SYSTEM PROMPT:")
                print("=" * 80)
                print(system_prompt)
                print("=" * 80)

            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                timeout=self.timeout,
            )

            response_text = response.choices[0].message.content

            if self.verbose:
                print("\n" + "=" * 80)
                print("AI RESPONSE:")
                print("=" * 80)
                print(response_text[:500] if len(response_text) > 500 else response_text)
                print("=" * 80)

            data = self._parse_response(response_text)

            # Construct StoryIdea
            idea = StoryIdea(
                raw_idea=data["raw_idea"],
                one_sentence=data["one_sentence"],
                expanded=data["expanded"],
                genres=data["genres"],
                tone=data["tone"],
                themes=data["themes"],
                setting=data["setting"],
            )

            return idea

        except Exception as e:
            last_error = e
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                print(f"⚠️  Error: {str(e)}")
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                break

    raise IdeaGenerationError(f"Failed after {self.max_retries} attempts: {last_error}")
```

### CharacterGenerator.generate() - 107 lines (IDENTICAL PATTERN!)
```python
def generate(self, story_idea: StoryIdea, story_type: str = "short-story") -> list[Character]:
    """Generate characters with retry logic."""
    last_error = None

    for attempt in range(self.max_retries):
        try:
            if self.verbose:
                print(f"\n🔄 Attempt {attempt + 1}/{self.max_retries}")

            system_prompt, user_prompt = self._build_prompt(story_idea, story_type)

            if self.verbose:
                print("\n" + "=" * 80)
                print("SYSTEM PROMPT:")
                print("=" * 80)
                print(system_prompt)
                print("=" * 80)

            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                timeout=self.timeout,
            )

            response_text = response.choices[0].message.content

            # ... EXACT SAME PATTERN repeats ...
```

**Result**: 7 generators × ~100 lines each = **700 lines of duplicated code**

---

## After Refactor (Clean, DRY)

### base.py - BaseGenerator (150 lines, shared by all)
```python
"""Base class for all AI generators with common retry/error/logging logic."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic
import litellm
import time

T = TypeVar('T')  # Return type varies per generator

class BaseGenerator(ABC, Generic[T]):
    """Abstract base for all AI generators."""

    def __init__(self, model: str = "gpt-4", max_retries: int = 3,
                 timeout: int = 600, verbose: bool = False):
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.verbose = verbose

    @abstractmethod
    def _build_prompt(self, *args, **kwargs) -> str | tuple[str, str]:
        """Build AI prompt. Return system_prompt or (system, user)."""
        pass

    @abstractmethod
    def _parse_response(self, response_text: str) -> Any:
        """Parse and validate AI response."""
        pass

    @abstractmethod
    def _construct_result(self, parsed_data: Any) -> T:
        """Construct final typed result from parsed data."""
        pass

    def _log_verbose(self, stage: str, content: str, max_chars: int = 500):
        """Consistent verbose logging."""
        if not self.verbose:
            return

        print(f"\n{'='*80}")
        print(f"{stage.upper()}")
        print(f"{'='*80}")

        if len(content) > max_chars:
            print(f"{content[:max_chars]}...")
            print(f"\n[... {len(content) - max_chars} more characters ...]")
        else:
            print(content)

        print(f"{'='*80}\n")

    def _call_ai(self, system_prompt: str, user_prompt: str) -> str:
        """Call AI with retry logic and error handling."""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                if self.verbose:
                    print(f"\n🔄 Attempt {attempt + 1}/{self.max_retries}")

                self._log_verbose("System Prompt", system_prompt)
                self._log_verbose("User Prompt", user_prompt)

                response = litellm.completion(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    timeout=self.timeout,
                )

                if not hasattr(response, "choices") or not response.choices:
                    raise ValueError("Invalid response format from AI model")

                response_text = response.choices[0].message.content
                if not response_text:
                    raise ValueError("Empty response from AI model")

                self._log_verbose("AI Response", response_text)

                return response_text

            except Exception as e:
                last_error = e

                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⚠️  Error: {str(e)}")
                    print(f"⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    break

        error_msg = f"Failed after {self.max_retries} attempts: {last_error}"
        raise self._get_error_class()(error_msg)

    @abstractmethod
    def _get_error_class(self) -> type[Exception]:
        """Return the appropriate exception class for this generator."""
        pass

    def generate(self, *args, **kwargs) -> T:
        """Main generation method. Subclasses can override for custom logic."""
        # Build prompt
        prompt = self._build_prompt(*args, **kwargs)

        # Handle both single string and tuple return
        if isinstance(prompt, tuple):
            system_prompt, user_prompt = prompt
        else:
            system_prompt = prompt
            user_prompt = args[0] if args else ""

        # Call AI
        response_text = self._call_ai(system_prompt, user_prompt)

        # Parse response
        parsed_data = self._parse_response(response_text)

        # Construct typed result
        return self._construct_result(parsed_data)
```

### idea.py - IdeaGenerator (50 lines!)
```python
"""Story idea generation using AI."""

from storygen.iterative.models import StoryIdea
from storygen.iterative.generators.base import BaseGenerator


class IdeaGenerationError(Exception):
    """Raised when idea generation fails."""
    pass


class IdeaGenerator(BaseGenerator[StoryIdea]):
    """Generates story ideas using AI."""

    def _build_prompt(self, user_prompt: str, story_type: str) -> str:
        """Build the system prompt for idea generation."""
        scope_guidance = {
            "flash-fiction": "FLASH FICTION (<1,500 words): Single moment...",
            "short-story": "SHORT STORY (1,500-7,500 words): Single plot...",
            # ... etc
        }

        scope = scope_guidance.get(story_type, scope_guidance["short-story"])

        return f"""You are a creative writing assistant...
{scope}

Your task is to take a brief story concept and expand it...

Return JSON: {{"raw_idea": "...", "one_sentence": "...", ...}}
"""

    def _parse_response(self, response_text: str) -> dict:
        """Parse and validate idea JSON."""
        # Remove markdown fences
        text = response_text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        data = json.loads(text)

        # Validate required fields
        required = ["raw_idea", "one_sentence", "expanded",
                   "genres", "tone", "themes", "setting"]
        missing = [f for f in required if f not in data]
        if missing:
            raise IdeaGenerationError(f"Missing fields: {missing}")

        return data

    def _construct_result(self, data: dict) -> StoryIdea:
        """Construct StoryIdea from parsed data."""
        return StoryIdea(
            raw_idea=data["raw_idea"],
            one_sentence=data["one_sentence"],
            expanded=data["expanded"],
            genres=data["genres"],
            tone=data["tone"],
            themes=data["themes"],
            setting=data["setting"],
        )

    def _get_error_class(self) -> type[Exception]:
        return IdeaGenerationError
```

### character.py - CharacterGenerator (80 lines!)
```python
"""Character generation using AI."""

from storygen.iterative.models import Character, StoryIdea
from storygen.iterative.generators.base import BaseGenerator


class CharacterGenerationError(Exception):
    """Raised when character generation fails."""
    pass


class CharacterGenerator(BaseGenerator[list[Character]]):
    """Generates characters using AI."""

    def _build_prompt(self, story_idea: StoryIdea, story_type: str) -> tuple[str, str]:
        """Build system and user prompts."""
        naming_guidance = self._get_naming_guidance(story_idea.genres, story_idea.tone)

        system_prompt = f"""You are a character designer...
{naming_guidance}

Return JSON: {{"characters": [...]}}
"""

        user_prompt = f"""Story Idea: {story_idea.one_sentence}
Setting: {story_idea.setting}
Tone: {story_idea.tone}
Genres: {', '.join(story_idea.genres)}

Generate 2-4 characters..."""

        return system_prompt, user_prompt

    def _get_naming_guidance(self, genres: list[str], tone: str) -> str:
        """Style-appropriate naming guidance."""
        # ... existing naming logic ...

    def _parse_response(self, response_text: str) -> list[dict]:
        """Parse and validate character JSON."""
        # ... existing parsing logic ...

    def _construct_result(self, char_dicts: list[dict]) -> list[Character]:
        """Construct Character objects."""
        return [Character(  # type: ignore
            name=c["name"],
            role=c["role"],
            bio=c["bio"],
            goal=c["goal"],
            flaw=c["flaw"],
            arc=c.get("arc"),
        ) for c in char_dicts]

    def _get_error_class(self) -> type[Exception]:
        return CharacterGenerationError
```

---

## Benefits Summary

### Before Refactor
- **IdeaGenerator**: 252 lines (107 in generate())
- **CharacterGenerator**: 341 lines (107 in generate())
- **LocationGenerator**: 286 lines (104 in generate())
- **OutlineGenerator**: 472 lines
- **BreakdownGenerator**: 446 lines
- **ProseGenerator**: 638 lines
- **TitleGenerator**: 298 lines
- **TOTAL**: ~2,733 lines with ~700 duplicated

### After Refactor
- **BaseGenerator**: 150 lines (shared by all)
- **IdeaGenerator**: ~50 lines (prompt + parsing only)
- **CharacterGenerator**: ~80 lines
- **LocationGenerator**: ~60 lines
- **OutlineGenerator**: ~120 lines
- **BreakdownGenerator**: ~100 lines
- **ProseGenerator**: ~200 lines
- **TitleGenerator**: ~80 lines
- **TOTAL**: ~840 lines (saving 1,893 lines!)

### Additional Benefits
✅ Bug fixes propagate to all generators automatically
✅ Easy to add streaming support (just modify `_call_ai()`)
✅ Easy to add caching (wrap `_call_ai()`)
✅ Easy to add rate limiting (throttle in `_call_ai()`)
✅ Consistent error handling across all generators
✅ Consistent verbose logging
✅ Type-safe with generics

---

## Migration Path

### Phase 1: Create BaseGenerator
1. Create `generators/base.py` with BaseGenerator class
2. Add comprehensive tests for BaseGenerator
3. Verify all retry/error/logging logic works

### Phase 2: Migrate Simple Generators First
4. Migrate IdeaGenerator (simplest)
5. Run tests - should be 100% passing
6. Migrate LocationGenerator
7. Run tests
8. Migrate CharacterGenerator

### Phase 3: Migrate Complex Generators
9. Migrate OutlineGenerator (may need custom generate())
10. Migrate TitleGenerator
11. Migrate BreakdownGenerator (complex, may override generate())
12. Migrate ProseGenerator (most complex)

### Phase 4: Cleanup
13. Remove duplicate code patterns
14. Update documentation
15. Archive old versions in git

**Estimated Time**: 8-10 hours total
**Risk Level**: LOW (tests catch any issues immediately)
**Impact**: HIGH (makes all future development easier)
