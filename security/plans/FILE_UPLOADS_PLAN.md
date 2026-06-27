# FILE_UPLOADS Fix Plan

## Changes

- `face_auth.py` — Replace `import pickle` + `pickle.dump/load` with `import json` + `json.dump/load`. Change `ENCODINGS_FILE` to `face_encodings.json`. Convert numpy arrays to lists on write (`enc.tolist()`); convert back on read (`numpy.array(e)` per element).
- `.gitignore` — Add `face_encodings.json` to replace the `face_encodings.pkl` entry.

## New files

None. Existing `face_encodings.pkl` will be superseded by `face_encodings.json` on next registration.

## Verification goals

- [ ] `import pickle` no longer appears in `face_auth.py`
- [ ] `face_encodings.json` is written after a registration session and is valid JSON
- [ ] `face_encodings.pkl` is no longer created by the application
- [ ] `face_encodings.json` added to `.gitignore`; `face_encodings.pkl` entry kept (for existing installs)
- [ ] `verify_face()` correctly loads encodings from the JSON file and matches a known face
- [ ] Supabase load path (`db.load_face_encodings`) still works as primary; JSON file is fallback

## Manual verification (for the human)

- Delete `face_encodings.pkl` and `face_encodings.json`, run HADES with `FACE_AUTH_ENABLED=true` → registration fires automatically → confirm `face_encodings.json` is created (not `.pkl`)
- Restart HADES → confirm face verification succeeds using the JSON file
