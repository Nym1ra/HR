from pydantic import BaseModel
from datetime import date

class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    role: str
    salary: float
    team: str
    hire_date: date

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase):
    id: int

    class Config:
        orm_mode = True
