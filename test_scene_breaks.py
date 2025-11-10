"""Check scene break rendering."""

import re
from zipfile import ZipFile

with ZipFile("output/whitespace_test.epub") as z:
    content = z.read("EPUB/story.xhtml").decode("utf-8")

    # Find all scene-break paragraphs
    breaks = re.findall(r'<p class="scene-break">([^<]*)</p>', content)

    print("Scene break contents:")
    for i, b in enumerate(breaks):
        print(f"  {i+1}: {repr(b)}")
        if "—" in b:
            print("      → Ornamental (POV change)")
        elif b.strip():
            print("      → Whitespace (time/location)")
        else:
            print("      → Empty?")

    print(f"\nTotal scene breaks: {len(breaks)}")
    ornamental = sum(1 for b in breaks if "—" in b)
    whitespace = sum(1 for b in breaks if "—" not in b and b.strip())
    print(f"Ornamental (with —): {ornamental}")
    print(f"Whitespace (nbsp): {whitespace}")
