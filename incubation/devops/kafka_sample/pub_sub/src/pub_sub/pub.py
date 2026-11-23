import time

from confluent_kafka import Producer

from pub_sub.base import BaseWorker


class PubWorker(BaseWorker):
    def __init__(self, topic: str | None, kafka_conf):
        if not topic:
            raise ValueError("Nu-uh")
        self.topic = topic
        self.p = Producer(kafka_conf)

    def run(self):
        id = 1
        while True:
            msg = f"Message number {id}"
            print(f"Sending '{msg}'")
            self.p.produce(self.topic, msg.encode())
            self.p.flush(timeout=1)
            time.sleep(1)
            id += 1
