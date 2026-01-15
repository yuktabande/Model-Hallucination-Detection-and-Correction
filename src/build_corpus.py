import os
import time
import re
import sqlite3
from rapidfuzz import fuzz
from semanticscholar import SemanticScholar
from arxiv import Client, Search, SortCriterion, SortOrder
import pdfplumber

# ---------------- CONFIG ----------------

ARXIV_LIMIT = 50       # bump to 200 later
S2_LIMIT = 100         # bump to 300 later
MERGE_THRESHOLD = 85   # fuzzy match threshold
S2_SLEEP = 1.5         # throttle to avoid 429

DATA_RAW = "data/raw"
DATA_PROCESSED = "data/processed"
DB_PATH = f"{DATA_PROCESSED}/chunks.db"

os.makedirs(DATA_RAW, exist_ok=True)
os.makedirs(DATA_PROCESSED, exist_ok=True)

client = Client()
sch = SemanticScholar()

# ---------------- HELPERS ----------------

def normalize_title(title):
    title = title.lower()
    title = re.sub(r'[^\w\s]', '', title)
    title = " ".join(title.split())
    return title

def similar(a, b):
    return fuzz.ratio(a, b)

# ---------------- S2 FETCH ----------------

def fetch_s2():
    print("\n📚 Fetching Semantic Scholar abstracts (throttled)...")

    abstracts = []
    queries = ["diffusion models", "generative models", "GAN", "LLM", "transformer"]

    for q in queries:
        print(f"  🔍 S2 query: {q}")
        papers = sch.search_paper(q, limit=S2_LIMIT)

        for p in papers:
            time.sleep(S2_SLEEP)  # throttle to avoid 429
            if p.abstract:
                abstracts.append({
                    "title": p.title,
                    "title_norm": normalize_title(p.title),
                    "abstract": p.abstract,
                    "year": p.year,
                    "authors": [a['name'] for a in p.authors] if p.authors else []
                })

        print(f"    ↳ collected: {len(abstracts)} abstracts so far")

    print(f"✔ Total abstracts: {len(abstracts)}")
    return abstracts

# ---------------- ARXIV FETCH ----------------

def fetch_arxiv():
    print("\n📄 Fetching arXiv PDFs...")

    pdfs = []
    downloaded_ids = set()

    queries = ["generative models", "diffusion models", "GAN", "LLM", "transformer"]

    for query in queries:
        print(f"  🔍 arXiv query: {query}")

        search = Search(
            query=query,
            max_results=ARXIV_LIMIT,
            sort_by=SortCriterion.SubmittedDate,
            sort_order=SortOrder.Descending
        )

        for paper in client.results(search):
            arxiv_id = paper.get_short_id()
            if arxiv_id in downloaded_ids:
                continue
            downloaded_ids.add(arxiv_id)

            year = paper.published.year
            title_clean = normalize_title(paper.title)
            filename = f"{year}_{arxiv_id}_{title_clean}.pdf"
            path = f"{DATA_RAW}/{filename}"

            try:
                paper.download_pdf(path)
                time.sleep(1)
                pdfs.append({
                    "title": paper.title,
                    "title_norm": normalize_title(paper.title),
                    "year": year,
                    "path": path
                })
            except Exception as e:
                print(f"❌ Failed PDF: {paper.title} — {e}")

    print(f"✔ Total PDFs: {len(pdfs)}")
    return pdfs

# ---------------- PDF EXTRACT ----------------

def extract_pdf(path):
    text = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text.append(t)
    except:
        print(f"⚠️ PDF extraction failed: {path}")
    return "\n".join(text)

# ---------------- CHUNK ----------------

def chunk(text, size=350):
    words = text.split()
    for i in range(0, len(words), size):
        yield " ".join(words[i:i+size])

# ---------------- MERGE ----------------

def merge(pdfs, abstracts):
    print("\n🔄 Merging PDF + Abstracts...")

    merged = []

    for p in pdfs:
        best = None
        best_score = 0

        for a in abstracts:
            score = similar(p['title_norm'], a['title_norm'])
            if score > best_score:
                best = a
                best_score = score

        if best_score >= MERGE_THRESHOLD:
            merged.append({
                "title": p['title'],
                "year": p['year'],
                "abstract": best['abstract'],
                "pdf_path": p['path']
            })
        else:
            merged.append({
                "title": p['title'],
                "year": p['year'],
                "abstract": None,
                "pdf_path": p['path']
            })

    print(f"✔ Merged entities: {len(merged)}")
    return merged

# ---------------- DB SAVE ----------------

def save_db(papers):
    print("\n🗄 Saving to SQLite...")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS chunks;")
    c.execute("""
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY,
            title TEXT,
            year INTEGER,
            chunk TEXT,
            chunk_type TEXT
        );
    """)

    for p in papers:
        if p['abstract']:
            c.execute("INSERT INTO chunks (title, year, chunk, chunk_type) VALUES (?, ?, ?, ?)",
                      (p['title'], p['year'], p['abstract'], "abstract"))

        pdf_text = extract_pdf(p['pdf_path'])
        for ch in chunk(pdf_text):
            c.execute("INSERT INTO chunks (title, year, chunk, chunk_type) VALUES (?, ?, ?, ?)",
                      (p['title'], p['year'], ch, "pdf"))

    conn.commit()
    conn.close()
    print("✔ DB saved!")

# ---------------- MAIN ----------------

if __name__ == "__main__":
    abstracts = fetch_s2()
    pdfs = fetch_arxiv()
    merged = merge(pdfs, abstracts)
    save_db(merged)
    print("\n🎉 Corpus build complete!")