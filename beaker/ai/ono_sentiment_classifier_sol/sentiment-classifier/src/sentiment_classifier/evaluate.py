"""Evaluate the trained network on the held-out test split."""

import numpy as np
import scipy.sparse as sp
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from . import config as C
from .model import load_params, predict_proba


def run() -> None:
    x_te = sp.load_npz(C.TEST_SPARSE)
    y_te = np.load(C.TEST_Y)

    probs = predict_proba(load_params(), x_te)
    pred = probs.argmax(axis=1)
    print(f"accuracy: {accuracy_score(y_te, pred):.4f}  "
          f"macro-F1: {f1_score(y_te, pred, average='macro'):.4f}")
    print(classification_report(y_te, pred, target_names=C.CLASS_NAMES, digits=4))
    print("confusion matrix (rows = true, cols = predicted):")
    print(confusion_matrix(y_te, pred))

