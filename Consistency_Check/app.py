"""Modules to run service"""
import json
import os
import logging
import logging.config
import yaml
import time
import jsonify
from datetime import datetime, timezone
import httpx
import connexion

with open('app_conf.yaml','r', encoding="utf-8") as f:
    app_config = yaml.safe_load(f.read())

with open("log_conf.yaml", "r", encoding="utf-8") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('basicLogger')

def run_consistency_checks():
    start_time = time.time()
    logging.info("Update process started.")

    pro_data = httpx.get(app_config['pro_url'])
    stor_data = httpx.get(f"{app_config['stor_url']}/count")
    ana_data = httpx.get(f"{app_config['ana_url']}/stats")
    stor_list_activity = httpx.get(f"{app_config['stor_url']}/get_list_activity")
    stor_list_beach = httpx.get(f"{app_config['stor_url']}/get_list_beach")
    ana_list_activity = httpx.get(f"{app_config['ana_url']}/get_list_activity")
    ana_list_beach = httpx.get(f"{app_config['ana_url']}/get_list_beach")
    stor_list_activity_set = set(stor_list_activity.items())
    ana_list_activity_set = set(ana_list_activity.items())
    stor_list_beach_set = set(stor_list_beach.items())
    ana_list_beach_set = set(ana_list_beach.items())
    events = ["activity", "beach"]
    # Create a new set with the added event info
    not_in_db_activity = {(*t, e) for t, e in zip(ana_list_activity_set-stor_list_activity_set, events[0])}
    not_in_queue_activity = {(*t, e) for t, e in zip(stor_list_activity_set-ana_list_activity_set, events[0])}
    not_in_db_beach = {(*t, e) for t, e in zip(ana_list_beach_set-stor_list_beach_set, events[1])}
    not_in_queue_beach = {(*t, e) for t, e in zip(stor_list_beach_set-ana_list_beach_set, events[1])}
    not_in_db_activity_list = [{"event_id": event_id, "trace_id": trace_id, "event_type": event_type} for event_id, trace_id, event_type in not_in_db_activity]
    not_in_queue_activity_list = [{"event_id": event_id, "trace_id": trace_id, "event_type": event_type} for event_id, trace_id, event_type in not_in_queue_activity]
    not_in_db_beach_list = [{"event_id": event_id, "trace_id": trace_id, "event_type": event_type} for event_id, trace_id, event_type in not_in_db_beach]
    not_in_queue_beach_list = [{"event_id": event_id, "trace_id": trace_id, "event_type": event_type} for event_id, trace_id, event_type in not_in_queue_beach]
    not_in_db_list = not_in_db_activity_list + not_in_db_beach_list
    not_in_queue_list = not_in_queue_activity_list + not_in_queue_beach_list

    updated_data = {
        "last_updated": datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z",
        "counts": {
            "db": stor_data,
            "queue": ana_data,
            "processing": pro_data
        },
        "not_in_db": not_in_db_list,
        "not in_queue" : not_in_queue_list
    }
    with open(app_config['filename'], 'w', encoding="utf-8") as fp:
        json.dump(updated_data,fp)
    
    duration = (time.time() - start_time) * 1000
    missing_in_db = len(updated_data["not_in_db"])
    missing_in_queue = len(updated_data["not_in_queue"])
    logging.info(f"Consistency checks completed | processing_time_ms={duration:.2f} | missing_in_db = {missing_in_db} | missing_in_queue = {missing_in_queue}")

def get_checks():
    if os.path.exists(app_config['filename']):
        with open(app_config['filename'], 'r') as file:
            check_results = json.load(file)
        return jsonify(check_results), 200
    else:
        return jsonify({"message": "No consistency checks have been run yet."}), 404

app = connexion.FlaskApp(__name__, specification_dir='')

app.add_api("analyze.yaml", base_path="/analyzer", strict_validation=True, validate_responses=True)
if __name__ == "__main__":
    app.run(port=8110, host="0.0.0.0")