from sentence_transformers import SentenceTransformer
import textwrap

# Load the embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_text(text, max_length=500):
    """
    Splits text into chunks, retaining important headings and small fragments.
    """
    lines = text.strip().split('\n')
    chunks = []
    buffer = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Treat short or heading-like lines as separate chunks
        if len(line) < 60 and (line.isupper() or line.endswith('.') or line[:2].isdigit()):
            if buffer:
                chunks.append(buffer.strip())
                buffer = ""
            chunks.append(line)
        else:
            if len(buffer + " " + line) <= max_length:
                buffer += " " + line
            else:
                chunks.append(buffer.strip())
                buffer = line

    if buffer:
        chunks.append(buffer.strip())

    return chunks

def embed_chunks(page_texts, doc_id):
    """
    Takes page-wise OCR output and returns embedded text chunks with metadata.

    Args:
        page_texts (List[Dict]): [{'page_num': int, 'text': str}, ...]
        doc_id (str): Unique document identifier.

    Returns:
        List[Dict]: Embedded chunks with metadata.
    """
    results = []

    for page in page_texts:
        chunks = chunk_text(page['text'])
        if not chunks:
            continue

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
