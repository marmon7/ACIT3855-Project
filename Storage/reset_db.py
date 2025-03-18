from sqlalchemy import create_engine
import yaml
from create_engine import Base

with open('app_conf.yaml', 'r') as f:
    app_config = yaml.safe_load(f.read())

def reset():
    engine = create_engine(f"mysql://{app_config["datastore"]["user"]}:{app_config["datastore"]["password"]}@{app_config["datastore"]["hostname"]}/{app_config["datastore"]["db"]}")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    reset()