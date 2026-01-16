from sqlalchemy import Column, Integer, String, Float
from src.Database.dataBase import Base

class Product(Base):
    __tablename__ = "product"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    quantity = Column(Integer)  