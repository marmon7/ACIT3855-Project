import connexion
import yaml
from datetime import datetime
from connexion import NoContent
from create_engine import BeachConditions,BookActivity,make_session
import functools
import logging
import logging.config
from sqlalchemy import select,create_engine
from pykafka import KafkaClient
import json
from pykafka.common import OffsetType
from threading import Thread
from create_engine import Base

with open('app_conf.yaml','r') as f:
    app_config = yaml.safe_load(f.read())

with open("log_conf.yaml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('basicLogger')

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
    hostname = f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}" # localhost:9092
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    # Create a consume on a consumer group, that only reads new messages
    # (uncommitted messages) when the service re-starts (i.e., it doesn't
    # read all the old messages from the history in the message queue).
    consumer = topic.get_simple_consumer(consumer_group=b'event_group',
    reset_offset_on_start=False,
    auto_offset_reset=OffsetType.LATEST)
    # This is blocking - it will wait for a new message
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)
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
        consumer.commit_offsets()

def setup_kafka_thread():
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()

def create_tables():
    engine = create_engine(f"mysql://{app_config["datastore"]["user"]}:{app_config["datastore"]["password"]}@{app_config["datastore"]["hostname"]}/{app_config["datastore"]["db"]}")
    Base.metadata.create_all(engine)

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("SummerFun.yaml", strict_validation=True, validate_responses=True)
if __name__ == "__main__":
    create_tables()
    setup_kafka_thread()
    app.run(port=8090, host="0.0.0.0")