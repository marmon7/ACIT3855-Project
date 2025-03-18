from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import yaml

with open('app_conf.yaml','r') as f:
    app_config = yaml.safe_load(f.read())

engine = create_engine(f"mysql://{app_config["datastore"]["user"]}:{app_config["datastore"]["password"]}@{app_config["datastore"]["hostname"]}/{app_config["datastore"]["db"]}")
def make_session():
    return sessionmaker(bind=engine)()

from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, DateTime, func, BigInteger

class Base(DeclarativeBase):
    pass

class BeachConditions(Base):
    __tablename__ = "Beach_Report"
    id = mapped_column(Integer, primary_key=True)
    device_id = mapped_column(String(50), nullable=False)
    beach_id = mapped_column(String(50), nullable=False)
    temperature = mapped_column(Integer, nullable=False)
    timestamp = mapped_column(DateTime, nullable=False)
    wave_height = mapped_column(Integer, nullable=False)
    trace_id = mapped_column(BigInteger, nullable=False)
    date_created = mapped_column(DateTime, nullable=False, default=func.now())

    def to_dict(self):
        """ Dictionary Representation of a heart rate reading """
        dict = {}
        dict['id'] = self.id
        dict['Device_id'] = self.device_id
        dict['Beach_id'] = self.beach_id
        dict['Temperature'] = self.temperature
        dict['timestamp'] = self.timestamp
        dict['Wave Height'] = self.wave_height
        dict['trace_id'] = self.trace_id
        dict['date_created'] = self.date_created
        return dict

class BookActivity(Base):
    __tablename__ = "Activity_Booking"
    id = mapped_column(Integer, primary_key=True)
    booking_id = mapped_column(String(50), nullable=False)
    activity_id = mapped_column(String(50), nullable=False)
    participants = mapped_column(Integer, nullable=False)
    booking_time = mapped_column(DateTime, nullable=False)
    beach_id = mapped_column(String(50), nullable=False)
    trace_id = mapped_column(BigInteger, nullable=False)
    date_created = mapped_column(DateTime, nullable=False, default=func.now())

    def to_dict(self):
        """ Dictionary Representation of a heart rate reading """
        dict = {}
        dict['id'] = self.id
        dict['booking_id'] = self.booking_id
        dict['Beach_id'] = self.beach_id
        dict['participants'] = self.participants
        dict['booking_time'] = self.booking_time
        dict['activity_id'] = self.activity_id
        dict['trace_id'] = self.trace_id
        dict['date_created'] = self.date_created
        return dict
    