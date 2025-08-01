"""Student Registration Microservice
---------------------------------
Puerto interno: 8001
Base de datos: PostgreSQL (studentdb)
Descripción:
  - Permite crear, listar y obtener estudiantes.
  - Sirve página de inicio con Bootstrap.
"""

from pathlib import Path
from typing import List
import os

import asyncpg
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
PORT = 8001

DB_USER = os.getenv("POSTGRES_USER", "postgrest1")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "Sebasalejandro22")
DB_NAME = os.getenv("POSTGRES_DB", "studentdb")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres-db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "../templates"))

app = FastAPI(title="Register Service", version="1.0.0")


class StudentIn(BaseModel):
    full_name: str
    email: str


class StudentOut(StudentIn):
    id: int


# ---------------------------------------------------------------------------
# Base de datos (asyncpg)
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    app.state.pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    async with app.state.pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            );
            """
        )


@app.on_event("shutdown")
async def shutdown_event():
    await app.state.pool.close()


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página de inicio HTML.
    Usa plantilla compartida para mostrar nombre del servicio y link a /docs
    """
    return templates.TemplateResponse("index.html", {"request": request, "service": "register-service"})


@app.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
async def create_student(student: StudentIn):
    query = "INSERT INTO students(full_name, email) VALUES ($1,$2) RETURNING id;"
    async with app.state.pool.acquire() as conn:
        try:
            new_id = await conn.fetchval(query, student.full_name, student.email)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Email already exists")
    return StudentOut(id=new_id, **student.dict())


@app.get("/students", response_model=List[StudentOut])
async def list_students(limit: int = 100):
    query = "SELECT id, full_name, email FROM students ORDER BY id LIMIT $1;"
    async with app.state.pool.acquire() as conn:
        rows = await conn.fetch(query, limit)
    return [StudentOut(id=r["id"], full_name=r["full_name"], email=r["email"]) for r in rows]


@app.get("/students/{student_id}", response_model=StudentOut)
async def get_student(student_id: int):
    query = "SELECT id, full_name, email FROM students WHERE id=$1;"
    async with app.state.pool.acquire() as conn:
        row = await conn.fetchrow(query, student_id)
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")
    return StudentOut(id=row["id"], full_name=row["full_name"], email=row["email"])  # type: ignore


# ---------------------------------------------------------------------------
# Punto de entrada local (útil para desarrollo)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("student-register:app", host="0.0.0.0", port=PORT, reload=True)
