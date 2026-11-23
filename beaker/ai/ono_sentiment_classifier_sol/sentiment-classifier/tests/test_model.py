import numpy as np
import pytest
from safetensors.numpy import save_file

from sentiment_classifier import config as C
from sentiment_classifier import model


def _random_params(n_in: int, seed: int = 0):
    rng = np.random.default_rng(seed)
    params, prev = [], n_in
    for out, _ in C.LAYERS:
        params.append((rng.normal(size=(prev, out)).astype(np.float32),
                       rng.normal(size=(out,)).astype(np.float32)))
        prev = out
    return params


def test_forward_matches_manual_computation():
    params = _random_params(5)
    x = np.random.default_rng(1).normal(size=(4, 5)).astype(np.float32)

    h = x
    for (w, b), (_, act) in zip(params, C.LAYERS):
        h = h @ w + b
        if act == "relu":
            h = np.maximum(h, 0)
    expected = np.exp(h - h.max(1, keepdims=True))
    expected /= expected.sum(1, keepdims=True)

    np.testing.assert_allclose(model.forward(params, x), expected, rtol=1e-5)


def test_output_is_probability_distribution():
    out = model.forward(_random_params(7), np.ones((3, 7), np.float32))
    assert out.shape == (3, C.N_CLASSES)
    np.testing.assert_allclose(out.sum(axis=1), 1.0, rtol=1e-5)
    assert (out >= 0).all()


def test_load_params_uses_ono_tensor_names(tmp_path):
    params = _random_params(6)
    tensors = {}
    for i, (w, b) in enumerate(params):
        tensors[f"layer_{i}.weight"] = w
        tensors[f"layer_{i}.bias"] = b
    path = tmp_path / "m.safetensors"
    save_file(tensors, str(path))

    loaded = model.load_params(path)
    assert len(loaded) == len(C.LAYERS)
    for (w, b), (lw, lb) in zip(params, loaded):
        np.testing.assert_array_equal(w, lw)
        np.testing.assert_array_equal(b, lb)


def test_predict_proba_accepts_sparse_in_batches():
    import scipy.sparse as sp
    params = _random_params(8)
    dense = np.random.default_rng(2).random((10, 8)).astype(np.float32)
    out = model.predict_proba(params, sp.csr_matrix(dense), batch=3)
    np.testing.assert_allclose(out, model.forward(params, dense), atol=1e-5)
