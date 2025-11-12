"""
Data models for iterative story generation.

All models support JSON serialization via to_dict() and from_dict() methods.

This module re-exports all models from domain-specific submodules for backward compatibility.
"""

# Story models
# Character models
from .characters import Character

# Feedback models
from .feedback import EditorialFeedback

# Location models
from .locations import Location

# Project models
from .project import Project, ProjectConfig, WorkingDoc
from .story import StoryConfig, StoryIdea, WorldBuilding

# Structure models
from .structure import Act, ActStructure, Outline, OutlineLegacy, SceneSequel

__all__ = [
    # Story
    "StoryConfig",
    "StoryIdea",
    "WorldBuilding",
    # Characters
    "Character",
    # Locations
    "Location",
    # Structure
    "Act",
    "ActStructure",
    "Outline",
    "OutlineLegacy",
    "SceneSequel",
    # Feedback
    "EditorialFeedback",
    # Project
    "Project",
    "ProjectConfig",
    "WorkingDoc",
]
