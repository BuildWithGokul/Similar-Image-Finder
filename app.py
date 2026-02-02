import os
from datetime import datetime
import numpy as np

from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

import config as cfg
from utils import (
    ensure_folder,
    allowed_file,
    load_db,
    save_db,
    compute_embedding,
    cosine_similarity,
    verify_faces,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = cfg.MAX_UPLOAD_SIZE_MB * 1024 * 1024

ensure_folder(cfg.UPLOAD_FOLDER)
ensure_folder(cfg.FACE_DB_FOLDER)
ensure_folder(os.path.dirname(cfg.DB_PATH))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(cfg.UPLOAD_FOLDER, filename)


@app.route("/face_db/<path:filename>")
def db_file(filename):
    return send_from_directory(cfg.FACE_DB_FOLDER, filename)


@app.route("/api/rebuild_db", methods=["POST"])
def rebuild_db():
    db_data = {"embeddings": [], "filenames": []}

    files = [
        f for f in os.listdir(cfg.FACE_DB_FOLDER)
        if f.lower().split(".")[-1] in cfg.ALLOWED_EXTENSIONS
    ]

    if len(files) == 0:
        save_db(db_data)
        return jsonify({"ok": True, "count": 0, "skipped": 0, "message": "No images found in face_db."})

    skipped = 0

    for fname in files:
        img_path = os.path.join(cfg.FACE_DB_FOLDER, fname)

        emb = compute_embedding(img_path)
        if emb is None:
            skipped += 1
            continue

        db_data["embeddings"].append(emb.tolist())
        db_data["filenames"].append(fname)

    save_db(db_data)

    return jsonify({
        "ok": True,
        "count": len(db_data["filenames"]),
        "skipped": skipped,
        "message": "Database rebuilt successfully ✅"
    })


@app.route("/api/search", methods=["POST"])
def search_similar_faces():
    if "image" not in request.files:
        return jsonify({"ok": False, "error": "No image received"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"ok": False, "error": "Empty filename"}), 400

    if not allowed_file(file.filename):
        return jsonify({"ok": False, "error": "Only JPG/JPEG/PNG allowed"}), 400

    # Save uploaded file
    filename = secure_filename(file.filename)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_name = f"{ts}_{filename}"
    saved_path = os.path.join(cfg.UPLOAD_FOLDER, saved_name)
    file.save(saved_path)

    # Query embedding (ULTRA)
    query_emb = compute_embedding(saved_path)
    if query_emb is None:
        return jsonify({"ok": False, "error": "No main face detected. Use clear front face photo."}), 400

    # Load DB
    db = load_db()
    if len(db.get("embeddings", [])) == 0:
        return jsonify({"ok": False, "error": "Database empty. Click Rebuild DB first."}), 400

    db_embeddings = np.array(db["embeddings"], dtype=np.float32)

    # Stage 1: cosine shortlist
    scores = [cosine_similarity(query_emb, emb) for emb in db_embeddings]
    shortlist_k = min(cfg.TOP_K_RESULTS, len(scores))
    shortlist_indexes = np.argsort(scores)[::-1][:shortlist_k]

    temp_results = []
    for idx in shortlist_indexes:
        fname = db["filenames"][int(idx)]
        score = float(scores[int(idx)])

        if score < cfg.COSINE_MATCH_THRESHOLD:
            continue

        item = {
            "filename": fname,
            "score": score,
            "db_image_url": f"/face_db/{fname}",
            "verified": None,
            "distance": None,
        }
        temp_results.append(item)

    # Stage 2: verify stage
    if cfg.USE_VERIFY_STAGE and temp_results:
        for item in temp_results:
            db_img_path = os.path.join(cfg.FACE_DB_FOLDER, item["filename"])
            v = verify_faces(saved_path, db_img_path)
            if v is not None:
                item["verified"] = bool(v.get("verified", False))
                item["distance"] = float(v.get("distance", 999))

        # Sort: verified first, then best similarity
        temp_results.sort(key=lambda x: (x["verified"] is True, x["score"]), reverse=True)

    # Return top results (UI)
    final_results = temp_results[: cfg.RETURN_TOP_RESULTS]

    return jsonify({
        "ok": True,
        "uploaded": saved_name,
        "uploaded_url": f"/uploads/{saved_name}",
        "results": final_results
    })


if __name__ == "__main__":
    app.run(debug=True)