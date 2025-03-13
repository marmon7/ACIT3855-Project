import connexion
import yaml
import time
from datetime import datetime
from connexion import NoContent
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

def book_Beach_activity(body):
    body["trace_id"] = time.time_ns()
    logger.info(f"Received event beach_activity with a trace id of {body["trace_id"]}")
    client = KafkaClient(hosts=f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}")
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    producer = topic.get_sync_producer()
    msg = { 
        "type": "beachactivity",
        "datetime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))
    logger.info(f"Response for event beach_activity (id: {body["trace_id"]}) has status 201")
    return NoContent, 201

def report_beach_conditions(body):
    body["trace_id"] = time.time_ns()
    logger.info(f"Received event beach_conditions with a trace id of {body["trace_id"]}")
    client = KafkaClient(hosts=f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}")
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    producer = topic.get_sync_producer()
    msg = { 
        "type": "beachcondition",
        "datetime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))
    logger.info(f"Response for event beach_weather (id: {body["trace_id"]}) has status 201")
    return NoContent, 201

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("SummerFun.yaml", strict_validation=True, validate_responses=True)
if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")