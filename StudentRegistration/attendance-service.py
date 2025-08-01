"""Attendance Microservice
-------------------------
Puerto interno: 8002
Base de datos: MongoDB (mongo-db)
Descripción:
  - Permite registrar asistencia por estudiante y fecha.
  - Endpoints CRUD granulares (crear, listar, obtener, actualizar, eliminar).
  - Página de inicio Bootstrap.
"""

from datetime import date
from pathlib import Path
from typing import List, Optional
import os

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from bson import ObjectId

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
PORT = 8002

MONGO_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME", "mongo1")
MONGO_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "Sebasalejandro22")
MONGO_HOST = os.getenv("MONGO_HOST", "mongo-db")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))

MONGO_URI = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}"
DB_NAME = "attendance_db"
COLLECTION = "records"

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Attendance Service", version="1.0.0")


# ---------------------------------------------------------------------------
# Modelos Pydantic
# ---------------------------------------------------------------------------
class AttendanceIn(BaseModel):
    student_id: int = Field(..., description="ID del estudiante")
    day: date = Field(default_factory=date.today, description="Fecha de la asistencia")
    present: bool = Field(True, description="¿Asistió?")


class AttendanceOut(AttendanceIn):
    id: str


# ---------------------------------------------------------------------------
# Utilidades de serialización
# ---------------------------------------------------------------------------

def serialize(doc) -> AttendanceOut:
    return AttendanceOut(id=str(doc["_id"]), student_id=doc["student_id"], day=doc["day"], present=doc["present"])


# ---------------------------------------------------------------------------
# Conexión MongoDB
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    app.state.client = AsyncIOMotorClient(MONGO_URI)
    app.state.db = app.state.client[DB_NAME]


@app.on_event("shutdown")
async def shutdown_event():
    app.state.client.close()


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "service": "attendance-service"})


@app.post("/attendance", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
async def create_attendance(att: AttendanceIn):
    doc = att.dict()
    result = await app.state.db[COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    return serialize(doc)


@app.get("/attendance", response_model=List[AttendanceOut])
async def list_attendance(student_id: Optional[int] = None, limit: int = 100):
    query = {"student_id": student_id} if student_id is not None else {}
    cursor = app.state.db[COLLECTION].find(query).limit(limit)
    return [serialize(doc) async for doc in cursor]


@app.get("/attendance/{record_id}", response_model=AttendanceOut)
async def get_attendance(record_id: str):
    doc = await app.state.db[COLLECTION].find_one({"_id": ObjectId(record_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Record not found")
    return serialize(doc)


@app.put("/attendance/{record_id}", response_model=AttendanceOut)
async def update_attendance(record_id: str, att: AttendanceIn):
    update_result = await app.state.db[COLLECTION].update_one({"_id": ObjectId(record_id)}, {"$set": att.dict()})
    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Record not found")
    doc = await app.state.db[COLLECTION].find_one({"_id": ObjectId(record_id)})
    return serialize(doc)


@app.delete("/attendance/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance(record_id: str):
    delete_result = await app.state.db[COLLECTION].delete_one({"_id": ObjectId(record_id)})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Record not found")
    return


# ---------------------------------------------------------------------------
# Main local
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("attendance-service:app", host="0.0.0.0", port=PORT, reload=True)


