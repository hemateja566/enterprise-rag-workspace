"""SECTION 2 — TEXT ANALYSIS.

Implements every variable defined in Text Analysis.docx:
sentiment scores, readability (Gunning Fog), word/syllable counts,
personal pronouns, avg word length.
"""
import glob
import os
import re


def load_stopwords(stop_dir):
    """Union of all StopWords_*.txt files, lowercased.

    Handles 'WORD | comment' lines by keeping the token before '|'.
    """
    stops = set()
    for path in glob.glob(os.path.join(stop_dir, "*.txt")):
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if "|" in line:
                    line = line.split("|")[0].strip()
                token = line.split()[0] if line.split() else ""
                token = token.strip().strip(",").lower()
                if token:
                    stops.add(token)
    return stops


def load_master_dict(path, stopwords):
    """Load positive/negative word list, keeping words NOT in stopwords."""
    words = set()
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            w = line.strip().lower()
            if not w:
                continue
            w = w.split()[0]
            if w and w not in stopwords:
                words.add(w)
    return words


def tokenize_words(text):
    """Word tokens: alphabetic sequences."""
    return re.findall(r"[A-Za-z]+", text)


def split_sentences(text):
    """Sentence split on . ! ? (avoids nltk data dependency)."""
    text = text.strip()
    if not text:
        return []
    parts = re.split(r"[.!?]+(?:\s+|$)", text)
    return [p.strip() for p in parts if p.strip()]


def syllable_count_word(word):
    """Vowel-group count with es/ed exception (per Text Analysis.docx)."""
    w = word.lower()
    if len(w) <= 2:
        return 1
    if w.endswith("es") or w.endswith("ed"):
        w = w[:-2]
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for ch in w:
        is_v = ch in vowels
        if is_v and not prev_vowel:
            count += 1
        prev_vowel = is_v
    return max(count, 1)


def count_personal_pronouns(text):
    """Counts I/we/my/ours/us (case-insensitive), excluding country 'US'."""
    matches = re.findall(r"\b(I|we|my|ours|us)\b", text, flags=re.IGNORECASE)
    n_us_upper = len(re.findall(r"\bUS\b", text))  # case-sensitive
    return max(len(matches) - n_us_upper, 0)


def analyze_text(text, stopwords, pos_dict, neg_dict):
    """Compute the 13 output variables. Returns dict."""
    raw_words = tokenize_words(text)
    lowered = [w.lower() for w in raw_words]
    cleaned = [w for w in lowered if w not in stopwords]

    pos = sum(1 for w in cleaned if w in pos_dict)
    neg = sum(1 for w in cleaned if w in neg_dict)

    polarity = (pos - neg) / ((pos + neg) + 0.000001)
    subjectivity = (pos + neg) / (len(cleaned) + 0.000001)

    sentences = split_sentences(text)
    n_sent = len(sentences) if sentences else 1
    n_words_raw = len(raw_words) if raw_words else 1

    avg_sent_len = n_words_raw / n_sent

    syllables = [syllable_count_word(w) for w in raw_words]
    complex_count = sum(1 for s in syllables if s > 2)
    pct_complex = complex_count / n_words_raw
    fog = 0.4 * (avg_sent_len + pct_complex)

    avg_words_per_sent = avg_sent_len  # same definition, separate column

    word_count = len(cleaned)
    syll_per_word = (sum(syllables) / n_words_raw) if n_words_raw else 0.0
    pronouns = count_personal_pronouns(text)
    avg_word_len = (sum(len(w) for w in raw_words) / n_words_raw) if n_words_raw else 0.0

    return {
        "POSITIVE SCORE": pos,
        "NEGATIVE SCORE": neg,
        "POLARITY SCORE": round(polarity, 4),
        "SUBJECTIVITY SCORE": round(subjectivity, 4),
        "AVG SENTENCE LENGTH": round(avg_sent_len, 2),
        "PERCENTAGE OF COMPLEX WORDS": round(pct_complex, 4),
        "FOG INDEX": round(fog, 2),
        "AVG NUMBER OF WORDS PER SENTENCE": round(avg_words_per_sent, 2),
        "COMPLEX WORD COUNT": complex_count,
        "WORD COUNT": word_count,
        "SYLLABLE PER WORD": round(syll_per_word, 2),
        "PERSONAL PRONOUNS": pronouns,
        "AVG WORD LENGTH": round(avg_word_len, 2),
    }
