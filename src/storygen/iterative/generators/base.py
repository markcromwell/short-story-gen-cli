"""Base generator class with shared functionality for all story generators."""

import json
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Generic, TypeVar

import litellm

# Type variable for return type of generate methods
T = TypeVar("T")


class GenerationError(Exception):
    """Base exception for all generation errors."""

    pass


class BaseGenerator(ABC, Generic[T]):
    """Abstract base class for all story generators.

    Provides common functionality:
    - Retry logic with exponential backoff
    - Error handling and logging
    - Timeout management
    - Response parsing framework
    - Verbose output control

    Subclasses must implement:
    - _build_prompt(): Build the system/user prompts
    - _parse_response(): Parse and validate AI response
    - generate(): Main generation method using _generate_with_retry()
    """

    def __init__(
        self,
        model: str = "anthropic/claude-3-5-sonnet-20241022",
        max_retries: int = 3,
        timeout: int = 120,
        verbose: bool = False,
    ):
        """
        Initialize the base generator.

        Args:
            model: LiteLLM model identifier (e.g., "anthropic/claude-3-5-sonnet-20241022")
            max_retries: Maximum number of retry attempts on failure
            timeout: Timeout in seconds for each AI call
            verbose: If True, print detailed debug information
        """
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.verbose = verbose
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def _build_prompt(self, *args: Any, **kwargs: Any) -> Any:
        """Build the system prompt for the AI.

        Subclasses must implement this to construct their specific prompts.
        Can return a string (system prompt) or tuple[str, str] (system, user).

        Returns:
            System prompt string or tuple of (system_prompt, user_prompt)
        """
        pass

    @abstractmethod
    def _parse_response(self, response_text: str) -> Any:
        """Parse and validate the AI response.

        Subclasses must implement this to parse their specific response formats.

        Args:
            response_text: Raw text response from AI

        Returns:
            Parsed data structure

        Raises:
            GenerationError: If response is invalid or malformed
        """
        pass

    def _log_request(self, system_prompt: str, user_prompt: str) -> None:
        """Log the request being sent to the AI (if verbose)."""
        if self.verbose:
            print("\n" + "=" * 80)
            print("SENDING TO AI MODEL:")
            print("=" * 80)
            print(f"\nSYSTEM PROMPT:\n{system_prompt}\n")
            print(f"\nUSER PROMPT:\n{user_prompt}\n")
            print("=" * 80)

        self.logger.debug(f"Sending request to {self.model}")
        self.logger.debug(f"System prompt length: {len(system_prompt)} chars")
        self.logger.debug(f"User prompt length: {len(user_prompt)} chars")

    def _log_response(self, response_text: str) -> None:
        """Log the response received from the AI (if verbose)."""
        if self.verbose:
            print("\n" + "=" * 80)
            print("RECEIVED FROM AI MODEL:")
            print("=" * 80)
            print(f"\n{response_text}\n")
            print("=" * 80)

        self.logger.debug(f"Received response length: {len(response_text)} chars")

    def _log_parsed(self, parsed_data: Any) -> None:
        """Log the parsed data (if verbose).

        Subclasses can override to provide custom logging.
        """
        if self.verbose:
            print("\n" + "=" * 80)
            print("PARSED RESULT:")
            print("=" * 80)
            print(f"\n{parsed_data}\n")
            print("=" * 80)

    def _call_ai(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.8,
        stream: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Call the AI model with retry logic.

        Args:
            system_prompt: System prompt defining the task
            user_prompt: User's specific request
            temperature: Sampling temperature (0.0-1.0)
            stream: Whether to use streaming
            **kwargs: Additional arguments to pass to litellm.completion

        Returns:
            Response text from AI

        Raises:
            GenerationError: If AI call fails
        """
        # Debug logging
        if self.verbose:
            self.logger.debug(f"System prompt length: {len(system_prompt)} chars")
            self.logger.debug(f"User prompt length: {len(user_prompt)} chars")
            self.logger.debug(f"System prompt preview: {system_prompt[:200]}...")
            self.logger.debug(f"User prompt preview: {user_prompt[:200]}...")

        response = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            timeout=self.timeout,
            temperature=temperature,
            stream=stream,
            **kwargs,
        )

        # Extract response text
        if not hasattr(response, "choices") or not response.choices:  # type: ignore[union-attr]
            raise GenerationError("Invalid response format from AI model")

        response_text = response.choices[0].message.content  # type: ignore[union-attr]
        if self.verbose:
            self.logger.debug(f"Response text: {response_text[:500] if response_text else 'NONE'}")
        if not response_text:
            raise GenerationError("Empty response from AI model")

        return response_text  # type: ignore[no-any-return]

    def _generate_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        parser: Callable[[str], T],
        temperature: float = 0.8,
        error_class: type[Exception] = GenerationError,
    ) -> T:
        """
        Generate content with automatic retry on failure.

        Args:
            system_prompt: System prompt for the AI
            user_prompt: User prompt for the AI
            parser: Function to parse the AI response
            temperature: Sampling temperature
            error_class: Exception class to raise on final failure

        Returns:
            Parsed result

        Raises:
            error_class: If generation fails after all retries
        """
        self._log_request(system_prompt, user_prompt)

        last_error = None
        current_user_prompt = user_prompt
        for attempt in range(self.max_retries):
            try:
                # Call AI
                response_text = self._call_ai(system_prompt, current_user_prompt, temperature)
                self._log_response(response_text)

                # Parse and validate
                parsed_data = parser(response_text)
                self._log_parsed(parsed_data)

                self.logger.info(f"Successfully generated after {attempt + 1} attempt(s)")
                return parsed_data

            except Exception as e:
                last_error = e
                self.logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")

                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff: 1, 2, 4, 8...
                    self.logger.info(f"Retrying in {wait_time} seconds...")

                    # Add error feedback to next attempt
                    current_user_prompt = f"{user_prompt}\n\nPREVIOUS ATTEMPT FAILED: {e}\nPlease correct this issue in your response."

                    if self.verbose:
                        print(f"\n⚠️  Attempt {attempt + 1} failed: {e}")
                        print(f"Retrying in {wait_time} seconds...\n")

                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    if self.verbose:
                        print(f"\n❌ All {self.max_retries} attempts failed")

        # All retries exhausted
        error_msg = (
            f"Failed to generate after {self.max_retries} attempts. Last error: {last_error}"
        )
        self.logger.error(error_msg)
        raise error_class(error_msg)

    def parse_json_response(
        self,
        response_text: str,
        required_fields: list[str] | None = None,
        error_class: type[Exception] = GenerationError,
    ) -> dict[str, Any]:
        """
        Parse and validate JSON response from AI.

        Handles common patterns:
        - JSON wrapped in markdown code blocks
        - JSON validation against required fields
        - Consistent error handling

        Args:
            response_text: Raw text response from AI
            required_fields: List of required field names (optional)
            error_class: Exception class to raise on error

        Returns:
            Parsed JSON dict

        Raises:
            error_class: If response is invalid or missing required fields
        """
        # Try to extract JSON if wrapped in markdown code blocks
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise error_class(f"Failed to parse JSON response: {e}")

        # Validate required fields if specified
        if required_fields:
            missing = [f for f in required_fields if f not in data]
            if missing:
                raise error_class(f"Missing required fields: {missing}")

        return data  # type: ignore[no-any-return]

    def parse_json_array_response(
        self,
        response_text: str,
        min_items: int = 1,
        error_class: type[Exception] = GenerationError,
    ) -> list[dict[str, Any]]:
        """
        Parse and validate JSON array response from AI.

        Handles common patterns:
        - JSON arrays wrapped in markdown code blocks
        - Extraction of multiple JSON objects if array parsing fails
        - Validation of minimum item count
        - Consistent error handling

        Args:
            response_text: Raw text response from AI
            min_items: Minimum number of items required in array
            error_class: Exception class to raise on error

        Returns:
            Parsed JSON array

        Raises:
            error_class: If response is invalid or has insufficient items
        """
        # Try to extract JSON if wrapped in markdown code blocks
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # Try to parse as array first
        array_start = text.find("[")
        if array_start != -1:
            # Find matching closing bracket for array
            bracket_count = 0
            end_idx = -1
            for i in range(array_start, len(text)):
                if text[i] == "[":
                    bracket_count += 1
                elif text[i] == "]":
                    bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i + 1
                        break

            if end_idx != -1:
                json_text = text[array_start:end_idx]
                try:
                    data = json.loads(json_text)
                    if isinstance(data, list):
                        # Successfully parsed array format
                        if len(data) < min_items:
                            raise error_class(
                                f"Array must contain at least {min_items} items, got {len(data)}"
                            )
                        return data  # type: ignore[no-any-return]
                except json.JSONDecodeError:
                    # Array parsing failed, fall through to object extraction
                    pass

        # If array format failed, try extracting multiple { } objects
        objects = []
        pos = 0
        while pos < len(text):
            # Find next object start
            obj_start = text.find("{", pos)
            if obj_start == -1:
                break

            # Find matching closing brace
            brace_count = 0
            obj_end = -1
            for i in range(obj_start, len(text)):
                if text[i] == "{":
                    brace_count += 1
                elif text[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        obj_end = i + 1
                        break

            if obj_end == -1:
                break

            # Try to parse this object
            obj_text = text[obj_start:obj_end]
            try:
                obj = json.loads(obj_text)
                # Only add if it looks like a valid object
                if isinstance(obj, dict):
                    objects.append(obj)
            except json.JSONDecodeError:
                pass

            pos = obj_end

        if not objects:
            raise error_class("No valid JSON array or objects found in response")

        if len(objects) < min_items:
            raise error_class(
                f"Response must contain at least {min_items} items, got {len(objects)}"
            )

        return objects  # type: ignore[no-any-return]

    def generate_with_json_parser(
        self,
        system_prompt: str,
        user_prompt: str,
        required_fields: list[str] | None = None,
        temperature: float = 0.8,
        error_class: type[Exception] = GenerationError,
    ) -> dict[str, Any]:
        """
        Generate content using JSON parsing pattern.

        This is a convenience method for generators that:
        - Send system + user prompts
        - Expect JSON responses
        - Have standard validation requirements

        Args:
            system_prompt: System prompt for the AI
            user_prompt: User prompt for the AI
            required_fields: List of required field names in JSON response
            temperature: Sampling temperature
            error_class: Exception class to raise on error

        Returns:
            Parsed JSON dict

        Raises:
            error_class: If generation or parsing fails
        """

        # Parser that uses the common JSON parsing logic
        def parse_json(response_text: str) -> dict[str, Any]:
            return self.parse_json_response(response_text, required_fields, error_class)

        # Use base class retry logic with type casting
        return self._generate_with_retry(  # type: ignore[return-value]
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            parser=parse_json,
            temperature=temperature,
            error_class=error_class,
        )

    @abstractmethod
    def generate(self, *args: Any, **kwargs: Any) -> T:
        """Generate the content.

        Subclasses must implement this method to define their specific generation logic.
        Should typically call _generate_with_retry() internally.

        Returns:
            Generated content of type T
        """
        pass
