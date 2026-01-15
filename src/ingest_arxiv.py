import os
import time
import re
from arxiv import Client, Search, SortCriterion, SortOrder

SAVE_DIR = "data/raw/arxiv/"
os.makedirs(SAVE_DIR, exist_ok=True)

INCLUDE_KEYWORDS = [
    "diffusion", "generative", "GAN", "adversarial", "transformer",
    "language model", "LLM", "autoregressive", "normalizing flow",
    "text-to-image", "multi-modal", "foundation model",
]

EXCLUDE_KEYWORDS = [
    "classification", "segmentation", "detection", "forecast", "reinforcement learning"
]

VALID_CATEGORIES = [
    "cs.LG", "cs.AI", "cs.CL", "cs.CV", "stat.ML", "eess.IV"
]
MIN_YEAR = 2014
MAX_YEAR = 2025

client = Client()


def is_relevant(paper):
    title = paper.title.lower()

    if not any(k in title for k in INCLUDE_KEYWORDS):
        return False

    if any(k in title for k in EXCLUDE_KEYWORDS):
        return False

    if paper.primary_category not in VALID_CATEGORIES:
        return False

    year = paper.published.year
    if not (MIN_YEAR <= year <= MAX_YEAR):
        return False

    return True


def sanitize_title(title):
    title = title.lower()
    title = re.sub(r'[^\w\s-]', '', title)
    title = "_".join(title.split())
    return title


def download_arxiv(limit=200):
    count = 0
    downloaded_ids = set()

    queries = [
        "generative models",
        "diffusion models",
        "GAN",
        "transformer",
        "LLM"
    ]

    for query in queries:
        print(f"\n🔍 Searching for: {query}")

        search = Search(
            query=query,
            max_results=limit,
            sort_by=SortCriterion.SubmittedDate,
            sort_order=SortOrder.Descending
        )

        for paper in client.results(search):
            if not is_relevant(paper):
                continue

            arxiv_id = paper.get_short_id()

            if arxiv_id in downloaded_ids:
                print(f"⏩ Skip duplicate ID: {arxiv_id}")
                continue

            downloaded_ids.add(arxiv_id)

            title_clean = sanitize_title(paper.title)
            year = paper.published.year
            filename = f"{year}_{arxiv_id}_{title_clean}.pdf"
            pdf_path = os.path.join(SAVE_DIR, filename)

            if os.path.exists(pdf_path):
                print(f"⏩ Skip exists: {filename}")
                continue

            try:
                print(f"[{count+1}/{limit}] ⬇️  {paper.title} ({year})")
                paper.download_pdf(pdf_path)
                time.sleep(1)
                count += 1

                if count >= limit:
                    print(f"\n✔ Downloaded total: {count} papers")
                    return

            except Exception as e:
                print(f"❌ Failed: {paper.title} — {e}")

    print(f"\n✔ Downloaded total: {count} papers")


if __name__ == "__main__":
    download_arxiv(limit=200)