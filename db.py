from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from contextlib import contextmanager
import os
from dotenv import load_dotenv



load_dotenv(override=True)

DATABASE_URL = os.environ["DATABASE_URL"]

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#connection setup --> open connection and run query
engine = create_engine(
    DATABASE_URL, # connect to this database
    pool_pre_ping=True, # check db connect before using db
    pool_recycle=300,
    connect_args={ #setting to be passed (secure connection)
        "ssl":{
            "ssl":True
        }
    }
)

SessionLocal = sessionmaker(bind = engine) # factory for new db session whenever required
Base = declarative_base() # to make tables using classes in python