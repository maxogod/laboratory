import argparse

from pub_sub.base import BaseWorker
from pub_sub.pub import PubWorker
from pub_sub.sub import SubWorker

common_conf = {
    "bootstrap.servers": "kafka:9092",
}

producer_conf = {
    **common_conf,
}

consumer_conf = {
    **common_conf,
    "group.id": "mygroup",
}


def main():
    parser = argparse.ArgumentParser(prog="pub-sub")

    parser.add_argument("role", choices=["publisher", "subscriber"])
    parser.add_argument("--topic", default="events")

    args = parser.parse_args()
    print(f"Arguments: {args}")

    worker: BaseWorker | None = None
    match args.role:
        case "publisher":
            worker = PubWorker(args.topic, producer_conf)
        case "subscriber":
            worker = SubWorker(args.topic, consumer_conf)

    if worker:
        print("Starting worker")
        worker.run()
    else:
        raise Exception("No worker configuration")
