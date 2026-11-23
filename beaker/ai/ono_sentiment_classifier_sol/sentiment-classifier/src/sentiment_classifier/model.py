"""Numpy forward pass over the safetensors written by ONO, which has no inference API."""

import joblib
import numpy as np
from safetensors.numpy import load_file

from . import config as C


def load_params(path=C.WEIGHTS) -> list[tuple[np.ndarray, np.ndarray]]:
    tensors = load_file(str(path))
    # ONO stores dense weights as [in, out]: y = x @ W + b.
    return [(tensors[f"layer_{i}.weight"], tensors[f"layer_{i}.bias"]) for i in range(len(C.LAYERS))]


def forward(params, x: np.ndarray) -> np.ndarray:
    for (w, b), (_, act) in zip(params, C.LAYERS):
        x = x @ w + b
        if act == "relu":
            x = np.maximum(x, 0.0)
        elif act == "softmax":
            x = np.exp(x - x.max(axis=1, keepdims=True))
            x /= x.sum(axis=1, keepdims=True)
    return x


def predict_proba(params, xs, batch: int = 4096) -> np.ndarray:
    """`xs` is a scipy sparse matrix or dense array; densified in batches."""
    out = []
    for s in range(0, xs.shape[0], batch):
        block = xs[s : s + batch]
        block = block.toarray() if hasattr(block, "toarray") else block
        out.append(forward(params, block.astype(np.float32)))
    return np.vstack(out)


def predict_text(texts: list[str]) -> np.ndarray:
    vec = joblib.load(C.VECTORIZER)
    return predict_proba(load_params(), vec.transform(texts))
