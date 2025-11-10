from zipfile import ZipFile

from storygen.epub import generate_epub
from storygen.models import Scene, Story

# Create a story with same POV but different locations to test whitespace breaks
story = Story(
    title="Detective Jones Investigation",
    genre="Mystery",
    summary="Detective follows leads across town",
    characters=["Detective Jones", "Witness Smith"],
    scenes=[
        Scene(
            number=1,
            title="Scene 1 - Office",
            content="Detective Jones reviewed the case files at his desk.\n\nThe evidence was thin, but he had a lead.",
            pov_character="Detective Jones",
            location="Police Station",
            time_hours=0.0,
        ),
        Scene(
            number=2,
            title="Scene 2 - Crime Scene",
            content="The crime scene was cordoned off with yellow tape.\n\nJones examined the broken window carefully.",
            pov_character="Detective Jones",  # Same POV
            location="Abandoned Warehouse",  # Different location
            time_hours=2.0,  # Small time gap
        ),
        Scene(
            number=3,
            title="Scene 3 - Interview",
            content="Mr. Smith sat nervously across the table.\n\nJones leaned forward, watching for tells.",
            pov_character="Detective Jones",  # Same POV
            location="Interview Room",  # Different location
            time_hours=8.0,  # Large time gap (>2 hours)
        ),
    ],
)

path = generate_epub(story, "output/whitespace_test.epub", "Test Author")
print(f"EPUB created: {path}")

# Check content
with ZipFile(path) as z:
    content = z.read("EPUB/story.xhtml").decode("utf-8")
    ornaments = content.count("  ")
    whitespace = content.count("&#160;")
    no_indent_class = 'class="no-indent"'
    no_indent_count = content.count(no_indent_class)
    print(f"\nOrnamental breaks (POV changes): {ornaments}")
    print(f"Whitespace breaks (time/location): {whitespace}")
    print(f"No-indent paragraphs: {no_indent_count}")

    if whitespace > 0:
        print("\n Whitespace breaks are working!")
    else:
        print("\n  Expected whitespace breaks between scenes")
