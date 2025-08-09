from sqlalchemy import Column, Integer, String, Float, Date
from database import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    role = Column(String)
    salary = Column(Float)
    team = Column(String)
    hire_date = Column(Date)
