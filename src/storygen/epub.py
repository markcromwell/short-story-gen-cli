"""
EPUB generation from Story models.
"""

import html
from datetime import datetime
from pathlib import Path
from typing import Optional

from ebooklib import epub  # type: ignore

from storygen.models import Story


def convert_markdown_to_html(text: str) -> str:
    """
    Convert basic markdown formatting to HTML for EPUB.

    Handles:
    - **bold** or __bold__ → <strong>bold</strong>
    - *italic* or _italic_ → <em>italic</em>
    - ***bold italic*** → <strong><em>bold italic</em></strong>

    Note: Input should be HTML-escaped first; this function only handles markdown.

    Args:
        text: Text with markdown formatting (already HTML-escaped)

    Returns:
        Text with HTML formatting
    """
    import re

    # Handle bold italic (must come first to avoid conflicting with bold/italic alone)
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    text = re.sub(r"___(.+?)___", r"<strong><em>\1</em></strong>", text)

    # Handle bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)

    # Handle italic
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"_(.+?)_", r"<em>\1</em>", text)

    return text


def generate_epub(story: Story, output_path: str, author: str = "AI Generated") -> Path:
    """
    Generate an EPUB file from a Story object with clean structure & metadata.

    Args:
        story: Story object with title, scenes, and metadata
        output_path: Path where the EPUB file should be saved
        author: Author name for the EPUB metadata

    Returns:
        Path object pointing to the created EPUB file

    Example:
        >>> story = Story(title="My Story", scenes=[...])
        >>> epub_path = generate_epub(story, "my_story.epub", author="John Doe")
    """
    # Create EPUB book
    book = epub.EpubBook()

    # Core metadata
    book_id = f"story_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    book.set_identifier(book_id)
    book.set_title(story.title)
    book.set_language("en")
    book.add_author(author)

    if story.genre:
        book.add_metadata("DC", "subject", story.genre)

    if story.summary:
        book.add_metadata("DC", "description", story.summary)

    # Shared CSS stylesheet
    base_css = """
    body {
        font-family: Georgia, "Times New Roman", serif;
        line-height: 1.6;
        margin: 2em;
    }
    h1, h2 {
        font-weight: normal;
    }
    h1.book-title {
        font-size: 2.2em;
        margin-bottom: 0.5em;
        text-align: center;
    }
    h2.section-title {
        font-size: 1.4em;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
        text-align: center;
    }
    p {
        text-align: justify;
        margin: 0 0 0.7em 0;
        text-indent: 2em;
    }
    p.no-indent {
        text-indent: 0;
    }
    .title-page {
        margin-top: 25vh;
        text-align: center;
    }
    .title-page .book-title {
        font-size: 2.5em;
        margin-bottom: 0.3em;
    }
    .title-page .author {
        font-size: 1.3em;
        font-style: italic;
        margin-bottom: 1.2em;
        color: #555;
    }
    .title-page .meta {
        font-size: 0.95em;
        color: #555;
        margin-top: 0.5em;
    }
    .summary {
        max-width: 32em;
        margin: 1.5em auto 0 auto;
        font-style: italic;
        color: #555;
    }
    .scene-break {
        text-align: center;
        margin: 1.8em 0 1.2em 0;
        text-indent: 0;
        font-size: 1.1em;
    }
    hr.scene {
        border: none;
        border-top: 1px solid #666;
        margin: 1.8em 0 1.2em 0;
    }
    ul {
        margin-left: 1.5em;
        margin-bottom: 1em;
    }
    li {
        margin-bottom: 0.2em;
    }
    """

    style_item = epub.EpubItem(
        uid="style_book",
        file_name="style/book.css",
        media_type="text/css",
        content=base_css,
    )
    book.add_item(style_item)

    # Escape HTML in metadata
    safe_title = html.escape(story.title)
    safe_author = html.escape(author)
    safe_genre = html.escape(story.genre) if story.genre else ""
    safe_summary = html.escape(story.summary) if story.summary else ""

    # Title page with proper structure and linked stylesheet
    title_chapter = epub.EpubHtml(
        title="Title Page",
        file_name="title.xhtml",
        lang="en",
    )
    title_chapter.content = f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head>
    <title>{safe_title}</title>
    <link rel="stylesheet" type="text/css" href="style/book.css" />
  </head>
  <body epub:type="titlepage">
    <div class="title-page">
      <h1 class="book-title">{safe_title}</h1>
      <div class="author">by {safe_author}</div>
      {f'<div class="meta">{safe_genre}</div>' if safe_genre else ''}
      {f'<div class="summary">{safe_summary}</div>' if safe_summary else ''}
    </div>
  </body>
