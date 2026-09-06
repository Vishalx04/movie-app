import pickle
from pathlib import Path
from functools import lru_cache

MODEL_PATH = Path(__file__).resolve().parent/"models"/"svd_baseline_v1.pkl"

@lru_cache(maxsize=1)
def get_cf_model():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

