"""
Main Flask application for PDF Knowledge Base.
Provides a web interface for uploading, indexing, and searching PDF documents.
"""
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from werkzeug.utils import secure_filename
import os
import time
import logging

# Import configuration
from config import (
    PDF_DIR, FLASK_DEBUG, MAX_CONTENT_LENGTH,
    LOG_LEVEL, LOG_FORMAT, LOG_FILE
)

# Import core functionality
from core.indexer import index_pdf
from core.search import query_knowledge_base, get_document_stats, get_document_list

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = PDF_DIR
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Global variable to store progress updates
progress_updates = []

# Routes for UI pages
@app.route('/')
def index():
    """Home page with navigation"""
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    """Page for uploading and indexing PDFs"""
    return render_template('upload.html')

@app.route('/search')
def search_page():
    """Page for searching indexed documents"""
    # Get stats about indexed documents
    try:
        stats = get_document_stats()
        doc_count = stats['doc_count']
        chunk_count = stats['chunk_count']
    except Exception as e:
        logging.error(f"Error getting collection stats: {e}")
        doc_count = 0
        chunk_count = 0

    return render_template('search.html', doc_count=doc_count, chunk_count=chunk_count)

# API Routes
@app.route("/api/upload", methods=["POST"])
def upload_api():
    """API endpoint for uploading and indexing PDFs"""
    if 'pdfs' not in request.files:
        return jsonify({"error": "No files uploaded under 'pdfs' field."}), 400

    files = request.files.getlist("pdfs")
    if not files:
        return jsonify({"error": "No files received."}), 400

    # Clear previous progress updates
    global progress_updates
    progress_updates = []

    indexed_files = []
    total_start = time.time()

    for file in files:
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        doc_id = os.path.splitext(filename)[0]
        progress_updates.append(f"Starting indexing: {doc_id}")
        logging.info(f"Starting indexing for {doc_id}")

        start_time = time.time()
        index_pdf(save_path)
        end_time = time.time()

        indexed_files.append(doc_id)
        progress_updates.append(f"Finished indexing: {doc_id} in {end_time - start_time:.2f} sec")
        logging.info(f"Finished indexing {doc_id} in {end_time - start_time:.2f} seconds")

    total_time = time.time() - total_start
    logging.info(f"Total indexing time for {len(indexed_files)} PDFs: {total_time:.2f} seconds")
    return jsonify({"message": f"Indexed {len(indexed_files)} PDF(s): {', '.join(indexed_files)}"})

@app.route('/api/progress')
def progress_stream():
    """Server-sent events endpoint for progress updates"""
    def generate():
        last_idx = 0
        while True:
            if last_idx < len(progress_updates):
                yield f"data: {progress_updates[last_idx]}\n\n"
                last_idx += 1
            time.sleep(0.5)
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route("/api/query", methods=["POST"])
def query_api():
    """API endpoint for searching indexed documents"""
    data = request.get_json()
    query_text = data.get("query")

    if not query_text:
        return jsonify({"error": "Query text is required."}), 400

    results = query_knowledge_base(query_text, top_k=10)
    return jsonify(results)

@app.route("/api/documents")
def get_documents():
    """API endpoint to get list of indexed documents"""
    try:
        doc_stats = get_document_list()
        return jsonify({"documents": doc_stats})
    except Exception as e:
        logging.error(f"Error getting document list: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=FLASK_DEBUG)
