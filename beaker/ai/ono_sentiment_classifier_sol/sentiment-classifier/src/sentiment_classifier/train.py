"""Orchestrates distributed training on the ONO node containers (all-reduce)."""

import json

from . import config as C


def run() -> None:
    # `orchestra` is only installed in the orchestrator image.
    from orchestra import Sequential, all_reduce, orchestrate
    from orchestra.activations import ReLU, Softmax
    from orchestra.arch import Dense
    from orchestra.datasets import LocalDataset
    from orchestra.initialization import Kaiming
    from orchestra.loss_fns import CrossEntropy
    from orchestra.optimizers import Adam, GradientDescent, GradientDescentWithMomentum

    meta = json.loads(C.META.read_text())
    acts = {"relu": lambda: ReLU(0.0), "softmax": Softmax}
    optimizers = {
        "gd": lambda: GradientDescent(lr=C.LR),
        "momentum": lambda: GradientDescentWithMomentum(lr=C.LR, mu=C.MOMENTUM),
        "adam": lambda: Adam(lr=C.LR),
    }
    model = Sequential([Dense(n, Kaiming(), acts[a]()) for n, a in C.LAYERS])

    training = all_reduce(
        addrs=C.NODE_ADDRS,
        dataset=LocalDataset(
            str(C.TRAIN_SAMPLES_BIN),
            str(C.TRAIN_LABELS_BIN),
            x_size=meta["n_features"],
            y_size=C.N_CLASSES,
        ),
        optimizer=optimizers[C.OPTIMIZER](),
        loss_fn=CrossEntropy(),
        max_epochs=C.MAX_EPOCHS,
        batch_size=C.BATCH_SIZE,
        seed=C.SEED,
        early_stopping_tolerance=C.EARLY_STOPPING_TOLERANCE,
    )

    print(f"optimizer={C.OPTIMIZER} lr={C.LR} batch={C.BATCH_SIZE} epochs<={C.MAX_EPOCHS} "
          f"early_stop_tol={C.EARLY_STOPPING_TOLERANCE}")
    print(f"training on {len(C.NODE_ADDRS)} workers, {meta['n_train']} samples")
    trained = orchestrate(model, training).wait()

    C.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    trained.save_safetensors(str(C.WEIGHTS))
    C.LOSS_HISTORY.write_text(json.dumps(trained.loss_history()))
    print(f"saved {C.WEIGHTS} and {C.LOSS_HISTORY}")
