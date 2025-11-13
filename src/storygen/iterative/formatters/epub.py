"""
EPUB formatting for iterative story generation pipeline.

Handles:
- Chapter decision logic (auto or manual)
- Intelligent chapter break placement
- Markdown to HTML conversion
- Scene break formatting
- Metadata and TOC generation
"""

import html
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from ebooklib import epub  # type: ignore

from storygen.iterative.generators.title import TitleGenerator
from storygen.iterative.models import Character, Location, SceneSequel, StoryIdea


@dataclass
class ChapterBreak:
    """Represents a chapter break decision."""

    scene_sequel_id: str
    chapter_number: int
    chapter_title: str | None
    reason: str  # Why this break was chosen


class ChapterDecider:
    """Decides where chapter breaks should occur."""

    def __init__(
        self,
        target_chapter_length: int = 3000,
        min_chapter_length: int = 1500,
        max_chapter_length: int = 5000,
    ):
        """
        Initialize chapter decider.

        Args:
            target_chapter_length: Target words per chapter
            min_chapter_length: Minimum words before considering break
            max_chapter_length: Maximum words before forcing break
        """
        self.target_chapter_length = target_chapter_length
        self.min_chapter_length = min_chapter_length
        self.max_chapter_length = max_chapter_length

    def decide_chapters(
        self,
        scene_sequels: list[SceneSequel],
        chapter_style: Literal["numbered", "titled", "sections", "none"] = "numbered",
        force_breaks: list[str] | None = None,
    ) -> list[ChapterBreak]:
        """
        Decide where chapter breaks should occur.

        Strategy:
        1. Check for manually-marked chapter breaks (chapter_start=True)
        2. If no manual breaks, apply automatic break logic:
           - Force break at max_chapter_length
           - Prefer breaks at:
             a) Act boundaries (source_act changes)
             b) Major time gaps (>12 hours)
             c) POV changes
             d) Location changes + sequel ending
           - Avoid breaking mid-scene-sequel pair

        Args:
            scene_sequels: List of scene-sequels with prose
            chapter_style: How to format chapters (numbered, titled, sections, none)
            force_breaks: Optional list of scene-sequel IDs to force breaks before

        Returns:
            List of ChapterBreak objects indicating where chapters start
        """
        if chapter_style == "none":
            return []

        force_breaks = force_breaks or []
        breaks: list[ChapterBreak] = []

        # Always start with chapter 1 at first scene
        breaks.append(
            ChapterBreak(
                scene_sequel_id=scene_sequels[0].id,
                chapter_number=1,
                chapter_title=self._generate_chapter_title(scene_sequels[0], chapter_style),
                reason="story_start",
            )
        )

        chapter_num = 2
        current_chapter_words = scene_sequels[0].actual_word_count or 0

        for i in range(1, len(scene_sequels)):
            ss = scene_sequels[i]
            prev_ss = scene_sequels[i - 1]
            ss_words = ss.actual_word_count or 0

            # Check for manual break
            if ss.chapter_start or ss.id in force_breaks:
                breaks.append(
                    ChapterBreak(
                        scene_sequel_id=ss.id,
                        chapter_number=chapter_num,
                        chapter_title=ss.chapter_title
                        or self._generate_chapter_title(ss, chapter_style),
                        reason="manual_break",
                    )
                )
                chapter_num += 1
                current_chapter_words = ss_words
                continue

            # Would adding this scene exceed max length?
            would_exceed_max = current_chapter_words + ss_words > self.max_chapter_length

            # Are we past minimum and near target?
            past_minimum = current_chapter_words >= self.min_chapter_length
            near_target = current_chapter_words >= self.target_chapter_length * 0.8

            # Calculate break score (higher = better break point)
            break_score = self._calculate_break_score(ss, prev_ss, scene_sequels)

            should_break = False
            reason = ""

            if would_exceed_max:
                should_break = True
                reason = f"max_length_exceeded ({current_chapter_words + ss_words} words)"
            elif past_minimum and break_score >= 8:
                should_break = True
                reason = f"strong_break_point (score: {break_score})"
            elif near_target and break_score >= 5:
                should_break = True
                reason = f"good_break_point (score: {break_score})"

            if should_break:
                breaks.append(
                    ChapterBreak(
                        scene_sequel_id=ss.id,
                        chapter_number=chapter_num,
                        chapter_title=self._generate_chapter_title(ss, chapter_style),
                        reason=reason,
                    )
                )
                chapter_num += 1
                current_chapter_words = ss_words
            else:
                current_chapter_words += ss_words

        return breaks

    def _calculate_break_score(
        self,
        ss: SceneSequel,
        prev_ss: SceneSequel,
        all_scenes: list[SceneSequel],
    ) -> int:
        """
        Calculate break score for scene-sequel (0-10, higher = better break point).

        Scoring factors:
        - Act boundary: +5
        - Sequel ending (natural pause): +3
        - Major time gap (>12h): +4
        - POV change: +3
        - Location change: +2
        - Day change: +2
        - End of major story beat: +3
        """
        score = 0

        # Act boundary (major structural break)
        if ss.source_act != prev_ss.source_act:
            score += 5

        # Sequel ending (natural reflection/pause point)
        if prev_ss.type == "sequel":
            score += 3

        # Major time gap
        time_gap = abs(ss.start_hours - prev_ss.end_hours)
        if time_gap > 12:
            score += 4
        elif time_gap > 6:
            score += 2

        # POV change (reader mental reset)
        if ss.pov_character != prev_ss.pov_character:
            score += 3

        # Location change (scene transition)
        if ss.location != prev_ss.location:
            score += 2

        # Day change (natural break)
        if ss.day_number != prev_ss.day_number:
            score += 2

        return score

    def _generate_chapter_title(
        self,
        ss: SceneSequel,
        chapter_style: Literal["numbered", "titled", "sections", "none"],
    ) -> str | None:
        """Generate chapter title based on style."""
        if chapter_style == "numbered":
            return None  # Just use "Chapter N"
        elif chapter_style == "titled":
            # Generate title from scene content or act
            if ss.source_act:
                # Clean up act name for title
                title = ss.source_act.replace("_", " ").title()
                # Remove common prefixes
                title = re.sub(r"^(Act \d+|Part \d+)[\s:-]+", "", title)
                return title
            return None
        elif chapter_style == "sections":
            return None  # Use section markers (*, #, etc.) instead
        return None


