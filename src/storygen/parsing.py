"""
Robust JSON parsing and sanitization for LLM outputs.

This module provides defensive parsing utilities to handle malformed JSON
from language models that don't strictly adhere to JSON specifications.
"""

import json
import re
from typing import Any

JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)


def _balanced_json_object(text: str) -> str | None:
    """
    Return the first top-level {...} block using brace counting with basic
    string/escape handling. Returns None if no complete object is found.
    """
    start = None
    depth = 0
    in_string = False
    escape = False

    for i, ch in enumerate(text):
        if start is None:
            if ch == "{":
                start = i
                depth = 1
            continue

        # After we've seen a '{', track until we close it.
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start is not None:
                    return text[start : i + 1]

    return None


def _escape_newlines_in_strings(s: str) -> str:
    """
    Walk through the text and replace raw newlines inside double-quoted strings
    with literal '\\n', so json.loads won't die on 'invalid control character'.
    This is a minimal streaming tokenizer, not a full JSON parser, but good enough
    for typical LLM output.
    """
    out = []
    in_string = False
    escape = False

    for ch in s:
        if not in_string:
            if ch == '"':
                in_string = True
                out.append(ch)
            else:
                out.append(ch)
        else:
            if escape:
                # whatever comes after a backslash is taken literally
                out.append(ch)
                escape = False
            elif ch == "\\":
                out.append(ch)
                escape = True
            elif ch == '"':
                in_string = False
                out.append(ch)
            elif ch == "\n":
                # newline inside a string → escape it
                out.append("\\n")
            elif ch == "\t":
                out.append("\\t")
            elif ord(ch) < 0x20:
                # drop other control chars inside strings
                continue
            else:
                out.append(ch)

    return "".join(out)


def extract_json_block(text: str) -> str:
    """
    Grab the first {...} block using brace balancing.
    Falls back to greedy regex if balanced approach fails.

    Handles reasoning model outputs (like qwen3) that include "Thinking..." sections
    before the actual JSON output.

    Args:
        text: Raw text that may contain JSON embedded in other content

    Returns:
        Extracted JSON string

    Raises:
        ValueError: If no JSON object is found
    """
    # Strip reasoning model "thinking" blocks (qwen3, deepseek-r1, etc.)
    # These models output their reasoning process before the actual response
    # Pattern: "Thinking...\n<reasoning>\n...done thinking.\n<actual output>"
    thinking_pattern = r"Thinking\.{3}.*?\.{3}done thinking\."
    text = re.sub(thinking_pattern, "", text, flags=re.DOTALL | re.IGNORECASE)

    # Also strip simpler thinking markers
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"\[thinking\].*?\[/thinking\]", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Try brace-balanced extraction first
    balanced = _balanced_json_object(text)
    if balanced:
        return balanced

    # Fallback to greedy regex
    m = JSON_OBJ_RE.search(text)
    if not m:
        raise ValueError("No JSON object found in model output.")
    return m.group(0)


def sanitize_llm_json(text: str) -> str:
    """
    Take dubious LLM 'JSON' and coerce it into something json.loads() can handle,
    without trying to be too magical.

    Handles common LLM JSON issues:
    - Triple-quoted strings (Python-style)
    - Code fences (```json```)
    - Illegal ASCII control characters
    - Curly quotes
    - Malformed keys

    Args:
        text: Raw JSON-like text from LLM

    Returns:
        Sanitized JSON string ready for json.loads()

    Raises:
        ValueError: If no JSON object can be extracted
    """
    # Extract just the outer JSON object if there's surrounding prose/markdown
    text = extract_json_block(text)

    # Remove code fences if present (both opening and closing)
    text = re.sub(r"```[a-zA-Z0-9]*", "", text)
    text = text.replace("```", "")

    # Replace triple-quoted strings (Python-style) with proper JSON strings
    # """...""" -> "..."
    def _triple_to_json(m):
        inner = m.group(1)
        # Let json.dumps handle escaping safely
        return json.dumps(inner)

    text = re.sub(r'"""(.*?)"""', _triple_to_json, text, flags=re.DOTALL)
    text = re.sub(r"'''(.*?)'''", _triple_to_json, text, flags=re.DOTALL)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove illegal ASCII control chars (keep tab, newline)
    # JSON spec allows 0x09, 0x0A, 0x0D inside strings only when escaped,
    # but in practice we'll keep them raw and let json.dumps-style encoding handle.
    text = "".join(ch for ch in text if (ord(ch) >= 0x20) or ch in "\n\t")

    # Normalize some common curly quotes to straight quotes to reduce parse weirdness
    # Using Unicode code points to avoid encoding issues
    trans = {
        0x201C: ord('"'),  # Left double quotation mark
        0x201D: ord('"'),  # Right double quotation mark
        0x2018: ord("'"),  # Left single quotation mark
        0x2019: ord("'"),  # Right single quotation mark
    }
    text = text.translate(trans)

    # Ensure raw newlines inside strings are escaped
    text = _escape_newlines_in_strings(text)

    # Sometimes models break a key like: `" - : 3,`
    # We can't fully auto-fix arbitrary nonsense, but we can drop lines that are obviously invalid.
    clean_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        # Heuristic: drop lines that look like broken keys with no colon+value structure
        if stripped and stripped.startswith('"') and '":' not in stripped:
            # e.g. '" - : 3,' -> nuke it
            # Skip this line as it's clearly malformed
            continue
        clean_lines.append(line)
    text = "\n".join(clean_lines)

    # Remove trailing commas before closing brackets/braces
    text = re.sub(r",(\s*[}\]])", r"\1", text)

    # Fix incomplete JSON if truncated - add missing closing braces
    # Count opening and closing braces/brackets to ensure balance
    open_braces = text.count("{")
    close_braces = text.count("}")
    open_brackets = text.count("[")
    close_brackets = text.count("]")

    if open_braces > close_braces or open_brackets > close_brackets:
        # Likely truncated - add missing closings
        text = text.rstrip()
        # Remove trailing comma if present at end
        if text.endswith(","):
            text = text[:-1]
        # Add missing closing brackets/braces
        text += "\n" + "]" * (open_brackets - close_brackets)
        text += "\n" + "}" * (open_braces - close_braces)

    return text


def parse_story_json(text: str) -> Any:
    """
    Full pipeline: sanitize then json.loads with clear error if it still fails.

    Args:
        text: Raw JSON text from LLM

    Returns:
        Parsed JSON as Python dict/list

    Raises:
        ValueError: If JSON cannot be parsed after sanitization
    """
    clean = sanitize_llm_json(text)
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        # Optional: write clean to a debug file for inspection
        # Uncomment for debugging:
        # with open("debug_story.json", "w", encoding="utf-8") as f:
        #     f.write(clean)
        raise ValueError(
            f"Failed to parse story JSON after sanitation: {e}\n\nCleaned content:\n{clean[:500]}..."
        )
