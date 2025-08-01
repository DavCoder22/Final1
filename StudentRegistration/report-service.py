"""Report Microservice
--------------------
Puerto interno: 8003
Combina datos de PostgreSQL (estudiantes) y MongoDB (asistencias) para generar reportes.
Endpoints:
  • GET /reports/attendance → Lista cada estudiante con total de asistencias.
  • Página de inicio Bootstrap en '/'.
"""

import asyncio
import os
from pathlib import Path
from typing import List

import asyncpg
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

# --------------------------- Configuración ---------------------------------
PORT = 8003
# PostgreSQL env
DB_USER = os.getenv("POSTGRES_USER", "postgrest1")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "Sebasalejandro22")
DB_NAME = os.getenv("POSTGRES_DB", "studentdb")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres-db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Mongo env
MONGO_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME", "mongo1")
MONGO_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "Sebasalejandro22")
MONGO_HOST = os.getenv("MONGO_HOST", "mongo-db")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_URI = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}"

# Templates directory
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Report Service", version="1.0.0")

# --------------------------- Modelos ---------------------------------------
class AttendanceReport(BaseModel):
    student_id: int
    full_name: str
    email: str
    attendance_count: int

# --------------------------- Ciclo de vida ---------------------------------
@app.on_event("startup")
async def startup_event() -> None:
    # Conexiones BD
    app.state.pg_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    app.state.mongo_client = AsyncIOMotorClient(MONGO_URI)
    app.state.mongo_db = app.state.mongo_client["attendance_db"]

@app.on_event("shutdown")
async def shutdown_event() -> None:
    await app.state.pg_pool.close()
    app.state.mongo_client.close()

# --------------------------- Rutas -----------------------------------------
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página de inicio genérica con Bootstrap."""
    return templates.TemplateResponse("index.html", {"request": request, "service": "report-service"})


@app.get("/reports/attendance", response_model=List[AttendanceReport])
async def attendance_report():
    """Une estudiantes + conteo de asistencias."""
    async with app.state.pg_pool.acquire() as conn:
        students = await conn.fetch("SELECT id, full_name, email FROM students;")

    if not students:
        raise HTTPException(status_code=404, detail="No students found")

    async def build_report(student):
        count = await app.state.mongo_db["records"].count_documents({"student_id": student["id"]})
        return AttendanceReport(
            student_id=student["id"],
            full_name=student["full_name"],
            email=student["email"],
            attendance_count=count,
        )

    reports = await asyncio.gather(*[build_report(s) for s in students])
    return reports


# --------------------------- Main local ------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("report-service:app", host="0.0.0.0", port=PORT, reload=True)
