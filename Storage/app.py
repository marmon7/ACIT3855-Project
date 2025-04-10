"""Modules to run service"""
import json
from datetime import datetime
import logging
import logging.config
import functools
from threading import Thread
import yaml
import connexion
from sqlalchemy import select,create_engine,func
from create_engine import BeachConditions,BookActivity,make_session
from create_engine import Base
from .kafka_client import KafkaWrapper

with open('app_conf.yaml','r', encoding="utf-8") as f:
    app_config = yaml.safe_load(f.read())

with open("log_conf.yaml", "r", encoding="utf-8") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('basicLogger')

kafka_wrapper = KafkaWrapper(f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}",app_config["events"]["topic"].encode())

def get_activity_stats(start_timestamp, end_timestamp):
    session = make_session()
    start = datetime.fromisoformat(start_timestamp)
    end = datetime.fromisoformat(end_timestamp)
    statement = select(BookActivity).where(BookActivity.date_created > start).where(BookActivity.date_created < end)
    results = [
        result.to_dict()
        for result in session.execute(statement).scalars().all()
    ]
    session.close()
    logger.info("Found %d Activity Events (start: %s, end: %s)", len(results), start, end)
    return results

def get_weather_stats(start_timestamp, end_timestamp):
    session = make_session()
    start = datetime.fromisoformat(start_timestamp)
    end = datetime.fromisoformat(end_timestamp)
    statement = select(BeachConditions).where(BeachConditions.date_created > start).where(BeachConditions.date_created < end)
    results = [
        result.to_dict()
        for result in session.execute(statement).scalars().all()
    ]
    session.close()
    logger.info("Found %d Beach Weather (start: %s, end: %s)", len(results), start, end)
    return results

def get_counts():
    # Count the number of entries in the BookActivity table
    session = make_session()
    bookactivity_count = session.query(func.count(BookActivity.id)).scalar()

    # Count the number of entries in the BeachConditions table
    beachconditions_count = session.query(func.count(BeachConditions.id)).scalar()

    # Return the counts as a JSON response
    return {
        "BookActivity": bookactivity_count,
        "BeachConditions": beachconditions_count
    }, 200

def get_list_activity():
    session = make_session()
    events = session.query(BookActivity.booking_id, BookActivity.trace_id).all()
    results = [{"event_id": event.booking_id, "trace_id": event.trace_id} for event in events]
    session.close()
    logger.info("finished getting all activities")
    return results, 200

def get_list_beach():
    session = make_session()
    events = session.query(BeachConditions.device_id, BeachConditions.trace_id).all()
    results = [{"event_id": event.device_id, "trace_id": event.trace_id} for event in events]
    session.close()
    logger.info("finished getting all beach conditions")
    return results, 200


def use_db_session(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = make_session()
        try:
            return func(session, *args, **kwargs)
        finally:
            session.close()
    return wrapper

def process_messages():
    """ Process event messages """
    for msg in kafka_wrapper.messages():
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s", msg)
        payload = msg["payload"]
        if msg["type"] == "beachcondition": # Change this to your event type
            # Store the event1 (i.e., the payload) to the DB
            session = make_session()
            event = BeachConditions(
                beach_id = payload['Beach_id'],
                device_id = payload['Device_id'],
                temperature = payload['Temperature'],
                timestamp = datetime.fromisoformat(payload['timestamp']),
                wave_height = payload['Wave Height'],
                trace_id = payload["trace_id"]
            )
            session.add(event)
            session.commit()
            session.close()
            logger.debug(f"Stored event beach_condition with a trace id of {payload["trace_id"]}")

        elif msg["type"] == "beachactivity": # Change this to your event type
            # Store the event2 (i.e., the payload) to the DB
            # Commit the new message as being read
            session = make_session()
            event = BookActivity(
                booking_id = payload['booking_id'],
                activity_id = payload['activity_id'],
                participants = payload['participants'],
                booking_time = datetime.fromisoformat(payload['booking_time']),
                beach_id = payload['Beach_id'],
                trace_id = payload["trace_id"]
                )
            session.add(event)
            session.commit()
            session.close()
            logger.debug(f"Stored event beach_activity with a trace id of {payload["trace_id"]}")
        kafka_wrapper.consumer.commit_offsets()

def setup_kafka_thread():
    t1 = Thread(target=process_messages)
    t1.daemon = True
    t1.start()

def create_tables():
    engine = create_engine(f"mysql://{app_config["datastore"]["user"]}:{app_config["datastore"]["password"]}@{app_config["datastore"]["hostname"]}/{app_config["datastore"]["db"]}")
    Base.metadata.create_all(engine)

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("SummerFun.yaml", base_path="/storage", strict_validation=True, validate_responses=True)
if __name__ == "__main__":
    create_tables()
    setup_kafka_thread()
    app.run(port=8090, host="0.0.0.0")
