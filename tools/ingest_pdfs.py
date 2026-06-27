"""
Apple Financial RAG — PDF Ingestion Script
Reads PDFs from 'apple date/', creates embeddings via OpenAI text-embedding-3-small (1024 dims),
and uploads vectors to Pinecone 'apple-rag' index.

Usage:
    set OPENAI_API_KEY=sk-...
    set PINECONE_API_KEY=pcsk-...
    python tools/ingest_pdfs.py
"""

import os
import sys
from pathlib import Path
from typing import List


PINECONE_INDEX = "apple-rag"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS = 1024
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
BATCH_SIZE = 96

SKIP_FILES = {"_10-K-2025-As-Filed (1).pdf"}


def split_text(text: str) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk = text[start:end].strip()
        if len(chunk) > 50:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def extract_pdf_text(pdf_path: Path) -> str:
    import pypdf
    text_parts = []
    with open(pdf_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(f"[Page {page_num + 1}]\n{page_text}")
    return "\n\n".join(text_parts)


def main():
    openai_key = os.environ.get("OPENAI_API_KEY")
    pinecone_key = os.environ.get("PINECONE_API_KEY")

    if not openai_key:
        print("ERROR: Set OPENAI_API_KEY environment variable first.")
        print("  Windows:  set OPENAI_API_KEY=sk-...")
        sys.exit(1)
    if not pinecone_key:
        print("ERROR: Set PINECONE_API_KEY environment variable first.")
        print("  Windows:  set PINECONE_API_KEY=pcsk-...")
        sys.exit(1)

    try:
        from openai import OpenAI
    except ImportError:
        print("ERROR: openai not installed. Run:  pip install openai")
        sys.exit(1)
    try:
        from pinecone import Pinecone
    except ImportError:
        print("ERROR: pinecone not installed. Run:  pip install pinecone-client")
        sys.exit(1)
    try:
        import pypdf
    except ImportError:
        print("ERROR: pypdf not installed. Run:  pip install pypdf")
        sys.exit(1)

    pdf_dir = Path(__file__).parent.parent / "apple date"
    if not pdf_dir.exists():
        print(f"ERROR: PDF directory not found: {pdf_dir}")
        sys.exit(1)

    pdf_files = sorted(f for f in pdf_dir.glob("*.pdf") if f.name not in SKIP_FILES)
    if not pdf_files:
        print(f"ERROR: No PDFs found in {pdf_dir}")
        sys.exit(1)

    print(f"Found {len(pdf_files)} PDFs to ingest:")
    for p in pdf_files:
        print(f"  - {p.name}")

    openai_client = OpenAI(api_key=openai_key)
    pc = Pinecone(api_key=pinecone_key)
    index = pc.Index(PINECONE_INDEX)

    total_vectors = 0

    for pdf_path in pdf_files:
        print(f"\n[{pdf_path.name}]")
        print("  Extracting text...")
        text = extract_pdf_text(pdf_path)
        if not text.strip():
            print("  WARNING: No text extracted, skipping.")
            continue

        chunks = split_text(text)
        print(f"  {len(text):,} chars → {len(chunks)} chunks")

        for batch_start in range(0, len(chunks), BATCH_SIZE):
            batch_chunks = chunks[batch_start: batch_start + BATCH_SIZE]

            response = openai_client.embeddings.create(
                input=batch_chunks,
                model=EMBEDDING_MODEL,
                dimensions=EMBEDDING_DIMS,
            )

            vectors = []
            for i, (chunk, emb_obj) in enumerate(zip(batch_chunks, response.data)):
                global_idx = batch_start + i
                vectors.append({
                    "id": f"{pdf_path.stem}_chunk_{global_idx:04d}",
                    "values": emb_obj.embedding,
                    "metadata": {
                        "text": chunk,
                        "source": pdf_path.name,
                        "chunk_index": global_idx,
                    },
                })

            index.upsert(vectors=vectors)
            done = min(batch_start + BATCH_SIZE, len(chunks))
            print(f"  Uploaded chunks {batch_start + 1}–{done} / {len(chunks)}")
            total_vectors += len(vectors)

    print(f"\n✓ Done! {total_vectors} vectors uploaded to Pinecone index '{PINECONE_INDEX}'.")
    print("\nNext step: Activate the Telegram bot workflow in n8n UI:")
    print("  https://ahmadmadi.cfd/workflow/wG2LXqOEGwdog81G")
    print("  → Toggle the 'Active' switch (top-right)")
