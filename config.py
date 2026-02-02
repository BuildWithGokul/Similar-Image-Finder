import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
FACE_DB_FOLDER = os.path.join(BASE_DIR, "face_db")
DB_PATH = os.path.join(BASE_DIR, "database", "embeddings.pkl")
LOGS_FOLDER = os.path.join(BASE_DIR, "logs")

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

MAX_UPLOAD_SIZE_MB = 10

# ✅ NORMAL MODE (Render Free + Stable + Decent Accuracy 50–75%)
MODEL_NAME = "Facenet512"          # ✅ good accuracy and stable
DETECTOR_BACKEND = "opencv"        # ✅ lightweight (no retinaface download)
ENFORCE_DETECTION = False          # ✅ prevents crash on low quality images

# ✅ Results
TOP_K_RESULTS = 15                 # check more images for better chance
RETURN_TOP_RESULTS = 5             # show best 5

# ✅ Thresholds (balanced)
COSINE_MATCH_THRESHOLD = 0.35      # 0.30 = too loose, 0.40 = too strict
USE_VERIFY_STAGE = False           # ✅ MUST OFF for Render free stability
