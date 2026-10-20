"""Download the BGE model once so HintOS can run without internet later."""

from pathlib import Path
import os

MODEL_NAME = "BAAI/bge-small-en-v1.5"
BASE_DIR = Path(__file__).resolve().parent
MODEL_FOLDER = BASE_DIR / "models" / "bge-small-en-v1.5"
CACHE_DIR = BASE_DIR / ".cache" / "huggingface"
os.environ["HF_HOME"] = str(CACHE_DIR)
os.environ["HF_HUB_CACHE"] = str(CACHE_DIR / "hub")
os.environ["TRANSFORMERS_CACHE"] = str(CACHE_DIR / "hub")

from sentence_transformers import SentenceTransformer

MODEL_FOLDER.parent.mkdir(parents=True, exist_ok=True)
model = SentenceTransformer(MODEL_NAME)
model.save(str(MODEL_FOLDER))
print(f"Model saved to: {MODEL_FOLDER}")
