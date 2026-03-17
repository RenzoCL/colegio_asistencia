from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import database  # Importamos nuestro archivo de DB
from datetime import datetime, timedelta

app = FastAPI(title="Colegio Asistencia API")

# --- LÓGICA DE ASISTENCIA (Regla de 5 minutos) ---

@app.post("/verificar-asistencia")
async def verificar_asistencia(alumno_id: int, db: Session = Depends(database.get_db)):
    # 1. Buscar último registro del alumno hoy
    hoy = datetime.now().date()
    ultimo_registro = db.query(database.Asistencia).filter(
        database.Asistencia.alumno_id == alumno_id,
        database.Asistencia.fecha == hoy
    ).first()

    ahora = datetime.now()

    if not ultimo_registro:
        # No hay registro hoy -> ENTRADA automática
        nueva_asistencia = database.Asistencia(
            alumno_id=alumno_id,
            hora_entrada=ahora,
            estado="PRESENTE"
        )
        db.add(nueva_asistencia)
        db.commit()
        return {"status": "success", "msg": "Entrada registrada", "tipo": "ENTRADA"}

    # 2. Si ya existe, aplicar regla de 5 minutos
    diferencia = ahora - ultimo_registro.hora_entrada
    
    if diferencia < timedelta(minutes=5):
        # Disparar alerta al portero (El frontend manejará el popup)
        return {
            "status": "warning", 
            "msg": "Re-escaneo detectado en menos de 5 min",
            "alumno_id": alumno_id,
            "requiere_confirmacion": True
        }
    
    # 3. Registrar SALIDA si pasó el tiempo
    if not ultimo_registro.hora_salida:
        ultimo_registro.hora_salida = ahora
        db.commit()
        return {"status": "success", "msg": "Salida registrada", "tipo": "SALIDA"}

    return {"status": "info", "msg": "El alumno ya cuenta con entrada y salida."}

# --- SELECTOR DE MODELOS IA (Persistente) ---

@app.get("/config/modelo")
async def get_modelo_ia(db: Session = Depends(database.get_db)):
    config = db.query(database.Configuracion).filter_by(parametro="modelo_ia").first()
    return {"nivel": config.valor}

@app.post("/config/modelo/{nivel}")
async def set_modelo_ia(nivel: int, db: Session = Depends(database.get_db)):
    if nivel not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Nivel no válido")
    
    config = db.query(database.Configuracion).filter_by(parametro="modelo_ia").first()
    config.valor = str(nivel)
    db.commit()
    return {"status": "updated", "nuevo_nivel": nivel}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) # 0.0.0.0 para acceso en LAN
