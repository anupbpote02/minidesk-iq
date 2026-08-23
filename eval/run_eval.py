"""Runs eval_questions.json against retrieval and reports hit-rate@k.

For each question with an expected_source, checks whether that source document
appears anywhere in the top-k retrieved chunks. Questions with expected_source
set to null are "should not confidently match" cases — success means the top
similarity score falls below the configured threshold.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import RETRIEVAL_SIMILARITY_THRESHOLD, RETRIEVAL_TOP_K  # noqa: E402
from app.rag.retrieve import retrieve  # noqa: E402

EVAL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eval_questions.json")


def run_eval():
    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)

    results = []
    hits = 0
    total = len(cases)

    for case in cases:
        question = case["question"]
        expected = case["expected_source"]
        chunks = retrieve(question, top_k=RETRIEVAL_TOP_K)
        retrieved_sources = [c.source for c in chunks]
        top_similarity = chunks[0].similarity if chunks else 0.0

        if expected is None:
            passed = top_similarity < RETRIEVAL_SIMILARITY_THRESHOLD
        else:
            passed = expected in retrieved_sources

        if passed:
            hits += 1

        results.append(
            {
                "question": question,
                "expected_source": expected,
                "retrieved_sources": retrieved_sources,
                "top_similarity": round(top_similarity, 4),
                "passed": passed,
            }
        )

    hit_rate = hits / total if total else 0.0

    print("=" * 70)
    print(f"MiniDesk IQ Retrieval Eval — top_k={RETRIEVAL_TOP_K}, threshold={RETRIEVAL_SIMILARITY_THRESHOLD}")
    print("=" * 70)
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] {r['question']}")
        print(f"       expected: {r['expected_source']}  |  top_similarity: {r['top_similarity']}")
        print(f"       retrieved: {r['retrieved_sources']}")
    print("=" * 70)
    print(f"Hit rate: {hits}/{total} ({hit_rate * 100:.1f}%)")
    print("=" * 70)

    return {"hit_rate": hit_rate, "hits": hits, "total": total, "results": results}


if __name__ == "__main__":
    run_eval()
