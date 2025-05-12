# app.py
from flask import Flask, render_template, request, jsonify
import os
import pytesseract
import pdf2image
from werkzeug.utils import secure_filename
from knowledge_base import build_knowledge_base, query_knowledge_base

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"  # Adjust if needed


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Legal PDF Knowledge Base</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            textarea, input[type=text] { width: 100%; padding: 10px; margin: 10px 0; }
            button { padding: 10px 20px; }
            .result { background: #f3f3f3; padding: 10px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>📄 Upload Legal PDF</h1>
        <form id="uploadForm" enctype="multipart/form-data">
            <input type="file" name="file" id="fileInput" required><br>
            <button type="submit">Upload & Index</button>
        </form>

        <h2>🔍 Ask a Question</h2>
        <input type="text" id="queryInput" placeholder="e.g., What are the termination terms?">
        <button onclick="searchQuery()">Search</button>

        <h3>Results:</h3>
        <div id="results"></div>

        <script>
        document.getElementById('uploadForm').onsubmit = async function(e) {
            e.preventDefault();
            const formData = new FormData();
            const file = document.getElementById('fileInput').files[0];
            formData.append("file", file);

            const response = await fetch('/upload', { method: 'POST', body: formData });
            const result = await response.json();
            alert(result.message || result.error);
        };

        async function searchQuery() {
            const query = document.getElementById('queryInput').value;
            const response = await fetch('/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            const data = await response.json();
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '';
            if (Array.isArray(data)) {
                data.forEach(item => {
                    resultsDiv.innerHTML += `<div class="result"><b>Document:</b> ${item.doc_id}, Page: ${item.page}, Score: ${item.score}<br><pre>${item.text}</pre></div>`;
                });
            } else {
                resultsDiv.innerHTML = `<p>${data.error || 'No results found.'}</p>`;
            }
        }
        </script>
    </body>
    </html>
    '''


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    doc_id = os.path.splitext(filename)[0]
    build_knowledge_base(filepath, doc_id)

    return jsonify({'message': f'File {filename} processed and indexed.', 'doc_id': doc_id})


@app.route('/query', methods=['POST'])
def query():
    data = request.json
    query_text = data.get('query')

    if not query_text:
        return jsonify({'error': 'No query provided'}), 400

    results = query_knowledge_base(query_text)
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)
