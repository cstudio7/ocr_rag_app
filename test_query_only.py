# test_query_only.py
from search_engine import query_knowledge_base, collection
import os

def display_intro():
    print("\n🧠 Vector Search Test CLI")
    print("─────────────────────────────")
    print("Vector DB path: ", os.path.abspath("vector_store"))
    print("Total chunks stored:", collection.count())

    try:
        sample = collection.peek()
        print("🔎 Sample entry:")
        for i, doc in enumerate(sample["documents"]):
            meta = sample["metadatas"][i]
            print(f"  • Page {meta['page_num']}, Chunk {meta['chunk_index']}: {doc[:80]}...")
    except Exception as e:
        print("⚠️ Error peeking into vector store:", e)

def search_loop():
    while True:
        query = input("\n🔍 Enter your query (or type 'exit'): ").strip()
        if query.lower() == "exit":
            print("👋 Exiting.")
            break

        results = query_knowledge_base(query, top_k=5)

        if not results:
            print("⚠️ No matches found.")
        else:
            for res in results:
                print("\n📄 Match:")
                print(f"Document: {res['doc_id']}, Page: {res['page']}, Score: {res['score']}")
                print("Snippet:")
                print(res['text'])

if __name__ == "__main__":
    display_intro()
    search_loop()
