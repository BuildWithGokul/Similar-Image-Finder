import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
FACE_DB_FOLDER = os.path.join(BASE_DIR, "face_db")
DB_PATH = os.path.join(BASE_DIR, "database", "embeddings.pkl")
LOGS_FOLDER = os.path.join(BASE_DIR, "logs")

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

MAX_UPLOAD_SIZE_MB = 10

# 🔥 ULTRA MODE
MODEL_NAME = "ArcFace"
DETECTOR_BACKEND = "retinaface"
ENFORCE_DETECTION = False

# 🔥 Results
TOP_K_RESULTS = 10            # shortlist more
RETURN_TOP_RESULTS = 5        # show best 5

# 🔥 Thresholds
COSINE_MATCH_THRESHOLD = 0.30     # increase = strict
USE_VERIFY_STAGE = True