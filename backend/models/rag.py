import os
from pinecone import Pinecone
from dotenv import load_dotenv
from google import genai
from google.genai import types
import fitz

load_dotenv()

pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
vector_index = pinecone_client.Index("yatrasathi-ai")


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract plain text across all pages in a PDF."""
    text = ""
    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            text += page.get_text() + "\n"
    return text.strip()


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """Splits document text into overlapping chunks for better RAG precision."""
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def embed_text(text: str) -> list[float]:
    """Generate 768-dimensional embedding vector using Gemini."""
    response = gemini_client.models.embed_content(
        model="gemini-embedding-2",
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=768),
    )
    return response.embeddings[0].values


def upsert_chunks_to_pinecone(chunks_with_meta: list[dict]):
    """Batch-upsert chunk vectors and their text payloads to Pinecone."""
    upsert_data = []
    for item in chunks_with_meta:
        vector = embed_text(item["text"])
        upsert_data.append((
            item["id"],
            vector,
            {"text": item["text"], "source": item["source"]}
        ))
    
    batch_size = 50
    for i in range(0, len(upsert_data), batch_size):
        vector_index.upsert(vectors=upsert_data[i:i + batch_size])


def ingest_documents(pdf_dir: str = "./backend/documents"):
    """Reads all PDFs, splits them into chunks, and uploads them to Pinecone."""
    if not os.path.exists(pdf_dir):
        print(f"Directory {pdf_dir} does not exist.")
        return

    all_chunks = []
    for file_name in os.listdir(pdf_dir):
        if not file_name.lower().endswith(".pdf"):
            continue
            
        full_pdf_path = os.path.join(pdf_dir, file_name)
        doc_text = extract_text_from_pdf(full_pdf_path)
        chunks = chunk_text(doc_text)
        
        for idx, chunk in enumerate(chunks):
            clean_name = os.path.splitext(file_name)[0]
            all_chunks.append({
                "id": f"{clean_name}_chunk_{idx}",
                "text": chunk,
                "source": file_name
            })

    if all_chunks:
        upsert_chunks_to_pinecone(all_chunks)
        print(f"Successfully upserted {len(all_chunks)} chunks to Pinecone.")
    else:
        print("No documents found to ingest.")


def query_rag(query: str, top_k: int = 3) -> str:
    """Retrieve relevant document contexts from Pinecone for a given query."""
    query_vector = embed_text(query)
    search_results = vector_index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True
    )

    contexts = [
        match["metadata"]["text"]
        for match in search_results.get("matches", [])
        if "metadata" in match and "text" in match["metadata"]
    ]
    return "\n---\n".join(contexts)


if __name__ == "__main__":
    ingest_documents()