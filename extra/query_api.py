
from flask import Flask, request, jsonify
from flask_cors import CORS
from search_engine import query_knowledge_base

app = Flask(__name__)
CORS(app, supports_credentials=True, origins="*")
# CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/query", methods=["POST"])
def query():
    print("✅ Reached /query endpoint")
    data = request.get_json()
    print("📩 Received query payload:", data)

    query_text = data.get("query")
    if not query_text:
        return jsonify({"error": "Query text is required."}), 400

    results = query_knowledge_base(query_text, top_k=10)
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
