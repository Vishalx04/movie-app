import json 
import pickle
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path 

import pandas as pd
from sqlalchemy.orm import Session
from surprise import SVD, Dataset, Reader
from surprise.model_selection import train_test_split as svd_train_test_split
from surprise import accuracy

from app.db.database import sessionLocal
from app.db.models import Movie, Rating

MIN_RATINGS_PER_MOVIE = 5
N_FACTORS = 50
RANDOM_STATE = 42
HIT_RATE_SAMPLE_SIZE = 3000
HIT_RATE_K = 10
HIT_RATE_N_NEGATIVES = 99
REGRESSION_TOLERANCE = 0.02   #new model can not be more worse than this

MODEL_DIR = Path(__file__).resolve().parent.parent /"ml"/"models"
CURRENT_MODEL_PATH = MODEL_DIR/"svd_baseline_v1.pkl"
PREVIOUS_MODEL_PATH = MODEL_DIR/"svd_previous.pkl"
METADATA_PATH = MODEL_DIR/"svd_baseline_v1_metadata.json"

