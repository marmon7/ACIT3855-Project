"""Modules to run service"""
import json
import time
import os
import logging
import logging.config
import yaml
import connexion
from pykafka import KafkaClient
from connexion import NoContent

with open('app_conf.yaml','r', encoding="utf-8") as f:
    app_config = yaml.safe_load(f.read())

with open("log_conf.yaml", "r", encoding="utf-8") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('basicLogger')

def update_anomalies():
    start_time = time.time()
    logging.debug("Update process started.")
    hostname = f"{app_config["events"]["hostname"]}:{app_config["events"]["port"]}" # localhost:9092
    client = KafkaClient(hosts=hostname)
    logger.info("Event stats request recieved")
    topic = client.topics[app_config["events"]["topic"].encode()]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    anomalies = []
    for msg in consumer:
        anomaly={}
        message = msg.value.decode("utf-8")
        data = json.loads(message)
        if data['type'] == 'beachactivity':
            if data['payload']['participants'] >= int(os.getenv("PARTICIPANTS_MAX")):
                anomaly.update({
                    'event_id': data['payload']['booking_id'],
                    'trace_id': data['payload']['trace_id'],
                    'event_type': 'activity',
                    'anomaly_type': f"participants over {os.getenv("PARTICIPANTS_MAX")}"
                })
                anomalies.append(anomaly)
                logger.debug(f"Activity anomaly found particpants is {data['payload']['participants']} over {os.getenv("PARTICIPANTS_MAX")}")

        if data['type'] == 'beachcondition':
            if data['payload']['Wave Height'] >= int(os.getenv("WAVE_HEIGHT_MAX")):
                anomaly.update({
                    'event_id': data['payload']['device_id'],
                    'trace_id': data['payload']['trace_id'],
                    'event_type': 'beach',
                    'anomaly_type': f"Wave height over {os.getenv("WAVE_HEIGHT_MAX")} meters"
                })
                anomalies.append(anomaly)
                logger.debug(f"Beach anomaly found wave height is {data['payload']['Wave Height']} over {os.getenv("WAVE_HEIGHT_MAX")}")

    with open(app_config['filename'], 'w', encoding="utf-8") as fp:
        json.dump(anomalies,fp)
    duration = (time.time() - start_time) * 1000
    logging.info(f"Anomaly checks completed | processing_time_ms={duration:.2f}")
    return {'num_of_anomalies': len(anomalies)}, 200

def get_anomalies(event=None):
    logger.debug("Anomaly request recieved")
    if (event != 'beach') or (event != 'activity'):
        return NoContent, 400
    if os.path.exists(app_config['filename']):
        with open(app_config['filename'], 'r') as file:
            anomalies = json.load(file)
        if anomalies == {}:
            return NoContent, 204
        if event == None:
            logger.debug("anomalies response returned")
            return anomalies, 200
        filtered_anomalies = []
        for anomaly in anomalies:
            if anomaly['event_type'] == event:
                filtered_anomalies.append(anomaly)
        logger.debug("anomalies response returned")
        return filtered_anomalies, 200

    else:
        logger.error("failed to find data.json")
        return {"message": "No anomaly checks have been run yet."}, 404

app = connexion.FlaskApp(__name__, specification_dir='')

app.add_api("anomaly.yaml", base_path="/anomaly", strict_validation=True, validate_responses=True)
if __name__ == "__main__":
    logger.info(f"Wave Height Max: {os.getenv("WAVE_HEIGHT_MAX")}, Paricipants max: {os.getenv("PARTICIPANTS_MAX")}")
    app.run(port=8130, host="0.0.0.0")