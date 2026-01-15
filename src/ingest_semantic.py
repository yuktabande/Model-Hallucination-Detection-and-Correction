from semanticscholar import SemanticScholar
import os
import json

SAVE_DIR = "data/raw/s2/"
os.makedirs(SAVE_DIR, exist_ok=True)

sch = SemanticScholar()

QUERIES = [
    "diffusion models",
    "generative models",
    "GAN",
    "normalizing flows",
    "autoregressive models",
    "transformers",
    "large language models",
    "text-to-image",
    "foundation models",
]

def fetch_semantic(limit=300):
    count = 0

    for query in QUERIES:
        print(f"Searching S2 for: {query}")
        papers = sch.search_paper(query, limit=100)

        for paper in papers:
            if not paper.abstract:
                continue

            title = paper.title.replace(" ", "_").replace("/", "_")
            json_path = os.path.join(SAVE_DIR, f"{title}.json")

            if os.path.exists(json_path):
                print(f"Skip existing: {title}")
                continue

            data = {
                "title": paper.title,
                "abstract": paper.abstract,
                "year": paper.year,
                "authors": [a['name'] for a in paper.authors] if paper.authors else [],
                "venue": paper.venue,
                "fields": paper.fieldsOfStudy,
                "url": paper.url
            }

            with open(json_path, "w") as f:
                json.dump(data, f, indent=2)

            count += 1
            if count >= limit:
                print(f"Downloaded total: {count} abstracts")
                return

    print(f"Downloaded total: {count} abstracts")

if __name__ == "__main__":
    fetch_semantic(limit=300)