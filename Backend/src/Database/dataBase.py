from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

## DB Configs
db_url = "postgresql://postgres:Password@localhost/UsersDB"
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)