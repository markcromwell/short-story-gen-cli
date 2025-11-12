"""
Main CLI entry point for iterative story generation.
"""

import logging

import click
from dotenv import load_dotenv

# Import command modules
from storygen.iterative.cli.commands import export, generate, project, prose

# Load environment variables (for API keys)
load_dotenv()


@click.group()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging (DEBUG level)",
    is_eager=True,
)
@click.pass_context
def cli(ctx, verbose: bool):
    """Iterative story generation using Scene-Sequel structure.

    Generate complete stories through a multi-stage pipeline:
    1. Create project and generate story idea
    2. Generate characters and locations
    3. Create structured outline
    4. Break down into scene-sequels
    5. Generate prose with markdown formatting
    6. Export to polished EPUB

    Each stage builds on the previous, allowing review and iteration.
    """
    # Configure logging based on verbose flag
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Store verbose in context for commands that need it
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


# Register project management commands
cli.add_command(project.new)
cli.add_command(project.list_projects_cmd, name="projects")
cli.add_command(project.status)

# Register generation commands
cli.add_command(generate.idea)
cli.add_command(generate.characters)
cli.add_command(generate.locations)
cli.add_command(generate.outline)

# Register prose commands
cli.add_command(prose.breakdown)
cli.add_command(prose.prose)

# Register export commands
cli.add_command(export.epub)


if __name__ == "__main__":
    cli()