class MarkdownConverter:
    """Converts markdown to HTML for EPUB."""

    @staticmethod
    def convert(text: str) -> str:
        """
        Convert markdown to HTML.

        Handles:
        - **bold** → <strong>
        - *italic* → <em>
        - ***bold italic*** → <strong><em>
        - Line breaks → <br/>

        Args:
            text: Markdown text (should be HTML-escaped first)

        Returns:
            HTML text
        """
        # Bold + italic first (longest pattern)
        text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
        text = re.sub(r"___(.+?)___", r"<strong><em>\1</em></strong>", text)

        # Bold
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)

        # Italic
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        text = re.sub(r"_(.+?)_", r"<em>\1</em>", text)

        return text


class EpubFormatter:
    """Formats iterative story into EPUB."""

    def __init__(
        self,
        author: str = "AI Generated",
        chapter_style: Literal["numbered", "titled", "sections", "none"] = "numbered",
        target_chapter_length: int = 3000,
        model: str = "gpt-4",
        verbose: bool = False,
    ):
        """
        Initialize EPUB formatter.

        Args:
            author: Author name for metadata
            chapter_style: How to format chapters
            target_chapter_length: Target words per chapter
            model: AI model for title generation
            verbose: Print detailed progress
        """
        self.author = author
        self.chapter_style = chapter_style
        self.target_chapter_length = target_chapter_length
        self.model = model
        self.verbose = verbose

        self.chapter_decider = ChapterDecider(target_chapter_length=target_chapter_length)
        self.markdown_converter = MarkdownConverter()
        self.title_generator = TitleGenerator(model=model, verbose=verbose)

    def format(
        self,
        story_idea: StoryIdea,
        characters: list[Character],
        locations: list[Location],
        scene_sequels: list[SceneSequel],
        output_path: str,
        title_override: str | None = None,
        force_chapter_breaks: list[str] | None = None,
    ) -> Path:
        """
        Generate EPUB from story components.

        Args:
            story_idea: Story idea with title, themes, etc.
            characters: List of characters
            locations: List of locations
            scene_sequels: List of scene-sequels with prose
            output_path: Output file path
            title_override: Override story title
            force_chapter_breaks: Scene-sequel IDs to force chapter breaks before

        Returns:
            Path to generated EPUB file
        """
        if self.verbose:
            print(f"📖 Formatting EPUB with {len(scene_sequels)} scene-sequels...")

        # Decide chapter breaks
        chapter_breaks = self.chapter_decider.decide_chapters(
            scene_sequels,
            chapter_style=self.chapter_style,  # type: ignore
            force_breaks=force_chapter_breaks,
        )

        if self.verbose:
            print(f"📚 Decided on {len(chapter_breaks)} chapters")
            for brk in chapter_breaks:
                print(f"   Ch {brk.chapter_number}: {brk.scene_sequel_id} ({brk.reason})")

        # Create EPUB book
        book = epub.EpubBook()

        # Metadata - generate title if not provided
        if title_override:
            title = title_override
        else:
            if self.verbose:
                print("📝 Generating title with AI (analyzing complete story)...")
            title = self.title_generator.generate(
                raw_idea=story_idea.raw_idea,
                one_sentence=story_idea.one_sentence,
                genres=story_idea.genres,
                themes=story_idea.themes,
                tone=story_idea.tone,
                scene_sequels=scene_sequels,
            )
            if self.verbose:
                print(f"✨ Generated title: {title}")

        book.set_identifier(f"story_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        book.set_title(title)
        book.set_language("en")
        book.add_author(self.author)

        for genre in story_idea.genres:
            book.add_metadata("DC", "subject", genre)
        if story_idea.expanded:
            book.add_metadata("DC", "description", story_idea.expanded[:500])

        # CSS
        style_css = self._get_css()
        style_item = epub.EpubItem(
            uid="style_book",
            file_name="style/book.css",
            media_type="text/css",
            content=style_css,
        )
        book.add_item(style_item)

        # Title page
        title_page = self._create_title_page(book, title, story_idea, style_item)
        book.add_item(title_page)

        # Group scene-sequels by chapter
        chapter_groups = self._group_by_chapters(scene_sequels, chapter_breaks)

        # Generate chapter HTML files
        chapter_items = []
        for chapter_num, chapter_scenes in chapter_groups.items():
            chapter_break = next(b for b in chapter_breaks if b.chapter_number == chapter_num)
            chapter_item = self._create_chapter(
                book, chapter_num, chapter_break.chapter_title, chapter_scenes, style_item
            )
            book.add_item(chapter_item)
            chapter_items.append(chapter_item)

        # Dramatis Personae
        dramatis_personae = self._create_dramatis_personae(book, characters, style_item)
        if dramatis_personae:
            book.add_item(dramatis_personae)

        # Table of Contents
        toc_items = [epub.Link("title.xhtml", "Title Page", "title")]
        for i, chapter_item in enumerate(chapter_items, 1):
            chapter_break = chapter_breaks[i - 1]
            label = (
                f"Chapter {i}: {chapter_break.chapter_title}"
                if chapter_break.chapter_title
                else f"Chapter {i}"
            )
            toc_items.append(epub.Link(chapter_item.file_name, label, f"chapter_{i}"))
        if dramatis_personae:
            toc_items.append(
                epub.Link(
                    "dramatis_personae.xhtml",
                    "Dramatis Personae",
                    "dramatis_personae",
                )
            )
        book.toc = tuple(toc_items)  # type: ignore

        # Navigation
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Spine
        spine: list = ["nav", title_page] + chapter_items
        if dramatis_personae:
            spine.append(dramatis_personae)
        book.spine = spine

        # Write file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        epub.write_epub(output_file, book)

        if self.verbose:
            print(f"✅ EPUB saved to: {output_file}")

        return output_file

    def _group_by_chapters(
        self,
        scene_sequels: list[SceneSequel],
        chapter_breaks: list[ChapterBreak],
    ) -> dict[int, list[SceneSequel]]:
        """Group scene-sequels by chapter number."""
        groups: dict[int, list[SceneSequel]] = {}

        # Create break lookup
        break_map = {b.scene_sequel_id: b.chapter_number for b in chapter_breaks}

        current_chapter = 1
        for ss in scene_sequels:
            # Check if this scene starts a new chapter
            if ss.id in break_map:
                current_chapter = break_map[ss.id]

            if current_chapter not in groups:
                groups[current_chapter] = []
            groups[current_chapter].append(ss)

        return groups

    def _create_title_page(
        self,
        book: epub.EpubBook,
        title: str,
        story_idea: StoryIdea,
        style_item: epub.EpubItem,
    ) -> epub.EpubHtml:
        """Create title page."""
        safe_title = html.escape(title)
        safe_author = html.escape(self.author)
        safe_genres = html.escape(", ".join(story_idea.genres)) if story_idea.genres else ""
        safe_summary = html.escape(story_idea.expanded[:300]) if story_idea.expanded else ""

        title_page = epub.EpubHtml(
            title="Title Page",
            file_name="title.xhtml",
            lang="en",
        )
        title_page.content = f"""<div class="title-page">
  <h1 class="book-title">{safe_title}</h1>
  <div class="author">by {safe_author}</div>
  {f'<div class="meta">{safe_genres}</div>' if safe_genres else ''}
  {f'<div class="summary">{safe_summary}</div>' if safe_summary else ''}
</div>
"""
        title_page.add_item(style_item)
        return title_page

    def _create_chapter(
        self,
        book: epub.EpubBook,
        chapter_num: int,
        chapter_title: str | None,
        scene_sequels: list[SceneSequel],
        style_item: epub.EpubItem,
    ) -> epub.EpubHtml:
        """Create chapter HTML."""
        chapter_label = (
            f"Chapter {chapter_num}: {chapter_title}" if chapter_title else f"Chapter {chapter_num}"
        )

        chapter = epub.EpubHtml(
            title=chapter_label,
            file_name=f"chapter_{chapter_num}.xhtml",
            lang="en",
        )

        # Chapter heading
        parts = [f'<h2 class="chapter-title">{html.escape(chapter_label)}</h2>']

        # Scene-sequels
        at_chapter_start = True
        for i, ss in enumerate(scene_sequels):
            # Scene break logic
            if i > 0:
                prev_ss = scene_sequels[i - 1]
                needs_break = self._needs_scene_break(ss, prev_ss)

                if needs_break == "major":
                    parts.append('<p class="scene-break">— • —</p>')
                    at_chapter_start = True
                elif needs_break == "minor":
                    parts.append('<p class="scene-break">&#160;</p>')
                    at_chapter_start = True

            # Convert prose
            if ss.content:
                prose_html = self._convert_prose(ss.content, at_chapter_start)
                parts.append(prose_html)
                at_chapter_start = False

        chapter.content = "\n".join(parts)
        chapter.add_item(style_item)
        return chapter

    def _needs_scene_break(
        self,
        ss: SceneSequel,
        prev_ss: SceneSequel,
    ) -> Literal["major", "minor", "none"]:
        """Determine if scene break is needed."""
        # Major break (ornamental separator)
        if ss.pov_character != prev_ss.pov_character:
            return "major"

        # Minor break (blank line)
        time_gap = abs(ss.start_hours - prev_ss.end_hours)
        if time_gap > 2.0 or ss.location != prev_ss.location:
            return "minor"

        return "none"

    def _convert_prose(self, content: str, at_chapter_start: bool) -> str:
        """Convert markdown prose to HTML paragraphs."""
        parts = []
        blocks = [b.strip() for b in content.split("\n\n") if b.strip()]

        for i, block in enumerate(blocks):
            # HTML escape first
            safe_block = html.escape(block)

            # Convert markdown
            formatted = self.markdown_converter.convert(safe_block)

            # First paragraph after chapter start has no indent
            first_para = at_chapter_start and i == 0
            css_class = "no-indent" if first_para else ""
            class_attr = f' class="{css_class}"' if css_class else ""

            parts.append(f"<p{class_attr}>{formatted}</p>")

        return "\n".join(parts)

    def _create_dramatis_personae(
        self,
        book: epub.EpubBook,
        characters: list[Character],
        style_item: epub.EpubItem,
    ) -> epub.EpubHtml | None:
        """Create dramatis personae page."""
        if not characters:
            return None

        dramatis = epub.EpubHtml(
            title="Dramatis Personae",
            file_name="dramatis_personae.xhtml",
            lang="en",
        )

        items = []
        for char in characters:
            name = html.escape(char.name)
            role = html.escape(char.role.title()) if char.role else ""
            bio = (
                html.escape(char.bio[:100] + "...")
                if len(char.bio) > 100
                else html.escape(char.bio)
            )

            items.append(f"<li><strong>{name}</strong> ({role})<br/><em>{bio}</em></li>")

        dramatis.content = f"""<h2 class="section-title">Dramatis Personae</h2>
<ul class="character-list">
  {"".join(items)}
</ul>
"""
        dramatis.add_item(style_item)
        return dramatis

    def _get_css(self) -> str:
        """Get CSS stylesheet."""
        return """
    body {
        font-family: Georgia, "Times New Roman", serif;
        line-height: 1.6;
        padding: 2em;
        margin: 0;
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
    h2.chapter-title {
        font-size: 1.6em;
        margin-top: 2em;
        margin-bottom: 1.5em;
        text-align: center;
        page-break-before: always;
    }
    /* Universal paragraph indentation */
    p {
        text-align: justify;
        margin: 0 0 1em 0;
        text-indent: 1.5em;
    }
    /* Never indent first paragraph after headings */
    h1 + p,
    h2 + p,
    h3 + p {
        text-indent: 0 !important;
    }
    /* Explicit no-indent class */
    p.no-indent {
        text-indent: 0 !important;
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
    /* Scene breaks with consistent spacing */
    .scene-break {
        text-indent: 0 !important;
        text-align: center;
        margin: 2em 0;
        font-size: 1.1em;
    }
    ul.character-list {
        margin-left: 1.5em;
        margin-bottom: 1em;
        list-style-type: none;
    }
    ul.character-list li {
        margin-bottom: 1em;
    }
    """
