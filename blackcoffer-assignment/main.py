"""SECTION 3 — PIPELINE (run this file).

Orchestrates Section 1 (extraction) + Section 2 (analysis) and writes Output.

Usage:
    python main.py
    python main.py --output Output.xlsx --workers 15
    python main.py --limit 3 --output Output_test.csv   # smoke test
"""
import argparse
import concurrent.futures
import os
import sys

import pandas as pd

from data_extraction import fetch_and_save
from text_analysis import analyze_text, load_master_dict, load_stopwords

COLUMNS = [
    "URL_ID", "URL",
    "POSITIVE SCORE", "NEGATIVE SCORE", "POLARITY SCORE", "SUBJECTIVITY SCORE",
    "AVG SENTENCE LENGTH", "PERCENTAGE OF COMPLEX WORDS", "FOG INDEX",
    "AVG NUMBER OF WORDS PER SENTENCE", "COMPLEX WORD COUNT", "WORD COUNT",
    "SYLLABLE PER WORD", "PERSONAL PRONOUNS", "AVG WORD LENGTH",
]


def main():
    ap = argparse.ArgumentParser(description="Blackcoffer: extraction + analysis pipeline")
    ap.add_argument("--input", default="Input.xlsx")
    ap.add_argument("--output", default="Output.csv")
    ap.add_argument("--articles", default="articles")
    ap.add_argument("--stopwords", default="StopWords")
    ap.add_argument("--master", default="MasterDictionary")
    ap.add_argument("--workers", type=int, default=15)
    ap.add_argument("--limit", type=int, default=0, help="first N URLs only (0=all)")
    args = ap.parse_args()

    os.makedirs(args.articles, exist_ok=True)

    # ---- load inputs ----
    df_in = pd.read_excel(args.input)
    df_in.columns = [str(c).strip() for c in df_in.columns]
    if args.limit:
        df_in = df_in.head(args.limit)

    stopwords = load_stopwords(args.stopwords)
    pos_dict = load_master_dict(os.path.join(args.master, "positive-words.txt"), stopwords)
    neg_dict = load_master_dict(os.path.join(args.master, "negative-words.txt"), stopwords)
    print(f"Stopwords: {len(stopwords)} | Positive: {len(pos_dict)} | Negative: {len(neg_dict)}")
    print(f"Articles: {len(df_in)} | workers={args.workers}")

    # ---- SECTION 1: extraction (parallel, resumable) ----
    texts, errors = {}, {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {
            ex.submit(fetch_and_save, row.URL_ID, row.URL, args.articles): row
            for row in df_in.itertuples()
        }
        done = 0
        for fut in concurrent.futures.as_completed(futs):
            row = futs[fut]
            try:
                url_id, text, err = fut.result()
                texts[url_id] = text
                if err:
                    errors[url_id] = err
            except Exception as e:  # noqa: BLE001
                texts[row.URL_ID] = ""
                errors[row.URL_ID] = f"{type(e).__name__}: {e}"
            done += 1
            if done % 50 == 0 or done == len(futs):
                print(f"  extracted {done}/{len(futs)}")
    if errors:
        print(f"Failed: {len(errors)} (kept empty, e.g. {list(errors.items())[:2]})")

    # ---- SECTION 2+3: analysis + output ----
    rows = []
    for row in df_in.itertuples():
        m = analyze_text(texts.get(row.URL_ID, ""), stopwords, pos_dict, neg_dict)
        rows.append({"URL_ID": row.URL_ID, "URL": row.URL, **m})

    df_out = pd.DataFrame(rows, columns=COLUMNS)
    if args.output.lower().endswith(".xlsx"):
        df_out.to_excel(args.output, index=False)
    else:
        df_out.to_csv(args.output, index=False)
    print(f"Wrote {args.output} ({len(df_out)} rows)")


if __name__ == "__main__":
    sys.exit(main())
