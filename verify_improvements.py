"""Verify the EPUB improvements from ChatGPT feedback."""

from zipfile import ZipFile

epub_path = "output/final_test_3.epub"

with ZipFile(epub_path) as z:
    content = z.read("EPUB/story.xhtml").decode("utf-8")

    print(" EPUB Scene Break Improvements\n")
    print("=" * 50)

    # Check for ornamental breaks (POV changes) - should have "  "
    ornament_count = content.count("  ")
    print(f" POV ornamental breaks (  ): {ornament_count}")

    # Check for whitespace breaks - should have &#160; (non-breaking space)
    whitespace_count = content.count("&#160;")
    print(f" Time/location spacer breaks (&#160;): {whitespace_count}")

    # Check no-indent paragraphs (first para after each break)
    no_indent_count = content.count('class="no-indent"')
    print(f" No-indent paragraphs: {no_indent_count}")

    # Verify NO <hr> elements anymore
    has_hr = "<hr" in content
    print(f" No <hr> horizontal rules: {not has_hr}")

    # Verify NO old .scene-gap class
    has_old_gap = 'class="scene-gap"' in content
    print(f" No old scene-gap class: {not has_old_gap}")

    # Show some context
    print("\n" + "=" * 50)
    print("Sample of scene breaks in content:\n")

    # Find first ornament
    if "  " in content:
        idx = content.find("  ")
        print("Ornamental break context:")
        print(content[max(0, idx - 50) : idx + 100])
        print()

    # Find first whitespace
    if "&#160;" in content:
        idx = content.find("&#160;")
        print("Whitespace break context:")
        print(content[max(0, idx - 50) : idx + 100])

    print("\n" + "=" * 50)
    if ornament_count > 0 and not has_hr and not has_old_gap:
        print(" All scene break improvements successfully applied!")
        print(f"   {ornament_count} POV shifts with ornaments")
        print(f"   {whitespace_count} time/location shifts with whitespace")
    else:
        print("  Some improvements may not be working correctly")
