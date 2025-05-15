from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from indexer import build_knowledge_base
from flask import Flask, request, jsonify
from flask_cors import CORS  # ✅ Import this

UPLOAD_FOLDER = "pdfs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app = Flask(__name__)
CORS(app)  # ✅ Enable CORS for all routes


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/upload", methods=["POST"])
def upload():
    if 'pdfs' not in request.files:
        return jsonify({"error": "No files uploaded under 'pdfs' field."}), 400

    files = request.files.getlist("pdfs")
    if not files:
        return jsonify({"error": "No files received."}), 400

    indexed_files = []
    for file in files:
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        doc_id = os.path.splitext(filename)[0]
        build_knowledge_base(save_path, doc_id)
        indexed_files.append(doc_id)

    return jsonify({"message": f"Indexed {len(indexed_files)} PDF(s): {', '.join(indexed_files)}"})

if __name__ == "__main__":
    app.run(debug=True)
