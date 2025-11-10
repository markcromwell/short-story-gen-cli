from ebooklib import epub

from storygen.models import Scene, Story

story = Story(
    title="Test",
    genre="Mystery",
    scenes=[
        Scene(
            number=1,
            title="S1",
            content="Content here.",
            pov_character="Bob",
            location="Home",
            time_hours=0.0,
        )
    ],
)

book = epub.EpubBook()
book.set_identifier("test123")
book.set_title(story.title)
book.set_language("en")
book.add_author("Test")

# Create a simple chapter
ch = epub.EpubHtml(title="Chapter", file_name="ch1.xhtml")
ch.content = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Test</title></head>
<body><p>Hello world</p></body>
</html>"""

book.add_item(ch)
book.toc = (epub.Link("ch1.xhtml", "Chapter", "ch1"),)
book.add_item(epub.EpubNcx())
nav = epub.EpubNav()
book.add_item(nav)
book.spine = [nav, ch]

print("Trying to write...")
try:
    epub.write_epub("output/simple_test.epub", book)
    print("SUCCESS!")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()
