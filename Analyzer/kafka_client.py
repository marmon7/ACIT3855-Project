import time
import logging
import logging.config
import yaml
from pykafka import KafkaClient
from pykafka.exceptions import KafkaException

with open("log_conf.yaml", "r", encoding="utf-8") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('basicLogger')

MAX_RETRIES = 5
RETRY_DELAY_SEC = 3

class KafkaWrapper:
    def __init__(self, hosts, topic_name, group=None, auto_commit=False):
        self.hosts = hosts
        self.topic_name = topic_name
        self.group = group
        self.auto_commit = auto_commit
        self.client = None
        self.consumer = None

    def connect(self):
        """Establish a connection to Kafka and get the consumer."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Connecting to Kafka ({self.hosts}), attempt {attempt}...")
                self.client = KafkaClient(hosts=self.hosts)
                topic = self.client.topics[self.topic_name]
                self.consumer = topic.get_simple_consumer(
                    consumer_group=self.group.encode("utf-8") if self.group else None,
                    auto_commit_enable=self.auto_commit,
                    reset_offset_on_start=True
                )
                logger.info(f"Connected to Kafka topic: {self.topic_name}")
                return
            except Exception as e:
                logger.warning(f"Kafka connection failed (attempt {attempt}): {e}")
                time.sleep(RETRY_DELAY_SEC)
        
        raise RuntimeError(f"Failed to connect to Kafka after {MAX_RETRIES} attempts")

    def messages(self):
        """Generator that yields messages from Kafka with reconnection logic."""
        if self.consumer is None:
            self.connect()

        while True:
            try:
                for message in self.consumer:
                    if message is not None:
                        yield message
            except KafkaException as e:
                logger.warning(f"Kafka error in consumer loop: {e}")
                self.client = None
                self.consumer = None
                self.connect()

    def commit(self):
        """Manually commit offsets if auto_commit is disabled."""
        if self.consumer and not self.auto_commit:
            try:
                self.consumer.commit_offsets()
            except Exception as e:
                logger.error(f"Failed to commit offsets: {e}")