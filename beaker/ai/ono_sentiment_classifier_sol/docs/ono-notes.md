# ONO notes

What this project relies on in the `external/ono` submodule and where each fact comes from. Paths are relative to
`external/ono/`. **Code** means the source was read, **Docs** means a README or `docs/*.md` only, **Run** means observed.

| # | Fact | Source | Type |
|---|------|--------|------|
| 1 | Every machine runs the same `node` binary (`HOST`, `PORT`). A node's role (worker or server) is assigned at runtime by the spec the orchestrator sends. | `README.md`, `docker/gen_compose.py` | Docs, code |
| 2 | `orchestra-py` is a PyO3 module. The Python process is the orchestrator: `orchestrate(model, training)` returns a `Session`, `session.wait()` returns a `TrainedModel`. | `orchestra-py/README.md`, `local.py` | Docs, code |
| 3 | `all_reduce`: every address in `addrs` is a worker. `parameter_server` and `strategy_switch`: `nservers` of the addresses become servers, and `nservers < len(addrs)`. | `docs/config-schema.md`, `orchestra-py/README.md` | Docs |
| 4 | `strategy_switch` starts as all-reduce and switches to parameter server when relative loss improvement drops under an internal threshold that is not configurable from Python. | `orchestra-py/README.md` | Docs |
| 5 | `LocalDataset` reads packed little-endian `f32`, row-major, `x_size` / `y_size` values per row. `.csv` / `.tsv` are auto-converted, but only when numeric. | `orchestra-py/src/datasets.rs`, `orchestrator/src/lib.rs:30-45` | Code |
| 6 | The orchestrator reads the dataset and streams partitions to the nodes in chunks of 8,192. Nodes never read the data from disk. | `orchestrator/src/sessions/session.rs:456-520` | Code |
| 7 | `batch_size` is validated only against the total sample count. It is applied per worker: each worker shuffles and batches its own partition (`dataset.batches(batch_size)`). | `orchestrator/src/configs/validator.rs:193`, `machine_learning/src/training/backprop_trainer.rs` | Code |
| 8 | `CrossEntropy` expects probabilities: loss `-Σ y·ln(max(p, ε)) / n`, gradient `-(y/p) / n`, with `n = batch × classes`. The model must end in `Softmax` and labels must be one-hot. | `machine_learning/src/arch/loss/cross_entropy.rs` | Code |
| 9 | `save_safetensors` writes F32 tensors `layer_{i}.weight` (shape `[in, out]`) and `layer_{i}.bias` (shape `[out]`), one pair per layer. | `orchestrator/src/sessions/trained_model.rs:36-110` | Code |
| 10 | `TrainedModel` exposes `weights()`, `loss_history()` and `save_safetensors()`. There is no inference API. | `orchestra-py/README.md`, `orchestra-py/src/session.rs` | Docs, code |
| 11 | `Session.wait()` prints live progress: animated in a TTY, plain lines otherwise. | `orchestra-py/src/session.rs:45` | Code |
| 12 | The node image is a multi-stage `cargo-chef` build with `ARG MODE` (`release` / `debug`). The build context is the ONO root. | `node/Dockerfile` | Code |
| 13 | ONO's own compose generator uses `cpus: 1` per node and a bridge network. | `docker/gen_compose.py` | Code |
| 14 | `orchestui` needs an interactive terminal. The `orchestrator` crate's `main.rs` is a developer harness with a hardcoded model and MNIST paths. Neither is used here. | `orchestui/README.md`, `orchestrator/src/main.rs` | Code |
| 15 | A node exits when a connection closes before the handshake: `accept()` propagates the EOF with `?` up through `NodeRouter::run`. A plain TCP connect-and-close, such as a readiness probe, kills the node (`Error: ... UnexpectedEof, "early eof"`). | `node/src/router.rs`, `comms/src/connection/acceptor.rs:52` | Code, run |
| 16 | **Sync is per epoch.** Inside an epoch each worker takes a plain-SGD step per batch (`stateless_optimizers = GradientDescent::new(lr)`) and sums the batch gradients into `residual`. After the epoch the residual is all-reduced (averaged over workers) and the chosen optimizer is applied once to the global parameters. Adam therefore gets one step per epoch, while `GradientDescent` makes the global step the average of the workers' local-SGD updates. The parameter-server worker has the same per-round structure. | `backprop_trainer.rs`, `arch/sequential.rs:114`, `worker/src/workers/all_reduce.rs`, `worker_ring.rs` | Code, run |
| 17 | The reported `avg_loss` is cross-entropy divided by the number of classes, so chance for 3 classes is ln(3)/3 = 0.366. | `cross_entropy.rs` | Code |
| 18 | `Softmax::backward` is the correct Jacobian-vector product. `ReLU` forward is `max(x, slope·x)`. `ReLU::backward` sets `d = slope·a` instead of `slope·d` for non-positive activations, harmless at `slope = 0` but wrong for leaky ReLU. | `arch/layers/softmax.rs`, `relu.rs` | Code |

## Still unverified

- **Weight data layout.** The declared shape is `[in, out]` (#9), but the flat data layout was not checked. `model.py` assumes
  `y = x @ W + b`. Above-chance results from the smoke test and the first run are consistent with it, and a well-trained run will settle it.
- **Learning rate.** The suggested range for plain gradient descent comes from a scikit-learn simulation, not from ONO itself.
