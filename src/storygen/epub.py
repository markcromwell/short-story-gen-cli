"""
EPUB generation from Story models.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from ebooklib import epub  # type: ignore

from storygen.models import Story


def generate_epub(story: Story, output_path: str, author: str = "AI Generated") -> Path:
    """
    Generate an EPUB file from a Story object.

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

    # Set metadata
    book.set_identifier(f"story_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    book.set_title(story.title)
    book.set_language("en")
    book.add_author(author)

    if story.genre:
        book.add_metadata("DC", "subject", story.genre)

    # Create title page
    title_chapter = epub.EpubHtml(
        title="Title Page",
        file_name="title.xhtml",
        lang="en",
    )

    title_content = f"""
    <html>
    <head><title>{story.title}</title></head>
    <body>
        <h1 style="text-align: center; margin-top: 100px;">{story.title}</h1>
        <p style="text-align: center; font-style: italic;">{author}</p>
        {f'<p style="text-align: center; margin-top: 20px;"><strong>Genre:</strong> {story.genre}</p>' if story.genre else ''}
        {f'<p style="text-align: center; font-style: italic; margin-top: 20px;">{story.summary}</p>' if story.summary else ''}
    </body>
    </html>
    """
    title_chapter.content = title_content
    book.add_item(title_chapter)

    # Create chapters for each scene
    chapters = []
    for scene in story.scenes:
        chapter = epub.EpubHtml(
            title=f"Scene {scene.number}: {scene.title}",
            file_name=f"scene_{scene.number}.xhtml",
            lang="en",
        )

        # Build chapter content
        chapter_content = f"<h2>Scene {scene.number}: {scene.title}</h2>"

        if scene.setting:
            chapter_content += f'<p style="font-style: italic; color: #666;"><strong>Setting:</strong> {scene.setting}</p>'

        if scene.characters:
            characters_list = ", ".join(scene.characters)
            chapter_content += f'<p style="font-style: italic; color: #666;"><strong>Characters:</strong> {characters_list}</p>'

        # Convert newlines to paragraphs
        paragraphs = scene.content.split("\n\n")
        for para in paragraphs:
            if para.strip():
                chapter_content += f"<p>{para.strip()}</p>"

        chapter.content = chapter_content
        book.add_item(chapter)
        chapters.append(chapter)

    # Define Table of Contents
    book.toc = (
        epub.Link("title.xhtml", "Title Page", "title"),
        *[
            epub.Link(f"scene_{i+1}.xhtml", f"Scene {i+1}: {scene.title}", f"scene_{i+1}")
            for i, scene in enumerate(story.scenes)
        ],
    )

    # Add default NCX and Nav files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Basic CSS styling
    style = """
    body {
        font-family: Georgia, serif;
        line-height: 1.6;
        margin: 2em;
    }
    h1 {
        font-size: 2em;
        margin-bottom: 0.5em;
    }
    h2 {
        font-size: 1.5em;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
        border-bottom: 2px solid #333;
        padding-bottom: 0.3em;
    }
    p {
        text-align: justify;
        margin-bottom: 1em;
    }
    """

    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style,
    )
    book.add_item(nav_css)

    # Define reading order (spine)
    book.spine = ["title", *chapters, "nav"]

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
