from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Alumno(Base):
    __tablename__ = "alumnos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    grado = Column(String, nullable=False)
    foto_path = Column(String, nullable=True)
    encoding = Column(String, nullable=True)
    asistencias = relationship("Asistencia", back_populates="alumno")

class Asistencia(Base):
    __tablename__ = "asistencias"

    id = Column(Integer, primary_key=True, index=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"))
    fecha = Column(DateTime, default=datetime.now)
    tipo = Column(String, default="ingreso")  # ingreso o salida
    registrado_por = Column(String, default="facial")  # facial o manual
    alumno = relationship("Alumno", back_populates="asistencias")