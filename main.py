from fastapi import FastAPI, Depends, Request, Form, Body, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import requests
import os
from dotenv import load_dotenv

import models, schemas, crud
from database import engine, Base, get_db

# --- Загружаем переменные окружения ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# --- Создаём таблицы ---
Base.metadata.create_all(bind=engine)

# --- Инициализация FastAPI ---
app = FastAPI(title="HR Система с ИИ")

# --- Подключаем шаблоны и статику ---
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Разрешаем CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------- ROUTES ----------------------

# --- Главная страница ---
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    employees = crud.get_employees(db)
    return templates.TemplateResponse("index.html", {"request": request, "employees": employees})


# --- API: получить всех сотрудников ---
@app.get("/employees/", response_model=list[schemas.Employee])
def read_employees(db: Session = Depends(get_db)):
    return crud.get_employees(db)


# --- API: добавить сотрудника (с проверкой дубликатов) ---
@app.post("/employees/")
def create_employee(
    first_name: str = Form(...),
    last_name: str = Form(...),
    role: str = Form(...),
    salary: float = Form(...),
    team: str = Form(...),
    hire_date: str = Form(...),
    db: Session = Depends(get_db)
):
    # Проверка на дубликаты
    existing = db.query(models.Employee).filter(
        models.Employee.first_name == first_name,
        models.Employee.last_name == last_name
    ).first()
    if existing:
        return {"error": "Сотрудник с таким именем и фамилией уже существует"}

    emp_data = schemas.EmployeeCreate(
        first_name=first_name,
        last_name=last_name,
        role=role,
        salary=salary,
        team=team,
        hire_date=hire_date
    )
    new_emp = crud.create_employee(db, emp_data)
    return {"message": "Сотрудник успешно добавлен", "id": new_emp.id}


# --- API: удалить сотрудника ---
@app.delete("/employees/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if not emp:
        return {"error": "Сотрудник не найден"}
    db.delete(emp)
    db.commit()
    return {"success": True, "message": "Сотрудник удалён"}


# --- API: чат с ИИ ---
@app.post("/chat/")
def chat_with_ai(query: str = Body(..., embed=True), db: Session = Depends(get_db)):
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY не найден в .env"}

    employees_data = crud.get_employees(db)
    employees_text = "\n".join(
        [f"{e.id}: {e.first_name} {e.last_name}, {e.role}, {e.salary}, {e.team}, {e.hire_date}"
         for e in employees_data]
    ) or "Сотрудников пока нет."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты умный помощник по сотрудникам компании. "
                    "Отвечай кратко, точно и на русском языке. "
                    "Дата найма — это начало работы, не дата окончания контракта. "
                    f"Список сотрудников:\n{employees_text}"
                )
            },
            {"role": "user", "content": query}
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            return {"error": "Groq API вернул ошибку", "details": response.text}

        data = response.json()
        ai_response = data.get("choices", [{}])[0].get("message", {}).get("content", "ИИ не дал ответ.")
        return {"query": query, "ai_response": ai_response}

    except requests.exceptions.RequestException as e:
        return {"error": "Ошибка соединения с Groq API", "details": str(e)}