</html>
"""
    book.add_item(title_chapter)

    # Story content with proper structure and scene breaks
    story_chapter = epub.EpubHtml(
        title=story.title,
        file_name="story.xhtml",
        lang="en",
    )

    story_parts = [f'<h1 class="book-title">{safe_title}</h1>']

    for i, scene in enumerate(story.scenes):
        if i > 0:
            prev = story.scenes[i - 1]

            pov_changed = (
                scene.pov_character
                and prev.pov_character
                and scene.pov_character != prev.pov_character
            )

            time_gap = (
                scene.time_hours is not None
                and prev.time_hours is not None
                and abs(scene.time_hours - prev.time_hours) > 2.0
            )

            location_changed = scene.location and prev.location and scene.location != prev.location

            if pov_changed:
                # Strong visual break for POV shift
                story_parts.append('<p class="scene-break">— • —</p>')
            elif time_gap or location_changed:
                # Subtle break with semantic <hr>
                story_parts.append('<hr class="scene" />')

        raw_content = scene.content or ""
        blocks = [b.strip() for b in raw_content.split("\n\n") if b.strip()]

        for j, block in enumerate(blocks):
            # Escape HTML first, then apply markdown-ish formatting
            safe_block = html.escape(block)
            formatted = convert_markdown_to_html(safe_block)
            # First paragraph after scene start: no indent
            css_class = "no-indent" if (i == 0 and j == 0) else ""
            class_attr = f' class="{css_class}"' if css_class else ""
            story_parts.append(f"<p{class_attr}>{formatted}</p>")

    story_chapter.content = f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>{safe_title}</title>
    <link rel="stylesheet" type="text/css" href="style/book.css" />
  </head>
  <body>
    {''.join(story_parts)}
  </body>
</html>
"""
    book.add_item(story_chapter)

    # Dramatis Personae page at the end if characters are defined
    dramatis_personae = None
    characters = story.get_characters()
    if characters:
        dramatis_personae = epub.EpubHtml(
            title="Dramatis Personae",
            file_name="dramatis_personae.xhtml",
            lang="en",
        )

        characters_html = "<ul>"
        for character in characters:
            safe_character = html.escape(character)
            characters_html += f"<li>{safe_character}</li>"
        characters_html += "</ul>"

        dramatis_personae.content = f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>Dramatis Personae</title>
    <link rel="stylesheet" type="text/css" href="style/book.css" />
  </head>
  <body>
    <h2 class="section-title">Dramatis Personae</h2>
    {characters_html}
  </body>
</html>
"""
        book.add_item(dramatis_personae)

    # Define Table of Contents
    toc_items = [
        epub.Link("title.xhtml", "Title Page", "title"),
        epub.Link("story.xhtml", story.title, "story"),
    ]
    if dramatis_personae:
        toc_items.append(
            epub.Link("dramatis_personae.xhtml", "Dramatis Personae", "dramatis_personae")
        )

    book.toc = tuple(toc_items)

    # Add default NCX and Nav files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define reading order (spine) - use actual objects to avoid ID mismatch
    spine_items = ["nav", title_chapter, story_chapter]
    if dramatis_personae:
        spine_items.append(dramatis_personae)
    book.spine = spine_items

    # Write EPUB file
    output_file = Path(output_path)
    epub.write_epub(output_file, book)

    return output_file


def story_to_epub_cli(
    story: Story, output_filename: Optional[str] = None, author: str = "AI Generated"
) -> Path:
    """
    Convenience function for CLI usage - generates EPUB with sensible defaults.

    Args:
        story: Story object to convert
        output_filename: Optional custom filename (defaults to story title)
        author: Author name for metadata

    Returns:
        Path to the generated EPUB file
    """
    if output_filename is None:
        # Generate filename from story title
        safe_title = "".join(c if c.isalnum() or c in (" ", "_") else "" for c in story.title)
        safe_title = safe_title.replace(" ", "_").lower()
        output_filename = f"{safe_title}.epub"

    return generate_epub(story, output_filename, author)
