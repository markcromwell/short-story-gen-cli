"""Check for bold italic markdown issue."""

import re
from zipfile import ZipFile

with ZipFile("output/qwen32b_hero_story_1.epub") as z:
    content = z.read("EPUB/story.xhtml").decode("utf-8")

    # Look for literal "bold italic" text
    literal_matches = re.findall(r"<strong>bold italic</strong>", content, re.IGNORECASE)
    print(f"Found {len(literal_matches)} instances of literal 'bold italic' text")

    # Look for bold with italic inside
    nested_matches = re.findall(r"<strong><em>.*?</em></strong>", content)
    print(f"Found {len(nested_matches)} properly formatted bold+italic")

    # Look for any "bold" or "italic" words in the text
    word_bold = content.lower().count("bold")
    word_italic = content.lower().count("italic")
    print(f"Word 'bold' appears {word_bold} times")
    print(f"Word 'italic' appears {word_italic} times")

    # Show first paragraph
    body_start = content.find("<body>")
    body_content = content[body_start : body_start + 1000]
    print(f"\nFirst 500 chars of body:\n{body_content[:500]}")

    # Look for the specific phrase
    if "bold italic" in content.lower():
        print("\n⚠️  Found 'bold italic' phrase in content")
        idx = content.lower().find("bold italic")
        print(f"Context:\n{content[max(0,idx-100):idx+200]}")
