"""Notes CRUD — local flat-file storage with optional Supabase cloud backend."""

import os
import re
import datetime
import logging

log = logging.getLogger("hades.commands.notes")

NOTES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "notes.txt")


def _use_db(user_id) -> bool:
    if not user_id:
        return False
    try:
        import db
        return db.is_available()
    except ImportError:
        return False


def save_note(note: str, category: str = None, user_id: str = None):
    if _use_db(user_id):
        import db
        db.add_note(user_id, note, category)
        return
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    cat_str = f"[{category.lower()}] " if category else ""
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {cat_str}{note}\n")


def get_existing_categories(user_id: str = None) -> list:
    if _use_db(user_id):
        import db
        try:
            return db.get_note_categories(user_id)
        except Exception as e:
            log.warning("DB category fetch failed: %s", e)
    if not os.path.exists(NOTES_FILE):
        return ["personal", "work"]
    cats = set()
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            m = re.search(r"\]\s*\[([a-zA-Z]+)\]", line)
            if m:
                cats.add(m.group(1).lower())
    return sorted(cats) if cats else ["personal", "work"]


def read_notes(category: str = None, user_id: str = None) -> str:
    if _use_db(user_id):
        import db
        try:
            rows = db.get_notes(user_id, category)
            if not rows:
                return (f"No {category} notes found, Sir." if category
                        else "No notes found, Sir.")
            clean  = [r["content"] for r in rows]
            prefix = f"Your {category} notes: " if category else "Your notes: "
            return prefix + "; ".join(clean) + "."
        except Exception as e:
            log.warning("DB read_notes failed: %s", e)
    if not os.path.exists(NOTES_FILE):
        return "No notes found, Sir."
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        lines = [l.rstrip() for l in f if l.strip()]
    if not lines:
        return "Your notes are empty, Sir."
    if category:
        tag      = f"[{category.lower()}]"
        filtered = [l for l in lines if tag in l.lower()]
        if not filtered:
            return f"No notes found under '{category}', Sir."
        clean = []
        for l in filtered:
            l = re.sub(r"^\[[^\]]+\]\s*", "", l)
            l = re.sub(r"^\[[^\]]+\]\s*", "", l)
            clean.append(l.strip())
        return f"Your {category} notes: " + "; ".join(clean) + "."
    return "\n".join(lines)


def delete_last_note(user_id: str = None) -> str:
    if _use_db(user_id):
        import db
        try:
            deleted = db.delete_last_note_db(user_id)
            return ("Done, Sir. Your last note has been deleted."
                    if deleted else "No notes to delete, Sir.")
        except Exception as e:
            log.warning("DB delete_last_note failed: %s", e)
    if not os.path.exists(NOTES_FILE):
        return "No notes to delete, Sir."
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    if not lines:
        return "Your notes are already empty, Sir."
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines[:-1])
    return "Done, Sir. Your last note has been deleted."


def delete_notes(category: str = None, user_id: str = None) -> str:
    if _use_db(user_id):
        import db
        try:
            count = db.delete_notes_db(user_id, category)
            if count == 0:
                return (f"No notes found under '{category}', Sir." if category
                        else "No notes to delete, Sir.")
            return f"Deleted {count} note{'s' if count != 1 else ''}, Sir."
        except Exception as e:
            log.warning("DB delete_notes failed: %s", e)
    if not os.path.exists(NOTES_FILE):
        return "No notes to delete, Sir."
    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    if not lines:
        return "Your notes are already empty, Sir."
    if category:
        tag     = f"[{category.lower()}]"
        keep    = [l for l in lines if tag not in l.lower()]
        deleted = len(lines) - len(keep)
        if deleted == 0:
            return f"No notes found under '{category}', Sir."
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            f.writelines(keep)
        return f"Deleted {deleted} {category} note{'s' if deleted != 1 else ''}, Sir."
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        pass
    return f"All {len(lines)} note{'s' if len(lines) != 1 else ''} deleted, Sir."
