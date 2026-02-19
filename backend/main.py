from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, date
import json
import shutil
import os

from database import engine, get_db, Base
from models import Alumno, Asistencia
from face_engine import obtener_encoding, comparar_rostro

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Asistencia Facial")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ALUMNOS ---

@app.post("/alumnos/")
def registrar_alumno(nombre: str, apellido: str, grado: str, db: Session = Depends(get_db)):
    alumno = Alumno(nombre=nombre, apellido=apellido, grado=grado)
    db.add(alumno)
    db.commit()
    db.refresh(alumno)
    return alumno

@app.post("/alumnos/{alumno_id}/foto")
def subir_foto(alumno_id: int, foto: UploadFile = File(...), db: Session = Depends(get_db)):
    alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")

    foto_path = f"../fotos_registro/{alumno_id}_{foto.filename}"
    with open(foto_path, "wb") as f:
        shutil.copyfileobj(foto.file, f)

    encoding = obtener_encoding(foto_path)
    if encoding is None:
        raise HTTPException(status_code=400, detail="No se detectó ningún rostro en la foto")

    alumno.foto_path = foto_path
    alumno.encoding = json.dumps(encoding)
    db.commit()
    return {"mensaje": "Foto registrada correctamente"}

@app.get("/alumnos/")
def listar_alumnos(db: Session = Depends(get_db)):
    return db.query(Alumno).all()

@app.get("/alumnos/buscar")
def buscar_alumnos(q: str = Query(...), db: Session = Depends(get_db)):
    resultados = db.query(Alumno).filter(
        (Alumno.nombre.ilike(f"%{q}%")) | (Alumno.apellido.ilike(f"%{q}%"))
    ).limit(5).all()
    return resultados

# --- RECONOCIMIENTO ---

@app.post("/reconocer")
def reconocer_rostro(foto: UploadFile = File(...), db: Session = Depends(get_db)):
    """Solo reconoce, NO registra asistencia todavía"""
    foto_path = f"../fotos_registro/temp_{foto.filename}"
    with open(foto_path, "wb") as f:
        shutil.copyfileobj(foto.file, f)

    alumnos = db.query(Alumno).filter(Alumno.encoding != None).all()
    alumno_encontrado = None

    for alumno in alumnos:
        if comparar_rostro(alumno.encoding, foto_path):
            alumno_encontrado = alumno
            break

    os.remove(foto_path)

    if not alumno_encontrado:
        raise HTTPException(status_code=404, detail="Rostro no reconocido")

    return {
        "id": alumno_encontrado.id,
        "nombre": alumno_encontrado.nombre,
        "apellido": alumno_encontrado.apellido,
        "grado": alumno_encontrado.grado,
        "foto_path": alumno_encontrado.foto_path,
    }

# --- ASISTENCIA ---

@app.post("/asistencia/registrar")
def registrar_asistencia(
    alumno_id: int,
    tipo: str = "ingreso",
    registrado_por: str = "facial",
    db: Session = Depends(get_db)
):
    """Registra la asistencia después de confirmación"""
    alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")

    # Verificar duplicado en el mismo día y mismo tipo
    hoy = date.today()
    duplicado = db.query(Asistencia).filter(
        Asistencia.alumno_id == alumno_id,
        Asistencia.tipo == tipo,
        Asistencia.fecha >= datetime.combine(hoy, datetime.min.time()),
        Asistencia.fecha <= datetime.combine(hoy, datetime.max.time()),
    ).first()

    if duplicado:
        raise HTTPException(status_code=400, detail=f"Ya se registró el {tipo} de este alumno hoy")

    asistencia = Asistencia(
        alumno_id=alumno_id,
        tipo=tipo,
        registrado_por=registrado_por,
        fecha=datetime.now()
    )
    db.add(asistencia)
    db.commit()

    return {
        "mensaje": f"{tipo.capitalize()} registrado correctamente",
        "alumno": f"{alumno.nombre} {alumno.apellido}",
        "grado": alumno.grado,
        "tipo": tipo,
        "hora": datetime.now().strftime("%H:%M:%S"),
        "registrado_por": registrado_por
    }

@app.get("/asistencia/")
def listar_asistencias(db: Session = Depends(get_db)):
    asistencias = db.query(Asistencia).order_by(Asistencia.fecha.desc()).all()
    resultado = []
    for a in asistencias:
        resultado.append({
            "alumno": f"{a.alumno.nombre} {a.alumno.apellido}",
            "grado": a.alumno.grado,
            "fecha": a.fecha.strftime("%d/%m/%Y %H:%M"),
            "tipo": a.tipo,
            "registrado_por": a.registrado_por
        })
    return resultado

@app.get("/stats/")
def obtener_stats(db: Session = Depends(get_db)):
    hoy = date.today()
    ingresos_hoy = db.query(Asistencia).filter(
        Asistencia.tipo == "ingreso",
        Asistencia.fecha >= datetime.combine(hoy, datetime.min.time())
    ).count()
    salidas_hoy = db.query(Asistencia).filter(
        Asistencia.tipo == "salida",
        Asistencia.fecha >= datetime.combine(hoy, datetime.min.time())
    ).count()
    total_alumnos = db.query(Alumno).count()
    return {
        "ingresos_hoy": ingresos_hoy,
        "salidas_hoy": salidas_hoy,
        "total_alumnos": total_alumnos
    }