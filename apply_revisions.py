import asyncio
import json

from storygen.editorial.cli.commands import _apply_revisions_with_ai
from storygen.editorial.core.config import load_editorial_config
from storygen.editorial.core.model_manager import ModelManager


async def apply_revisions():
    # Load the original prose
    with open("examples/test_prose.json", encoding="utf-8") as f:
        story_data = json.load(f)

    # Load the feedback
    with open("integration_test_xai.json", encoding="utf-8") as f:
        feedback_data = json.load(f)  # Initialize model manager
    config = load_editorial_config()
    model_manager = ModelManager(config)
    model_manager.current_model = "xai/grok-4-fast-reasoning"

    # Apply revisions
    print("Applying editorial revisions...")
    revised_story = await _apply_revisions_with_ai(
        story_data, feedback_data["suggested_revisions"], model_manager, max_cost=None, verbose=True
    )

    # Save the result
    with open("revised_story_xai.json", "w") as f:
        json.dump(revised_story, f, indent=2)

    print("Revised story saved to revised_story_xai.json")

    # Show a summary
    print(f'Original scenes: {len(story_data["scene_sequels"])}')
    print(f'Revised scenes: {len(revised_story["scene_sequels"])}')
    print(f'Total word count: {revised_story["total_actual_words"]}')


if __name__ == "__main__":
    asyncio.run(apply_revisions())
