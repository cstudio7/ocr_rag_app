
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from indexer import build_knowledge_base
from search_engine import query_knowledge_base
import os

UPLOAD_FOLDER = "pdfs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
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

@app.route("/query", methods=["POST"])
def query():
    data = request.get_json()
    query_text = data.get("query")

    if not query_text:
        return jsonify({"error": "Query text is required."}), 400

    results = query_knowledge_base(query_text, top_k=10)
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
