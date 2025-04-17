import time
import random
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
    def __init__(self, hostname, topic):
        self.hostname = hostname
        self.topic = topic
        self.client = None
        self.producer = None
        self.connect()

    def connect(self):
        """Infinite loop: will keep trying"""
        while True:
            logger.debug("Trying to connect to Kafka...")
            if self.make_client():
                if self.make_producer():
                    break
        # Sleeps for a random amount of time (0.5 to 1.5s)
        time.sleep(random.randint(500, 1500) / 1000)

    def make_client(self):
        """
        Runs once, makes a client and sets it on the instance.
        Returns: True (success), False (failure)
        """
        if self.client is not None:
            return True
        try:
            self.client = KafkaClient(hosts=self.hostname)
            logger.info("Kafka client created!")
            return True
        except KafkaException as e:
            msg = f"Kafka error when making client: {e}"
            logger.warning(msg)
            self.client = None
            self.producer = None
            return False

    def make_producer(self):
        """
        Runs once, makes a producer and sets it on the instance.
        Returns: True (success), False (failure)
        """
        if self.producer is not None:
            return True
        if self.client is None:
            return False
        try:
            topic = self.client.topics[self.topic]
            self.producer = topic.get_sync_producer()
        except KafkaException as e:
            msg = f"Make error when making producer: {e}"
            logger.warning(msg)
            self.client = None
            self.producer = None
            return False
        
    def send(self, message):
        """Produce a message to Kafka, waiting for Kafka if necessary."""
        attempts = 0
        retries = 5
        while attempts < retries:
            if self.producer is None:
                self.connect()
            try:
                self.producer.produce(message.encode('utf-8'))
                logger.info("Message produced successfully")
                return True
            except KafkaException as e:
                logger.warning(f"Kafka error when producing message: {e}")
                self.client = None
                self.producer = None
                attempts += 1
                time.sleep(1.0)  # Wait before retry
        logger.error("Failed to produce message after retries")
        return False
