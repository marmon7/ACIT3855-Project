"""Modules to run service"""
import time
from datetime import datetime
import json
import logging
import logging.config
import yaml
import connexion
from connexion import NoContent
from kafka_client import KafkaWrapper

with open('app_conf.yaml','r', encoding="utf-8") as f:
    app_config = yaml.safe_load(f.read())

with open("log_conf.yaml", "r", encoding="utf-8") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('basicLogger')

kafka_wrapper = KafkaWrapper(f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}",app_config["events"]["topic"])

def book_beach_activity(body):
    """Sends Payload to kafka for a beach activity event"""
    body["trace_id"] = time.time_ns()
    logger.info("Received event beach_activity with a trace id of %s", body["trace_id"])
    msg = {
        "type": "beachactivity",
        "datetime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body
    }
    kafka_wrapper.send(msg)
    logger.info("Response for event beach_activity (id: %s) has status 201", body["trace_id"])
    kafka_wrapper.close()
    return NoContent, 201

def report_beach_conditions(body):
    """Send Payload to kafka for a beach condition"""
    body["trace_id"] = time.time_ns()
    logger.info("Received event beach_conditions with a trace id of %s", body["trace_id"])
    msg = {
        "type": "beachcondition",
        "datetime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body
    }
    kafka_wrapper.send(msg)
    logger.info("Response for event beach_weather (id: %s) has status 201", body["trace_id"])
    kafka_wrapper.close()
    return NoContent, 201

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("SummerFun.yaml",base_path="/receiver", strict_validation=True, validate_responses=True)
if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")
