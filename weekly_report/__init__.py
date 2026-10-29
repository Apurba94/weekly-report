"""Compile git activity and notes from several repositories into a weekly progress report."""
from .core import git_log, parse_log, week_range, notes_in_range, render

__version__ = "0.1.0"
__all__ = ["git_log", "parse_log", "week_range", "notes_in_range", "render"]
