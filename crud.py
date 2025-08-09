from sqlalchemy.orm import Session
import models, schemas

def get_employees(db: Session):
    return db.query(models.Employee).all()

def get_employee(db: Session, emp_id: int):
    return db.query(models.Employee).filter(models.Employee.id == emp_id).first()

def create_employee(db: Session, emp: schemas.EmployeeCreate):
    db_emp = models.Employee(**emp.dict())
    db.add(db_emp)
    db.commit()
    db.refresh(db_emp)
    return db_emp

def update_employee(db: Session, emp_id: int, emp: schemas.EmployeeCreate):
    db_emp = get_employee(db, emp_id)
    if not db_emp:
        return None
    for key, value in emp.dict().items():
        setattr(db_emp, key, value)
    db.commit()
    db.refresh(db_emp)
    return db_emp

def delete_employee(db: Session, emp_id: int):
    db_emp = get_employee(db, emp_id)
    if not db_emp:
        return None
    db.delete(db_emp)
    db.commit()
    return db_emp
