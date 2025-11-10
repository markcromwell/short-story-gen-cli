"""
EPUB generation from Story models.
"""

import html
from datetime import datetime
from pathlib import Path

from ebooklib import epub  # type: ignore

from storygen.models import Story


def convert_markdown_to_html(text: str) -> str:
    """
    Convert basic markdown formatting to HTML for EPUB.

    Handles:
    - **bold** or __bold__ → <strong>bold</strong>
    - *italic* or _italic_ → <em>italic</em>
    - ***bold italic*** → <strong><em>bold italic</em></strong>

    Args:
        text: Text with markdown formatting (already HTML-escaped)

    Returns:
        Text with HTML formatting
    """
    import re

    # Bold + italic first
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    text = re.sub(r"___(.+?)___", r"<strong><em>\1</em></strong>", text)

    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)

    # Italic
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"_(.+?)_", r"<em>\1</em>", text)

    return text


def generate_epub(story: Story, output_path: str, author: str = "AI Generated") -> Path:
    """
    Generate an EPUB file from a Story object with clean structure & metadata.
    """
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

    # Shared CSS
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
    title_chapter.content = f"""<div class="title-page">
  <h1 class="book-title">{safe_title}</h1>
  <div class="author">by {safe_author}</div>
  {f'<div class="meta">{safe_genre}</div>' if safe_genre else ''}
  {f'<div class="summary">{safe_summary}</div>' if safe_summary else ''}
</div>
"""
    book.add_item(title_chapter)

    # Story content
    story_chapter = epub.EpubHtml(
        title=story.title,
        file_name="story.xhtml",
        lang="en",
    )

    story_parts: list[str] = []
    at_scene_start = True

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
                story_parts.append('<p class="scene-break">— • —</p>')
                at_scene_start = True
            elif time_gap or location_changed:
                story_parts.append('<p class="scene-break">&#160;</p>')
                at_scene_start = True
            else:
                at_scene_start = True

        raw_content = scene.content or ""
        blocks = [b.strip() for b in raw_content.split("\n\n") if b.strip()]

        for j, block in enumerate(blocks):
            safe_block = html.escape(block)
            formatted = convert_markdown_to_html(safe_block)

            first_para = at_scene_start and j == 0
            css_class = "no-indent" if first_para else ""
            class_attr = f' class="{css_class}"' if css_class else ""

            story_parts.append(f"<p{class_attr}>{formatted}</p>")

        at_scene_start = False

    story_chapter.content = "".join(story_parts)
    book.add_item(story_chapter)

    # Dramatis Personae
    dramatis_personae = None
    characters = story.get_characters()
    if characters:
        dramatis_personae = epub.EpubHtml(
            title="Dramatis Personae",
            file_name="dramatis_personae.xhtml",
            lang="en",
        )

        items = "".join(f"<li>{html.escape(name)}</li>" for name in characters)

        dramatis_personae.content = f"""<h2 class="section-title">Dramatis Personae</h2>
<ul>
  {items}
</ul>
"""
        book.add_item(dramatis_personae)

    # TOC
    toc_items = [
        epub.Link("title.xhtml", "Title Page", "title"),
        epub.Link("story.xhtml", story.title, "story"),
    ]
    if dramatis_personae:
        toc_items.append(
            epub.Link(
                "dramatis_personae.xhtml",
                "Dramatis Personae",
                "dramatis_personae",
            )
        )
    book.toc = tuple(toc_items)

    # NCX / Nav
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Spine
    spine: list = ["nav", title_chapter, story_chapter]
    if dramatis_personae:
        spine.append(dramatis_personae)
    book.spine = spine

    output_file = Path(output_path)
    epub.write_epub(output_file, book)
    return output_file


def story_to_epub_cli(
    story: Story,
    output_filename: str | None = None,
    author: str = "AI Generated",
) -> Path:
    if output_filename is None:
        safe_title = "".join(c if c.isalnum() or c in (" ", "_") else "" for c in story.title)
        safe_title = safe_title.replace(" ", "_").lower()
        output_filename = f"{safe_title}.epub"
    return generate_epub(story, output_filename, author)
