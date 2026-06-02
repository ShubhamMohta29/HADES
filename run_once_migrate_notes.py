"""One-time migration: import notes.txt into the Supabase notes table.

Run after setting up Supabase and signing in for the first time:

    python run_once_migrate_notes.py

The script reads your local notes.txt, preserves timestamps and category tags,
inserts every note into the Supabase `notes` table, then renames notes.txt to
notes.txt.bak so it is no longer read by the app.

Safe to re-run: it checks for notes.txt before doing anything.
"""

import re
import sys
import os
from dotenv import load_dotenv

load_dotenv()

from config import SUPABASE_URL, SUPABASE_ANON_KEY

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env.")
    sys.exit(1)

NOTES_FILE = os.path.join(os.path.dirname(__file__), "notes.txt")

if not os.path.exists(NOTES_FILE):
    print("notes.txt not found — nothing to migrate.")
    sys.exit(0)

print("\nHADES — notes.txt → Supabase Migration")
print("=" * 42)

# Ask for user_id (from Supabase dashboard → Auth → Users)
print("\nYou need your Supabase user UUID.")
print("Find it at: Supabase dashboard → Authentication → Users → copy the UUID.")
user_id = input("\nYour user UUID: ").strip()
if not user_id:
    print("No user ID entered. Aborting.")
    sys.exit(1)

from supabase import create_client
client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

with open(NOTES_FILE, "r", encoding="utf-8") as f:
    lines = [l.strip() for l in f if l.strip()]

if not lines:
    print("notes.txt is empty — nothing to migrate.")
    sys.exit(0)

print(f"\nFound {len(lines)} note(s). Migrating...")

migrated = 0
skipped  = 0

for line in lines:
    # Format: [YYYY-MM-DD HH:MM] [category?] content
    m = re.match(r"\[(.+?)\]\s*(?:\[([a-zA-Z]+)\]\s*)?(.+)", line)
    if not m:
        print(f"  SKIP  (unrecognized format): {line[:60]}")
        skipped += 1
        continue

    timestamp, category, content = m.groups()
    content = content.strip()

    try:
        client.table("notes").insert({
            "user_id":    user_id,
            "content":    content,
            "category":   category,
            "created_at": timestamp,
        }).execute()
        cat_str = f"[{category}] " if category else ""
        print(f"  OK    {cat_str}{content[:55]}")
        migrated += 1
    except Exception as e:
        print(f"  FAIL  {content[:50]} — {e}")
        skipped += 1

print(f"\nMigrated: {migrated}  |  Skipped: {skipped}")

if migrated > 0:
    bak = NOTES_FILE + ".bak"
    os.rename(NOTES_FILE, bak)
    print(f"\nnotes.txt renamed to notes.txt.bak")
    print("The app will now read notes from Supabase.")
else:
    print("\nNo rows were inserted. notes.txt left unchanged.")
