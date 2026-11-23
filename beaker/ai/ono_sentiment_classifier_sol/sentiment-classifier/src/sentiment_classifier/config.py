"""Configuration. Every value can be overridden through environment variables."""

import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
MODELS_DIR = Path(os.environ.get("MODELS_DIR", "models"))
PROCESSED_DIR = Path(os.environ.get("PROCESSED_DIR", DATA_DIR / "processed"))

RAW_CSV = DATA_DIR / "sentiment_data.csv"
TRAIN_SAMPLES_BIN = PROCESSED_DIR / "train_samples.bin"
TRAIN_LABELS_BIN = PROCESSED_DIR / "train_labels.bin"
TEST_SPARSE = PROCESSED_DIR / "test_x.npz"
TEST_Y = PROCESSED_DIR / "test_y.npy"
VECTORIZER = MODELS_DIR / "vectorizer.joblib"
META = PROCESSED_DIR / "meta.json"
WEIGHTS = MODELS_DIR / "sentiment.safetensors"
LOSS_HISTORY = MODELS_DIR / "loss_history.json"

# Label ids are assumed from the data: 0 negative, 1 neutral, 2 positive.
CLASS_NAMES = ["negative", "neutral", "positive"]
N_CLASSES = len(CLASS_NAMES)

N_FEATURES = int(os.environ.get("N_FEATURES", 2000))
TEST_SIZE = float(os.environ.get("TEST_SIZE", 0.1))
MAX_ROWS = int(os.environ["MAX_ROWS"]) if os.environ.get("MAX_ROWS") else None
SEED = int(os.environ.get("SEED", 42))

# ONO's CrossEntropy expects probabilities, hence the final softmax.
LAYERS = [(256, "relu"), (64, "relu"), (N_CLASSES, "softmax")]

# With all_reduce every node is a worker.
N_NODES = int(os.environ.get("NODES", 3))
BASE_PORT = 40_000
NODE_ADDRS = [f"node-{i}:{BASE_PORT + i}" for i in range(N_NODES)]

# ONO applies the optimizer once per epoch (docs/ono-notes.md #16), so Adam barely trains:
# plain gradient descent is the default. ONO's gradient is mean-CE / n_classes, so LR is ~3x usual.
OPTIMIZER = os.environ.get("OPTIMIZER", "gd")
if OPTIMIZER not in ("gd", "momentum", "adam"):
    raise ValueError(f"OPTIMIZER must be gd, momentum or adam, got {OPTIMIZER!r}")
LR = float(os.environ.get("LR", 1.0))
MOMENTUM = float(os.environ.get("MOMENTUM", 0.9))  # only used by OPTIMIZER=momentum
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", 256))
MAX_EPOCHS = int(os.environ.get("MAX_EPOCHS", 40))
EARLY_STOPPING_TOLERANCE = float(os.environ.get("EARLY_STOPPING_TOLERANCE", 1e-5))
