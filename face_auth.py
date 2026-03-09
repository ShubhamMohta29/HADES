"""
Face recognition security layer.
Setup:
  pip install opencv-python face_recognition cmake dlib

To register your face, run this file directly:
  python face_auth.py --register
"""
import os
import sys
import pickle

ENCODINGS_FILE = os.path.join(os.path.dirname(__file__), "face_encodings.pkl")

try:
    import cv2
    import face_recognition
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False

def register_face():
    if not CV_AVAILABLE:
        print("face_recognition not installed. Run: pip install face_recognition opencv-python")
        return False

    print("Looking at camera to register your face... Look straight at the camera.")
    cap = cv2.VideoCapture(0)
    encodings = []

    for _ in range(30):  # capture 30 frames for reliability
        ret, frame = cap.read()
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
        with open(ENCODINGS_FILE, "wb") as f:
            pickle.dump(encodings, f)
        print(f"Face registered successfully with {len(encodings)} samples.")
        return True
    print("No face detected. Try again.")
    return False

def verify_face(timeout=10):
    """Returns True if the registered face is detected within timeout seconds."""
    if not CV_AVAILABLE:
        return True  # skip if not installed

    if not os.path.exists(ENCODINGS_FILE):
        print("No registered face found. Run: python face_auth.py --register")
        return True  # don't block if not set up

    with open(ENCODINGS_FILE, "rb") as f:
        known_encodings = pickle.load(f)

    cap = cv2.VideoCapture(0)
    import time
    start = time.time()

    while time.time() - start < timeout:
        ret, frame = cap.read()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb)
        face_encodings = face_recognition.face_encodings(rgb, face_locations)

        for encoding in face_encodings:
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
    if "--register" in sys.argv:
        register_face()
    else:
        result = verify_face()
        print("Access granted." if result else "Access denied.")