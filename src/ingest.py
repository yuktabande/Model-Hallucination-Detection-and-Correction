import os
import json
from src.extract_pdf import extract_pdf_text
from src.chunker import chunk_text
from src.db import init_db

def ingest():
    conn = init_db()
    cursor = conn.cursor()

    # Ingest arXiv PDFs
    for root, _, files in os.walk("data/raw/arxiv"):
        for fname in files:
            if not fname.endswith(".pdf"):
                continue

            paper_id = fname.replace(".pdf", "")
            path = os.path.join(root, fname)

            print(f"[PDF] {paper_id}")

            text = extract_pdf_text(path)
            chunks = chunk_text(text)

            for chunk in chunks:
                cursor.execute("""
                    INSERT INTO chunks (paper_id, chunk, chunk_type, source, year)
                    VALUES (?, ?, ?, ?, ?)
                """, (paper_id, chunk, "pdf", "arXiv", None))

            conn.commit()

    # Ingest Semantic Scholar abstracts
    for root, _, files in os.walk("data/raw/s2"):
        for fname in files:
            if not fname.endswith(".json"):
                continue

            paper_id = fname.replace(".json", "")
            path = os.path.join(root, fname)

            with open(path, "r") as f:
                data = json.load(f)

            print(f"[ABS] {paper_id}")

            abstract = data.get("abstract", "")
            year = data.get("year", None)
            authors = ", ".join(data.get("authors", []))
            venue = data.get("venue", None)

            cursor.execute("""
                INSERT INTO chunks (paper_id, chunk, chunk_type, source, year, authors, venue)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (paper_id, abstract, "abstract", "SemanticScholar", year, authors, venue))

            conn.commit()

    conn.close()

if __name__ == "__main__":
    ingest()