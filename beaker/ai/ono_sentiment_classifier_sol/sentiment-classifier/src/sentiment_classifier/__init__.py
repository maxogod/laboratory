import argparse


def main() -> None:
    p = argparse.ArgumentParser(prog="sentiment-classifier")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("preprocess", help="CSV -> TF-IDF -> f32 binaries + test split")
    sub.add_parser("train", help="distributed training against the ONO nodes")
    sub.add_parser("evaluate", help="metrics on the held-out test split")
    pr = sub.add_parser("predict", help="classify raw text")
    pr.add_argument("text", nargs="+")
    args = p.parse_args()

    # Imports are lazy: `orchestra` exists only in the image, sklearn is not needed to train.
    if args.cmd == "preprocess":
        from . import preprocess
        preprocess.run()
    elif args.cmd == "train":
        from . import train
        train.run()
    elif args.cmd == "evaluate":
        from . import evaluate
        evaluate.run()
    else:
        from . import config as C
        from .model import predict_text
        for text, probs in zip(args.text, predict_text(args.text)):
            print(f"{C.CLASS_NAMES[int(probs.argmax())]:9s} {probs.round(3)}  {text}")
