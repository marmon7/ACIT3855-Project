import connexion
import yaml
import logging
import logging.config
from pykafka import KafkaClient
import json

with open('app_conf.yaml','r') as f:
    app_config = yaml.safe_load(f.read())

with open("log_conf.yaml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('basicLogger')

def get_book_activity(index):
    logger.info("Book Activity search request was received")
    hostname = f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}" # localhost:9092
    client = KafkaClient(hosts=hostname)
    topic = client.topics[app_config["events"]["topic"].encode()]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    counter = 0
    status = 404
    payload = { "message": f"No message at index {index}!"}
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)
        if data['type'] == 'beachactivity':
            if counter == index:
                payload = data["payload"]
                status = 200
            counter+=1
    if payload == { "message": f"No message at index {index}!"}:
        logger.error(f"No message at index {index}")
    return payload, status

def get_beach_condition(index):
    logger.info("Beach Condition search request was received")
    hostname = f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}" # localhost:9092
    client = KafkaClient(hosts=hostname)
    topic = client.topics[app_config["events"]["topic"].encode()]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    counter = 0
    status = 404
    payload = { "message": f"No message at index {index}!"}
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)
        if data['type'] == 'beachcondition':
            if counter == index:
                payload = data["payload"]
                status = 200
            counter+=1
    if payload == { "message": f"No message at index {index}!"}:
        logger.error(f"No message at index {index}")

    return payload, status


def get_event_stats():
    logger.info("EVent stats request recieved")
    hostname = f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}" # localhost:9092
    client = KafkaClient(hosts=hostname)
    topic = client.topics[app_config["events"]["topic"].encode()]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)

    counter_activity = 0
    counter_condition = 0
    
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)
        if data['type'] == 'beachactivity':
            counter_activity+=1

        if data['type'] == 'beachcondition':
            counter_condition+=1

    return {"num_summer_activities": counter_activity,"num_beach_conditions": counter_condition}, 200

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("analyze.yaml", strict_validation=True, validate_responses=True)
if __name__ == "__main__":
    app.run(port=8110, host="0.0.0.0")