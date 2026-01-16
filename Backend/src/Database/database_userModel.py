from sqlalchemy import Column, Integer, String, Boolean
from src.Database.dataBase import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)