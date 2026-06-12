"""
Quick cosine-similarity tester — paste two sentences and see how similar they are.

Uses the SAME embedding model as the project:
  - Default: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2  (384 dims)
  - Nomic:   nomic-ai/nomic-embed-text-v1.5                              (768 dims)

Set model via .env:  EMBEDDING_MODEL=minilm   or   EMBEDDING_MODEL=nomic

Usage:
    python test_similarity.py

Then enter two sentences when prompted. Type 'quit' to exit.
You can also pass sentences on the command line:
    python test_similarity.py "केले की खेती" "केले के पौधे को कैसे उगाए"
"""
import os
import sys
import numpy as np

# ── Load .env if present ─────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — fall back to system env vars

# ── Model config (mirrors embedding_service.py) ───────────────────────────────
AVAILABLE_MODELS = {
    "minilm": {
        "name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "dims": 384,
    },
    "nomic": {
        "name": "nomic-ai/nomic-embed-text-v1.5",
        "dims": 768,
    },
}

model_key = os.getenv("EMBEDDING_MODEL", "minilm").lower()
if model_key not in AVAILABLE_MODELS:
    print(f"⚠  Unknown model '{model_key}', falling back to 'minilm'")
    model_key = "minilm"

config = AVAILABLE_MODELS[model_key]

# ── Load model ───────────────────────────────────────────────────────────────
from sentence_transformers import SentenceTransformer

print(f"Loading model: {config['name']}  ({config['dims']} dims)")
print("(First load downloads from HuggingFace if not cached — may take a moment)\n")

kwargs = {}
if "nomic" in config["name"]:
    kwargs["trust_remote_code"] = True

model = SentenceTransformer(config["name"], **kwargs)

# ── Helpers ──────────────────────────────────────────────────────────────────
def embed(text: str) -> np.ndarray:
    """Get L2-normalized embedding (cosine similarity = dot product)."""
    return model.encode(
        text.strip(),
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

def cosine_sim(text1: str, text2: str) -> float:
    """Cosine similarity between two texts (0–1 scale)."""
    e1 = embed(text1)
    e2 = embed(text2)
    # Already normalized → dot product = cosine similarity
    return float(np.dot(e1, e2))

# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("COSINE SIMILARITY TESTER")
    print("=" * 60)
    print("Type two sentences to compare.  'quit' to exit.\n")

    # Accept command-line args
    if len(sys.argv) == 3:
        s1, s2 = sys.argv[1], sys.argv[2]
        sim = cosine_sim(s1, s2)
        print(f'  "{s1}"')
        print(f'  "{s2}"')
        print(f"  Similarity: {sim:.4f}")
        sys.exit(0)

    while True:
        try:
            s1 = input("  Sentence 1 > ").strip()
            if s1.lower() == "quit":
                break
            s2 = input("  Sentence 2 > ").strip()
            if s2.lower() == "quit":
                break

            if not s1 or not s2:
                print("  ⚠  Both sentences needed.\n")
                continue

            sim = cosine_sim(s1, s2)
            print(f"  → Cosine similarity: {sim:.4f}")

            # Friendly interpretation
            if sim >= 0.85:
                print("     (Very similar — almost identical meaning)")
            elif sim >= 0.70:
                print("     (Moderately similar — related topic)")
            elif sim >= 0.50:
                print("     (Somewhat related)")
            else:
                print("     (Different / unrelated)")

            print()

        except KeyboardInterrupt:
            print("\nDone.")
            break
