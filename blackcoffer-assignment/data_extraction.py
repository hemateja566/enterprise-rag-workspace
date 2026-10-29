"""SECTION 1 — DATA EXTRACTION.

Fetches each URL from Input.xlsx and saves title + article text to
articles/<URL_ID>.txt (header/footer excluded).
"""
import os
import time

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def extract_article(url, timeout=30):
    """Fetch URL, return (title, full_text). Raises on failure."""
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "html.parser")

    # --- title: prefer article h1, else og:title, else <title>
    title = ""
    h1 = soup.select_one("h1.entry-title") or soup.select_one("article h1") or soup.find("h1")
    if h1:
        title = h1.get_text(" ", strip=True)
    if not title:
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            title = og["content"].strip()
    if not title and soup.title:
        title = soup.title.get_text(" ", strip=True)

    # --- body: site uses div.td-post-content (Newspaper WordPress theme)
    body = None
    for sel in ["div.td-post-content", "article", "div.entry-content", "main"]:
        el = soup.select_one(sel)
        if el and len(el.get_text(strip=True)) > 200:
            body = el
            break
    if body is None:
        body = soup.body

    texts = []
    for tag in body.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        t = tag.get_text(" ", strip=True)
        if t and len(t) > 1:
            texts.append(t)
    article_text = "\n".join(texts)
    if len(article_text) < 100:
        article_text = body.get_text("\n", strip=True)
    full = (title + "\n" + article_text).strip() if title else article_text.strip()
    return title.strip(), full


def fetch_and_save(url_id, url, articles_dir, retries=3):
    """Download one article, save to articles_dir/<url_id>.txt."""
    out_path = os.path.join(articles_dir, f"{url_id}.txt")
    if os.path.exists(out_path) and os.path.getsize(out_path) > 100:
        with open(out_path, encoding="utf-8", errors="ignore") as f:
            return url_id, f.read(), None
    err = None
    for attempt in range(retries):
        try:
            _, full = extract_article(url)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(full)
            return url_id, full, None
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}: {e}"
            time.sleep(1.5 * (attempt + 1))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("")
    return url_id, "", err
