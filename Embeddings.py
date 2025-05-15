from sentence_transformers import SentenceTransformer
import textwrap
import os
os.environ["OMP_DUPLICATE_LIB_OK"] = "TRUE"


# Load embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_text(text, max_length=500):
    """
    Breaks long text into smaller chunks with a max character length.
    """
    return textwrap.wrap(text, max_length, break_long_words=False, replace_whitespace=False)

def embed_chunks(page_texts, doc_id):
    """
    Converts list of page-wise text into embeddings with metadata.
    
    Args:
        page_texts (List[Dict]): [{'page_num': int, 'text': str}, ...]
        doc_id (str): Unique document ID

    Returns:
        List[Dict]: [{'embedding': vector, 'text': chunk, 'doc_id': ..., 'page_num': ..., 'chunk_index': ...}, ...]
    """
    results = []

    for page in page_texts:
        chunks = chunk_text(page['text'])
        embeddings = model.encode(chunks)

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            results.append({
                'embedding': embedding,
                'text': chunk,
                'doc_id': doc_id,
                'page_num': page['page_num'],
                'chunk_index': i
            })

    return results



from extract_text import extract_text_by_page
from embedding_utils import embed_chunks
pdf_path = r"D:\Project\Search Engine\TMC0058.pdf"

doc_id = "TMC0058"

page_texts = extract_text_by_page(pdf_path, poppler_path=r"C:\poppler-23.11.0\Library\bin")
embedded_chunks = embed_chunks(page_texts, doc_id)

