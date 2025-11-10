"""Comprehensive test of scene break logic."""

import re
from zipfile import ZipFile

from storygen.epub import generate_epub
from storygen.models import Scene, Story

# Create story with all three scenarios:
# 1. POV change (should get ornament)
# 2. Time/location change (should get whitespace)
# 3. Continuous flow (should get nothing)

story = Story(
    title="Scene Break Test",
    genre="Test",
    summary="Testing all scene break scenarios",
    scenes=[
        Scene(
            number=1,
            title="Scene 1",
            content="Alice starts the story in her office.",
            pov_character="Alice",
            location="Office",
            time_hours=0.0,
        ),
        Scene(
            number=2,
            title="Scene 2",
            content="Bob takes over the narrative.",  # POV CHANGE → ornament
            pov_character="Bob",
            location="Office",
            time_hours=0.5,
        ),
        Scene(
            number=3,
            title="Scene 3",
            content="Bob continues but moves to a different place.",  # LOCATION CHANGE → whitespace
            pov_character="Bob",
            location="Warehouse",
            time_hours=1.0,
        ),
        Scene(
            number=4,
            title="Scene 4",
            content="Bob continues with a big time jump.",  # TIME GAP → whitespace
            pov_character="Bob",
            location="Warehouse",
            time_hours=5.0,  # >2 hour gap
        ),
    ],
)

path = generate_epub(story, "output/comprehensive_test.epub", "Test")
print(f"✅ EPUB created: {path}\n")

# Analyze the breaks
with ZipFile(path) as z:
    content = z.read("EPUB/story.xhtml").decode("utf-8")
    breaks = re.findall(r'<p class="scene-break">([^<]*)</p>', content)

    print("Scene Transitions Analysis:")
    print("=" * 50)

    transitions = [
        "Scene 1→2: POV change (Alice→Bob)",
        "Scene 2→3: Location change (Office→Warehouse)",
        "Scene 3→4: Time gap (1.0→5.0 hours)",
    ]

    for i, (transition, break_content) in enumerate(zip(transitions, breaks), 1):
        has_ornament = "—" in break_content
        is_whitespace = break_content == "\xa0"

        print(f"\n{i}. {transition}")
        if has_ornament:
            print("   ✓ Ornamental break (— • —)")
        elif is_whitespace:
            print("   ✓ Whitespace break (nbsp)")
        else:
            print(f"   ✗ Unexpected: {repr(break_content)}")

    print("\n" + "=" * 50)
    ornaments = sum(1 for b in breaks if "—" in b)
    whitespace = sum(1 for b in breaks if b == "\xa0")

    print("\nSummary:")
    print(f"  Ornamental breaks (POV): {ornaments} (expected: 1)")
    print(f"  Whitespace breaks (time/loc): {whitespace} (expected: 2)")

    if ornaments == 1 and whitespace == 2:
        print("\n🎉 Perfect! All scene break logic working correctly!")
    else:
        print("\n⚠️  Unexpected break pattern")
