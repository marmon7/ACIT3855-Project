import connexion
import json
import yaml
from datetime import datetime, timezone
from connexion import NoContent
import logging
import logging.config
from apscheduler.schedulers.background import BackgroundScheduler
import httpx
from statistics import mean
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
import os

with open('app_conf.yaml','r') as f:
    app_config = yaml.safe_load(f.read())

with open("log_conf.yaml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger('basicLogger')

#Get Request to generate a json object of the stats
def get_stats():
    logger.info("Stats request was received")
    try:
        with open(app_config['datastore']['filename'], 'r') as fp:
            stats = json.load(fp)
    except IOError:
        logger.error("Statistics do not exist")
        return NoContent, 400
    logger.debug(stats)
    logger.info("Stats request completed")
    return stats, 200

#Does the calculation of the statistics from storage
def populate_stats():
    logger.info("periodic processing has started")
    current_time = datetime.now(timezone.utc)

    #Read data.json if it exists if not create a stats dictionary with default values 
    try:
        with open(app_config['datastore']['filename'], 'r') as fp:
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
    activity_get = httpx.get(f"{app_config["eventstores"]["beach_activity"]["url"]}?start_timestamp={stats["last_update"]}&end_timestamp={current_time.replace(microsecond=0).isoformat().replace("+00:00", "Z")}")
    weather_get = httpx.get(f"{app_config["eventstores"]["beach_weather"]["url"]}?start_timestamp={stats["last_update"]}&end_timestamp={current_time.replace(microsecond=0).isoformat().replace("+00:00", "Z")}")
    
    #Check the status code from the GET requests log different message based on the result
    if (activity_get.status_code != 200) or (weather_get.status_code != 200):
        logger.error(f"Error with request event")
    else:
        logger.info(f"Number of events received for activity is {len(activity_get.json())} and for weather is {len(weather_get.json())}")
    
    #update the running total of summer activities with the number of new activities
    stats["num_summer_activities"] += len(activity_get.json())
    
    #update the running total of weather events with the number of new weather events
    stats["num_beach_conditions"] += len(weather_get.json())
    
    #convert last update string to datetime object for processing
    stats["last_update"] = datetime.fromisoformat(stats["last_update"])
    
    #Check if there is a new max temperature and update it if that's the case update the last update with the most recent event
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

    #creates a list of all the participants data to be used later for processing also update the last update with the most recent event    
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
    with open(app_config['datastore']['filename'], 'w') as fp:
            json.dump(stats,fp)

    logger.debug(f"num_summer_activities is {stats["num_summer_activities"]}, avg_participants is {stats["avg_participants"]}, num_beach_conditions is {stats["num_beach_conditions"]} and max_temperature is {stats["max_temperature"]}")
    logger.info("periodic processing has ended")

def init_scheduler():
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
    