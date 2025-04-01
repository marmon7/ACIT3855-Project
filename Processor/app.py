"""Modules to run service"""
import json
from datetime import datetime, timezone
import logging
import logging.config
from statistics import mean
import os
import yaml
import connexion
from connexion import NoContent
from connexion.middleware import MiddlewarePosition
from apscheduler.schedulers.background import BackgroundScheduler
import httpx
from starlette.middleware.cors import CORSMiddleware

with open('app_conf.yaml','r', encoding="utf-8") as f:
    app_config = yaml.safe_load(f.read())

with open("log_conf.yaml", "r", encoding="utf-8") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('basicLogger')

#Get Request to generate a json object of the stats
def get_stats():
    """Gets the stats for both events"""
    logger.info("Stats request was received")
    try:
        with open(app_config['datastore']['filename'], 'r', encoding="utf-8") as fp:
            stats = json.load(fp)
    except IOError:
        logger.error("Statistics do not exist")
        return NoContent, 400
    logger.debug(stats)
    logger.info("Stats request completed")
    return stats, 200

#Does the calculation of the statistics from storage
def populate_stats():
    """populate stats on a schedule"""
    logger.info("periodic processing has started")
    current_time = datetime.now(timezone.utc)

    #Read data.json if it exists if not create a stats dictionary with default values
    try:
        with open(app_config['datastore']['filename'], 'r', encoding="utf-8") as fp:
            stats = json.load(fp)

    except IOError:
        stats = {
            "num_summer_activities": 0,
            "avg_participants": 0,
            "num_beach_conditions": 0,
            "max_temperature": 0,
            "last_update": "2016-08-29T09:12:33Z"
        }
    #Do GET requests to storage server to get statistics on events
    url_activity = app_config["eventstores"]["beach_activity"]["url"]
    url_weather = app_config["eventstores"]["beach_weather"]["url"]
    timestamp = current_time.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    activity_get = httpx.get(f"{url_activity}?start_timestamp={stats['last_update']}&end_timestamp={timestamp}")
    weather_get = httpx.get(f"{url_weather}?start_timestamp={stats["last_update"]}&end_timestamp={timestamp}")
    #Check the status code from the GET requests log different message based on the result
    if (activity_get.status_code != 200) or (weather_get.status_code != 200):
        logger.error("Error with request event")
    else:
        logger.info(
            "Number of events received for activity is %d and for weather is %d",
            len(activity_get.json()), len(weather_get.json())
            )
    #update the running total of summer activities with the number of new activities
    stats["num_summer_activities"] += len(activity_get.json())
    #update the running total of weather events with the number of new weather events
    stats["num_beach_conditions"] += len(weather_get.json())
    #convert last update string to datetime object for processing
    stats["last_update"] = datetime.fromisoformat(stats["last_update"])
    #Check if there is a new max temperature and update it if that's the case
    for weather in weather_get.json():
        if weather["Temperature"] > stats["max_temperature"]:
            stats["max_temperature"] = weather["Temperature"]
        if stats["last_update"] < datetime.fromisoformat(weather["date_created"]):
            stats["last_update"] = datetime.fromisoformat(weather["date_created"])
    #initialize avg_participants depending if its a default value or not
    if stats["avg_participants"] != 0:
        avg_numbers = [stats["avg_participants"]]
    else:
        avg_numbers = []
    #creates a list of all the participants data to be used later
    for activity in activity_get.json():
        avg_numbers.append(activity["participants"])
        if stats["last_update"] < datetime.fromisoformat(activity["date_created"]):
            stats["last_update"] = datetime.fromisoformat(activity["date_created"])
    #Calculate the avg partcipants based on the old value and including new values
    if len(avg_numbers) != 0:
        stats["avg_participants"] = round(mean(avg_numbers))
    #Convert last update to json readable string
    stats["last_update"] = stats["last_update"].isoformat().replace("+00:00", "Z")
    #Dump dictionary to data.json
    with open(app_config['datastore']['filename'], 'w', encoding="utf-8") as fp:
        json.dump(stats,fp)
    logger.debug(
    "num_summer_activities: %d, avg_participants: %.2f, num_beach_conditions: %d, max_temperature: %.2f",
    stats["num_summer_activities"], stats["avg_participants"], stats["num_beach_conditions"], stats["max_temperature"]
    )
    logger.info("periodic processing has ended")

def init_scheduler():
    """Initialize scheduler"""
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats,
    'interval',
    seconds=app_config['scheduler']['interval'])
    sched.start()

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("Stats.yaml", base_path="/processor", strict_validation=True, validate_responses=True)
if "CORS_ALLOW_ALL" in os.environ and os.environ["CORS_ALLOW_ALL"] == "yes":
    app.add_middleware(
    CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100, host="0.0.0.0")
