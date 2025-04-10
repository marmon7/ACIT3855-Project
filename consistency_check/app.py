"""Modules to run service"""
import json
import os
import logging
import logging.config
import yaml
import time
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

    pro_data = httpx.get(app_config['pro_url']).json()
    stor_data = httpx.get(f"{app_config['stor_url']}/count").json()
    ana_data = httpx.get(f"{app_config['ana_url']}/stats").json()
    stor_list_activity = httpx.get(f"{app_config['stor_url']}/get_list_activity")
    stor_list_beach = httpx.get(f"{app_config['stor_url']}/get_list_beach")
    ana_list_activity = httpx.get(f"{app_config['ana_url']}/get_list_activity")
    ana_list_beach = httpx.get(f"{app_config['ana_url']}/get_list_beach")
    stor_list_activity_set = set((event["event_id"], event["trace_id"]) for event in stor_list_activity.json())
    ana_list_activity_set = set((event["event_id"], event["trace_id"]) for event in stor_list_beach.json())
    stor_list_beach_set = set((event["event_id"], event["trace_id"]) for event in ana_list_activity.json())
    ana_list_beach_set = set((event["event_id"], event["trace_id"]) for event in ana_list_beach.json())
    diff_queue_activity = ana_list_activity_set - stor_list_activity_set
    diff_db_activity = stor_list_activity_set-ana_list_activity_set
    diff_queue_beach = ana_list_beach_set-stor_list_beach_set
    diff_db_beach = stor_list_beach_set-ana_list_beach_set
    events = ["activity", "beach"]
    # Create a new set with the added event info
    not_in_db_activity = {(*t, events[0]) for t in diff_queue_activity}
    not_in_queue_activity = {(*t, events[0]) for t in diff_db_activity}
    not_in_db_beach = {(*t, events[1]) for t in diff_db_beach}
    not_in_queue_beach = {(*t, events[1]) for t in diff_queue_beach}
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
            "queue": {
                "BookActivity": ana_data['num_summer_activities'],
                "BeachConditions": ana_data['num_beach_conditions']
            },
            "processing": {
                "BookActivity": pro_data['num_summer_activities'],
                "BeachConditions": pro_data['num_beach_conditions']
            }
        },
        "not_in_db": not_in_db_list,
        "not_in_queue" : not_in_queue_list
    }
    with open(app_config['filename'], 'w', encoding="utf-8") as fp:
        json.dump(updated_data,fp)
    
    duration = (time.time() - start_time) * 1000
    missing_in_db = len(updated_data["not_in_db"])
    missing_in_queue = len(updated_data["not_in_queue"])
    logging.info(f"Consistency checks completed | processing_time_ms={duration:.2f} | missing_in_db = {missing_in_db} | missing_in_queue = {missing_in_queue}")

def get_checks():
    logger.info("Show Consistency data")
    if os.path.exists(app_config['filename']):
        with open(app_config['filename'], 'r') as file:
            check_results = json.load(file)
        return check_results, 200
    else:
        logger.error("failed to find data.json")
        return {"message": "No consistency checks have been run yet."}, 404

app = connexion.FlaskApp(__name__, specification_dir='')

app.add_api("consistency_check.yaml", base_path="/consistency", strict_validation=True, validate_responses=True)
if __name__ == "__main__":
    app.run(port=8120, host="0.0.0.0")