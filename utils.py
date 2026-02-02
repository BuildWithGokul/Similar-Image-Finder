import os
import pickle
import numpy as np
import cv2
from deepface import DeepFace
import config as cfg


def ensure_folder(path: str):
    os.makedirs(path, exist_ok=True)


def allowed_file(filename: str):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in cfg.ALLOWED_EXTENSIONS


def save_db(data: dict):
    ensure_folder(os.path.dirname(cfg.DB_PATH))
    with open(cfg.DB_PATH, "wb") as f:
        pickle.dump(data, f)


def load_db():
    if not os.path.exists(cfg.DB_PATH):
        return {"embeddings": [], "filenames": []}
    with open(cfg.DB_PATH, "rb") as f:
        return pickle.load(f)


def cosine_similarity(a: np.ndarray, b: np.ndarray):
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)

    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0

    return float(np.dot(a, b) / denom)


# ✅ ULTRA: detect face & take biggest one only
def extract_main_face(img_path: str):
    """
    Returns cropped face image (numpy) or None.
    Picks biggest face if multiple faces exist.
    """
    try:
        faces = DeepFace.extract_faces(
            img_path=img_path,
            detector_backend=cfg.DETECTOR_BACKEND,
            enforce_detection=cfg.ENFORCE_DETECTION,
            align=True,
        )

        if not faces:
            return None

        # pick biggest face by area
        best = None
        best_area = 0

        for f in faces:
            fa = f.get("facial_area", {})
            w = fa.get("w", 0)
            h = fa.get("h", 0)
            area = w * h
            if area > best_area:
                best_area = area
                best = f

        if best is None:
            return None

        face_img = best.get("face", None)
        if face_img is None:
            return None

        # face_img is RGB float [0..1] sometimes -> convert to uint8 BGR safely
        if face_img.max() <= 1.0:
            face_img = (face_img * 255).astype(np.uint8)
        else:
            face_img = face_img.astype(np.uint8)

        # DeepFace gives RGB -> convert to BGR for OpenCV safe
        face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)

        return face_img

    except Exception:
        return None


def compute_embedding_from_face(face_bgr):
    """
    Compute embedding from already cropped face image (BGR).
    """
    try:
        reps = DeepFace.represent(
            img_path=face_bgr,
            model_name=cfg.MODEL_NAME,
            detector_backend="skip",  # ✅ important: we already extracted face
            enforce_detection=False,
        )

        if not reps or "embedding" not in reps[0]:
            return None

        emb = np.array(reps[0]["embedding"], dtype=np.float32)
        return emb
    except Exception:
        return None


def compute_embedding(img_path: str):
    """
    ✅ ULTRA MODE embedding:
    1) Extract main face (biggest)
    2) Compute embedding only for that face
    """
    face = extract_main_face(img_path)
    if face is None:
        return None
    return compute_embedding_from_face(face)


def verify_faces(query_path: str, db_img_path: str):
    """
    ✅ Final verification stage: highest accuracy
    """
    try:
        result = DeepFace.verify(
            img1_path=query_path,
            img2_path=db_img_path,
            model_name=cfg.MODEL_NAME,
            detector_backend=cfg.DETECTOR_BACKEND,
            enforce_detection=cfg.ENFORCE_DETECTION,
        )
        return result
    except Exception:
        return None