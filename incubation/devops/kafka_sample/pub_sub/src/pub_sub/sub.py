import time

from confluent_kafka import Consumer

from pub_sub.base import BaseWorker


class SubWorker(BaseWorker):
    def __init__(self, topic: str | None, kafka_conf):
        if not topic:
            raise ValueError("Nu-uh")
        self.topic = topic
        self.c = Consumer(kafka_conf)
        self.c.subscribe(topics=[topic])

    def run(self):
        while True:
            msg = self.c.poll(timeout=1)
            if msg and not msg.error():
                val = msg.value()
                print(f"Received: '{val.decode() if val else 'Undecodable message'}'")
            elif msg and msg.error():
                print("Error receiving")
            time.sleep(2)
