from knowledge_base import build_knowledge_base, query_knowledge_base, collection
import os

# 1. Set your test PDF file path
pdf_file = r"D:\Project\Search Engine\TMC0058.pdf"  # Update this path if needed
doc_id = "TMC0058"

# Confirm working directory
print("\n📂 Current working directory:", os.getcwd())
print("🔍 Looking for PDF at:", pdf_file)

# 2. Build the knowledge base
if not os.path.exists(pdf_file):
    print(f"❌ PDF not found at: {pdf_file}")
else:
    print(f"📄 Indexing {pdf_file} ...")
    build_knowledge_base(pdf_file, doc_id)
    print(f"✅ Document '{doc_id}' indexed and stored in vector DB.")

# 3. Check vector DB status
print("\n🧠 Vector DB status:")
print("Total chunks stored:", collection.count())
print("Sample entry:", collection.peek())
print("Saving vector DB to:", os.path.abspath("vector_store"))

# 4. Ask a test query
query = "What are the scope and duties?"
print(f"\n🔎 Query: {query}")

results = query_knowledge_base(query, top_k=10)

# 5. Print top results
if results:
    for res in results:
        print("\n📄 Match:")
        print(f"Document: {res['doc_id']}, Page: {res['page']}, Score: {res['score']}")
        print(f"Snippet:\n{res['text']}")
else:
    print("⚠️ No relevant matches found.")
