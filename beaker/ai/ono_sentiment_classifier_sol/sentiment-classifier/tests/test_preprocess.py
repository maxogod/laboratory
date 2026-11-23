import numpy as np
import scipy.sparse as sp

from sentiment_classifier import config as C
from sentiment_classifier import preprocess


def test_write_dense_is_packed_little_endian_f32(tmp_path):
    m = sp.csr_matrix(np.array([[0, 1.5, 0], [2, 0, 3]], dtype=np.float32))
    path = tmp_path / "x.bin"
    preprocess._write_dense(m, path)
    raw = path.read_bytes()
    assert len(raw) == 2 * 3 * 4
    np.testing.assert_array_equal(np.frombuffer(raw, dtype="<f4").reshape(2, 3), m.toarray())


def test_write_dense_spans_multiple_chunks(tmp_path, monkeypatch):
    monkeypatch.setattr(preprocess, "CHUNK", 2)
    dense = np.arange(15, dtype=np.float32).reshape(5, 3)
    path = tmp_path / "x.bin"
    preprocess._write_dense(sp.csr_matrix(dense), path)
    np.testing.assert_array_equal(np.frombuffer(path.read_bytes(), "<f4").reshape(5, 3), dense)


def test_write_onehot(tmp_path):
    path = tmp_path / "y.bin"
    preprocess._write_onehot(np.array([0, 2, 1]), path)
    got = np.frombuffer(path.read_bytes(), "<f4").reshape(3, C.N_CLASSES)
    np.testing.assert_array_equal(got, np.eye(3, dtype=np.float32)[[0, 2, 1]])
