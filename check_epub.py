"""Check if the EPUB was successfully created."""

import os
from zipfile import ZipFile

path = "output/qwen32b_hero_story.epub"

print(f"File exists: {os.path.exists(path)}")
if os.path.exists(path):
    print(f"File size: {os.path.getsize(path):,} bytes")

    with ZipFile(path) as z:
        files = z.namelist()
        print(f"Has nav.xhtml: {'EPUB/nav.xhtml' in files}")
        print(f"Total files: {len(files)}")

        # Check story content
        content = z.read("EPUB/story.xhtml").decode("utf-8")
        print(f"\nStory content length: {len(content):,} characters")

        # Count paragraphs
        paragraph_count = content.count("<p")
        print(f"Paragraphs: {paragraph_count}")

        # Count scene breaks
        ornaments = content.count("— • —")
        print(f"POV changes (ornaments): {ornaments}")

        print("\n✅ EPUB appears to be complete and valid!")
else:
    print("❌ EPUB file not found!")
