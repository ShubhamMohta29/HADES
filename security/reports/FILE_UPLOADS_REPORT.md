# FILE_UPLOADS Security Report

## Status: MEDIUM

## Findings

HADES has no HTTP file upload endpoints. However, it uses Python's `pickle` module to serialize and deserialize face recognition encodings to/from a local file, which violates the project's CLAUDE.md security rule:

> "NEVER use `pickle.loads`, `pickle.load`, or any deserialization on user-supplied data. Use JSON for all network data exchange."

### Vulnerable code — `face_auth.py`

```python
# Writing
with open(ENCODINGS_FILE, "wb") as f:
    pickle.dump(encodings, f)

# Reading
with open(ENCODINGS_FILE, "rb") as f:
    return pickle.load(f)
```

`pickle.load()` on a maliciously crafted `.pkl` file executes arbitrary Python code during deserialization. If an attacker can write to `face_encodings.pkl` (e.g., via another vulnerability, shared machine, or physical access), they can achieve code execution the next time HADES starts with `FACE_AUTH_ENABLED=true`.

The risk is local (requires write access to the file), not remote, but the rule exists precisely to eliminate this class of vulnerability regardless of context.

**Note:** Face encodings are now also stored in Supabase as JSON (`db.save_face_encodings` / `db.load_face_encodings`). The Supabase path is already safe. Only the local cache file uses pickle.

### Safe path — Supabase storage

```python
# db.py — already JSON-safe
db.save_face_encodings(user_id, [e.tolist() for e in encodings])  # numpy → list → jsonb
data = db.load_face_encodings(user_id)                            # jsonb → list
```
JSON via Supabase is safe. ✅

## What's at risk

An attacker with write access to `face_encodings.pkl` can inject a malicious pickle payload that executes arbitrary code when HADES loads the file at startup.

## What's already secure

- Supabase storage path uses JSON, not pickle
- File is gitignored (not committed to version control)
- The file is only written by the local application after a face registration session

## Recommendations

1. **(MEDIUM — fix)** Replace `pickle.dump` / `pickle.load` in `face_auth.py` with `json.dump` / `json.load`, converting numpy arrays to/from Python lists. The local cache format becomes a JSON file (`face_encodings.json`).
