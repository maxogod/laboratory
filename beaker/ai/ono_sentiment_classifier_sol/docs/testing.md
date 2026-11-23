# Testing

## Unit tests

`sentiment-classifier/tests/` needs neither Docker nor ONO. It covers the numpy forward pass against a hand-computed result,
safetensors loading with ONO's tensor names, sparse batching, and the packed little-endian `f32` layout the `.bin` writers produce.

```bash
PYTHONPATH=sentiment-classifier/src uv run --no-project \
  --with numpy --with scipy --with scikit-learn --with pandas --with joblib --with safetensors --with pytest \
  pytest sentiment-classifier/tests
```

The tests build their own safetensors, so they cannot detect a mismatch with ONO's real weight layout.

## Smoke test

`scripts/smoke_test.sh` runs the full stack on a small subset (10k rows, 500 features, 2 epochs): build, preprocess, train on the
3 nodes, then check that `sentiment.safetensors` and `loss_history.json` exist, the loss decreased, and `evaluate` accuracy is above chance.
It runs `docker compose down` on exit.

```bash
./scripts/smoke_test.sh
```

If the loss drops but accuracy stays at chance, suspect `model.py` (weight layout or activations) first.

## Learning-rate trial

`scripts/lr_trial.sh [lr ...]` trains on 60k rows for 10 epochs per learning rate and prints loss and per-class metrics. It writes only to
`data/trial` and `models/trial`, so the full data and model are untouched.

```bash
./scripts/lr_trial.sh 0.5 1.0 2.0
```
