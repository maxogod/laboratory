"""CSV -> TF-IDF features -> packed little-endian f32 files that ONO's LocalDataset reads."""

import json

import joblib
import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split

from . import config as C

CHUNK = 10_000


def _write_dense(matrix: sp.csr_matrix, path) -> None:
    """Write as packed little-endian f32, densifying in chunks to bound memory."""
    with open(path, "wb") as f:
        for start in range(0, matrix.shape[0], CHUNK):
            block = matrix[start : start + CHUNK].toarray().astype("<f4")
            f.write(block.tobytes())


def _write_onehot(y: np.ndarray, path) -> None:
    onehot = np.eye(C.N_CLASSES, dtype="<f4")[y]
    path.write_bytes(onehot.tobytes())


def run() -> None:
    C.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    C.MODELS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(C.RAW_CSV).dropna(subset=["Comment", "Sentiment"])
    df["Comment"] = df["Comment"].astype(str)
    df["Sentiment"] = df["Sentiment"].astype(int)
    if C.MAX_ROWS:
        df = df.sample(n=min(C.MAX_ROWS, len(df)), random_state=C.SEED)
    print(f"rows: {len(df)}")
    print(df["Sentiment"].value_counts().sort_index().to_string())

    # Split BEFORE fitting the vectorizer so no test information leaks into it.
    x_tr, x_te, y_tr, y_te = train_test_split(
        df["Comment"].to_numpy(),
        df["Sentiment"].to_numpy(),
        test_size=C.TEST_SIZE,
        stratify=df["Sentiment"],
        random_state=C.SEED,
    )

    vec = TfidfVectorizer(
        max_features=C.N_FEATURES, min_df=5, sublinear_tf=True, dtype=np.float32
    )
    xs_tr = vec.fit_transform(x_tr).tocsr()
    xs_te = vec.transform(x_te).tocsr()
    n_features = xs_tr.shape[1]
    print(f"features: {n_features}, train: {xs_tr.shape[0]}, test: {xs_te.shape[0]}")

    _write_dense(xs_tr, C.TRAIN_SAMPLES_BIN)
    _write_onehot(y_tr, C.TRAIN_LABELS_BIN)

    sp.save_npz(C.TEST_SPARSE, xs_te)
    np.save(C.TEST_Y, y_te)
    joblib.dump(vec, C.VECTORIZER)

    C.META.write_text(
        json.dumps({"n_features": n_features, "n_train": int(xs_tr.shape[0])}, indent=2)
    )
    print(f"wrote {C.TRAIN_SAMPLES_BIN} ({C.TRAIN_SAMPLES_BIN.stat().st_size / 1e9:.2f} GB)")
