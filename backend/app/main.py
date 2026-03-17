from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from . import database  # Asegúrate de usar el punto si están en el mismo paquete
from datetime import datetime, timedelta
import json

app = FastAPI(title="Colegio Asistencia API")

# --- ENDPOINTS DE GESTIÓN DE ALUMNOS ---

@app.post("/alumnos/registrar")
async def registrar_alumno(data: dict, db: Session = Depends(database.get_db)):
    """Recibe los datos del script de registro y los guarda en SQLite."""
    try:
        nuevo_alumno = database.Alumno(
            dni=data['dni'],
            nombres=data['nombres'],
            grado=data['grado'],
            seccion=data['seccion'],
            nivel=data['nivel'],
            encoding=json.dumps(data['encoding'])  # Guardamos la lista como texto
        )
        db.add(nuevo_alumno)
        db.commit()
        return {"status": "success", "message": f"Alumno {data['nombres']} registrado"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al registrar: {str(e)}")

@app.get("/alumnos/encodings")
async def obtener_encodings(db: Session = Depends(database.get_db)):
    """Las PCs Clientes llaman aquí al iniciar para cargar las caras en memoria."""
    alumnos = db.query(database.Alumno).all()
    lista_alumnos = []
    for a in alumnos:
        lista_alumnos.append({
            "id": a.id,
            "nombres": a.nombres,
            "encoding": json.loads(a.encoding) # Convertimos texto de vuelta a lista
        })
    return lista_alumnos

# --- LÓGICA DE ASISTENCIA (Tu código con mejoras) ---

@app.post("/verificar-asistencia/{alumno_id}")
async def verificar_asistencia(alumno_id: int, db: Session = Depends(database.get_db)):
    hoy = datetime.now().date()
    ahora = datetime.now()

    # Buscamos si ya marcó algo hoy
    asistencia = db.query(database.Asistencia).filter(
        database.Asistencia.alumno_id == alumno_id,
        database.Asistencia.fecha >= hoy
    ).first()

    if not asistencia:
        # PRIMER CONTACTO DEL DÍA -> Entrada
        nueva_asistencia = database.Asistencia(
            alumno_id=alumno_id,
            hora_entrada=ahora,
            tipo="ENTRADA",
            estado="PRESENTE" # Aquí podrías añadir lógica de horario de tardanza
        )
        db.add(nueva_asistencia)
        db.commit()
        return {"status": "success", "msg": "Entrada registrada", "tipo": "ENTRADA"}

    # REGLA DE LOS 5 MINUTOS
    diferencia = ahora - asistencia.hora_entrada
    if diferencia < timedelta(minutes=5):
        return {
            "status": "warning", 
            "msg": "Re-escaneo en menos de 5 min. ¿Es un error o salida?",
            "requiere_confirmacion": True
        }
    
    # REGISTRO DE SALIDA
    if not asistencia.hora_salida:
        asistencia.hora_salida = ahora
        asistencia.tipo = "ENTRADA/SALIDA"
        db.commit()
        return {"status": "success", "msg": "Salida registrada", "tipo": "SALIDA"}

    return {"status": "info", "msg": "El alumno ya cumplió su jornada hoy."}

# --- SELECTOR DE MODELOS IA ---

@app.get("/config/modelo")
async def get_modelo_ia(db: Session = Depends(database.get_db)):
    config = db.query(database.Configuracion).filter_by(parametro="modelo_ia").first()
    return {"nivel": config.valor if config else "2"}

@app.post("/config/modelo/{nivel}")
async def set_modelo_ia(nivel: int, db: Session = Depends(database.get_db)):
    if nivel not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Nivel no válido")
    
    config = db.query(database.Configuracion).filter_by(parametro="modelo_ia").first()
    if not config:
        config = database.Configuracion(parametro="modelo_ia", valor=str(nivel))
        db.add(config)
    else:
        config.valor = str(nivel)
    
    db.commit()
    return {"status": "updated", "nuevo_nivel": nivel}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
