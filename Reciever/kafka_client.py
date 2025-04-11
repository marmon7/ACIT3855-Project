import json
import logging
import logging.config
import yaml
from pykafka import KafkaClient
from pykafka.exceptions import KafkaException

with open("log_conf.yaml", "r", encoding="utf-8") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('basicLogger')

class KafkaWrapper:
    def __init__(self, hosts="kafka:9092", topic_name="events"):
        self.hosts = hosts
        self.topic_name = topic_name
        self.client = None
        self.topic = None
        self.producer = None
        self._connect()

    def _connect(self):
        """Initialize Kafka client and producer"""
        try:
            logger.info(f"Connecting to Kafka at {self.hosts}")
            self.client = KafkaClient(hosts=self.hosts)
            self.topic = self.client.topics[self.topic_name.encode()]
            self.producer = self.topic.get_sync_producer()
            logger.info(f"Connected to Kafka topic: {self.topic_name}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self.client = None
            self.producer = None

    def send(self, message: dict):
        """Send a JSON message to Kafka"""
        if self.producer is None:
            logger.warning("Producer not initialized. Reconnecting...")
            self._connect()

        try:
            payload = json.dumps(message).encode("utf-8")
            self.producer.produce(payload)
            logger.debug(f"Sent message to Kafka: {message}")
        except KafkaException as e:
            logger.error(f"KafkaException while sending: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while sending to Kafka: {e}")

    def close(self):
        """Flush and close the producer"""
        if self.producer is not None:
            self.producer.stop()
            logger.info("Kafka producer closed.")