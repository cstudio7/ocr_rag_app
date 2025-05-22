from werkzeug.utils import secure_filename
import os
from parallel_indexer import index_pdf
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import time
import logging

UPLOAD_FOLDER = "pdfs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

progress_updates = []  # For SSE tracking

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("upload_indexing.log"),
        logging.StreamHandler()
    ]
)

@app.route("/upload", methods=["POST"])
def upload():
    if 'pdfs' not in request.files:
        return jsonify({"error": "No files uploaded under 'pdfs' field."}), 400

    files = request.files.getlist("pdfs")
    if not files:
        return jsonify({"error": "No files received."}), 400

    indexed_files = []
    total_start = time.time()

    for file in files:
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        doc_id = os.path.splitext(filename)[0]
        progress_updates.append(f"📥 Starting indexing: {doc_id}")
        logging.info(f"📥 Starting indexing for {doc_id}")

        start_time = time.time()
        index_pdf(save_path)
        end_time = time.time()

        indexed_files.append(doc_id)
        progress_updates.append(f"✅ Finished indexing: {doc_id} in {end_time - start_time:.2f} sec")
        logging.info(f"✅ Finished indexing {doc_id} in {end_time - start_time:.2f} seconds")

    total_time = time.time() - total_start
    logging.info(f"⏱ Total indexing time for {len(indexed_files)} PDFs: {total_time:.2f} seconds")
    return jsonify({"message": f"Indexed {len(indexed_files)} PDF(s): {', '.join(indexed_files)}"})

@app.route('/progress')
def progress_stream():
    def generate():
        last_idx = 0
        while True:
            if last_idx < len(progress_updates):
                yield f"data: {progress_updates[last_idx]}\n\n"
                last_idx += 1
            time.sleep(0.5)
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == "__main__":
    app.run(debug=True)