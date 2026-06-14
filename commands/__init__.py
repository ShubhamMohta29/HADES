"""Commands package — PC control, notes, and help card."""

from commands.system import handle_command
from commands.notes import (
    save_note,
    read_notes,
    delete_last_note,
    delete_notes,
    get_existing_categories,
)
from commands.help import HELP_HTML

__all__ = [
    "handle_command",
    "save_note",
    "read_notes",
    "delete_last_note",
    "delete_notes",
    "get_existing_categories",
    "HELP_HTML",
]
