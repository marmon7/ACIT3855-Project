"""Modules to run service"""
import json
import os
import logging
import logging.config
import yaml
import connexion
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
from kafka_client import KafkaWrapper

with open('app_conf.yaml','r', encoding="utf-8") as f:
    app_config = yaml.safe_load(f.read())

with open("log_conf.yaml", "r", encoding="utf-8") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('basicLogger')

kafka_wrapper = KafkaWrapper(f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}",app_config["events"]["topic"].encode())

def get_book_activity(index):
    """function to get booking activities"""
    logger.info("Book Activity search request was received")
    counter = 0
    status = 404
    payload = { "message": f"No message at index {index}!"}
    for msg in kafka_wrapper.messages():
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
    """function to get beach conditions"""
    logger.info("Beach Condition search request was received")
    counter = 0
    status = 404
    payload = { "message": f"No message at index {index}!"}
    for msg in kafka_wrapper.messages():
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
    """function to get stats"""
    logger.info("Event stats request recieved")
    logger.info("new commit info updated")

    counter_activity = 0
    counter_condition = 0
    for msg in kafka_wrapper.messages():
        print(msg)
        message = msg.value.decode("utf-8")
        data = json.loads(message)
        if data['type'] == 'beachactivity':
            counter_activity+=1

        if data['type'] == 'beachcondition':
            counter_condition+=1

    return {"num_summer_activities": counter_activity,
            "num_beach_conditions": counter_condition}, 200

def get_list_activity():
    """function to get stats"""
    logger.info("Event stats request recieved")
    logger.info("retriving list of activities")
    activity_list = []

    for msg in kafka_wrapper.messages():
        message = msg.value.decode("utf-8")
        data = json.loads(message)
        if data['type'] == 'beachactivity':
            activity = {
                    "event_id": data['payload']['booking_id'],
                    "trace_id": data['payload']['trace_id']
                }
            activity_list.append(activity)
    return activity_list, 200

def get_list_beach():
    """function to get stats"""
    logger.info("Event stats request recieved")
    logger.info("retriving list of activities")
    activity_list = []

    for msg in kafka_wrapper.messages():
        message = msg.value.decode("utf-8")
        data = json.loads(message)
        if data['type'] == 'beachcondition':
            activity = {
                    "event_id": data['payload']['Device_id'],
                    "trace_id": data['payload']['trace_id']
                }
            activity_list.append(activity)
    return activity_list, 200

            


app = connexion.FlaskApp(__name__, specification_dir='')
if "CORS_ALLOW_ALL" in os.environ and os.environ["CORS_ALLOW_ALL"] == "yes":
    app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.add_api("analyze.yaml", base_path="/analyzer", strict_validation=True, validate_responses=True)
if __name__ == "__main__":
    app.run(port=8110, host="0.0.0.0")
