from zipfile import ZipFile

from storygen.epub import generate_epub
from storygen.models import Scene, Story

# Create a simple story with proper content
story = Story(
    title="The Fixed EPUB Test",
    genre="Mystery",
    summary="Testing the nav.xhtml fix",
    characters=["Detective Jones", "Mr. Smith"],
    scenes=[
        Scene(
            number=1,
            title="Scene 1",
            content="This is the first scene with some content.\n\nIt has multiple paragraphs to test formatting.",
            pov_character="Detective Jones",
            location="Office",
            time_hours=0.0,
        ),
        Scene(
            number=2,
            title="Scene 2",
            content="This is the second scene.\n\nIt also has content to make sure the EPUB is valid.",
            pov_character="Detective Jones",
            location="Street",
            time_hours=1.0,
        ),
    ],
)

# Generate EPUB
path = generate_epub(story, "output/nav_fixed_test.epub", "Test Author")
print(f"EPUB created: {path}")

# Verify nav.xhtml exists
with ZipFile(path) as z:
    files = z.namelist()
    nav_exists = any("nav.xhtml" in f for f in files)
    print(f"nav.xhtml exists: {nav_exists}")
    if nav_exists:
        print("SUCCESS! The fix works!")
    else:
        print("ERROR: nav.xhtml still missing")
        print("Files:", [f for f in files if "EPUB" in f])
