"""
Face recognition security layer.
Setup:
  pip install opencv-python face_recognition cmake dlib

Encodings are stored in Supabase (primary) and face_encodings.pkl (local cache).
Registration happens automatically on first run when no encodings are found.
"""
import os
import pickle
import logging

ENCODINGS_FILE = os.path.join(os.path.dirname(__file__), "face_encodings.pkl")
log = logging.getLogger("hades.face_auth")

try:
    import cv2
    import face_recognition
    CV_AVAILABLE = True
except (ImportError, Exception):
    CV_AVAILABLE = False


def _load_encodings(user_id=None):
    """Load encodings from Supabase (if user_id given) then fall back to local file."""
    import numpy as np
    if user_id:
        try:
            import db
            if db.is_available():
                data = db.load_face_encodings(user_id)
                if data:
                    return [np.array(e) for e in data]
        except Exception as e:
            log.warning("Could not load face encodings from Supabase: %s", e)
    if os.path.exists(ENCODINGS_FILE):
        with open(ENCODINGS_FILE, "rb") as f:
            return pickle.load(f)
    return None


def _save_encodings(encodings, user_id=None):
    """Persist encodings to local file and Supabase."""
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(encodings, f)
    if user_id:
        try:
            import db
            if db.is_available():
                db.save_face_encodings(user_id, [e.tolist() for e in encodings])
                log.info("Face encodings synced to Supabase for user %s.", user_id)
        except Exception as e:
            log.warning("Could not save face encodings to Supabase: %s", e)


def register_face(user_id=None):
    """Capture frames from the webcam and save encodings locally + to Supabase."""
    if not CV_AVAILABLE:
        print("face_recognition not installed. Run: pip install face_recognition opencv-python")
        return False

    print("Looking at camera to register your face... Look straight at the camera.")
    cap = cv2.VideoCapture(0)
    encodings = []

    for _ in range(30):
        ret, frame = cap.read()
        if not ret:
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        found = face_recognition.face_encodings(rgb)
        if found:
            encodings.append(found[0])
        cv2.imshow("Registering Face - Press Q to stop", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if encodings:
        _save_encodings(encodings, user_id)
        print(f"Face registered successfully with {len(encodings)} samples.")
        return True
    print("No face detected. Try again.")
    return False


def verify_face(user_id=None, timeout=10):
    """Return True if the registered face is detected within timeout seconds.

    On first run (no stored encodings), registration is triggered automatically.
    """
    if not CV_AVAILABLE:
        return True

    known_encodings = _load_encodings(user_id)

    if not known_encodings:
        print("No registered face found. Starting automatic registration...")
        if not register_face(user_id):
            return False
        known_encodings = _load_encodings(user_id)
        if not known_encodings:
            return False

    import time
    cap = cv2.VideoCapture(0)
    start = time.time()

    while time.time() - start < timeout:
        ret, frame = cap.read()
        if not ret:
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb)
        face_enc_list = face_recognition.face_encodings(rgb, face_locations)

        for encoding in face_enc_list:
            matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)
            if any(matches):
                cap.release()
                cv2.destroyAllWindows()
                return True

        cv2.imshow("HADES - Face Verification", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return False


if __name__ == "__main__":
    import sys
    if "--register" in sys.argv:
        register_face()
    else:
        result = verify_face()
        print("Access granted." if result else "Access denied.")
