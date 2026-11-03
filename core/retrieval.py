"""用 TF-IDF 在岗位库里做相似 JD 检索（最小可用的 RAG 检索层）。"""
from pathlib import Path
import json

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA = Path(__file__).resolve().parent.parent / "data" / "jds.jsonl"


def load_corpus(path: Path = DATA) -> list:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def similar(query: str, corpus: list | None = None, k: int = 3):
    corpus = corpus if corpus is not None else load_corpus()
    docs = [f"{r['title']} {r['text']}" for r in corpus]
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(docs + [query])
    last = matrix.shape[0] - 1
    sims = cosine_similarity(matrix[last], matrix[:last]).flatten()
    order = sims.argsort()[::-1][:k]
    return [
        {"id": corpus[i]["id"], "title": corpus[i]["title"], "score": round(float(sims[i]), 3)}
        for i in order
    ]


def similarity(query: str, doc: str) -> float:
    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform([query, doc])
    return float(cosine_similarity(matrix[0], matrix[1])[0][0])
