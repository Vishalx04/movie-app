import pickle
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parent/"models"/"svd_baseline_v1.pkl"

_model_cache  = {"model": None, "mtime": None}


def get_cf_model():
    mtime = MODEL_PATH.stat().st_mtime
    if _model_cache["model"] is None or _model_cache["mtime"]!=mtime:
        with open(MODEL_PATH, "rb") as f:
            _model_cache["model"] = pickle.load(f)
        _model_cache["mtime"] = mtime
    return _model_cache["model"]