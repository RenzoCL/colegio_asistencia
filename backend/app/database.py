from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

# Crear carpeta para la DB si no existe
db_dir = os.path.join(os.getcwd(), "backend", "storage", "db")
os.makedirs(db_dir, exist_ok=True)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(db_dir, 'colegio.db')}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Alumno(Base):
    __tablename__ = "alumnos"
    id = Column(Integer, PRIMARY KEY=True, index=True)
    dni = Column(String, unique=True, index=True)
    nombres = Column(String)
    grado = Column(String)
    seccion = Column(String)
    nivel = Column(String)
    encoding = Column(Text)  # Guardaremos el array de la cara como texto (json)

class Asistencia(Base):
    __tablename__ = "asistencia"
    id = Column(Integer, PRIMARY KEY=True, index=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"))
    fecha = Column(DateTime, default=datetime.datetime.now)
    tipo = Column(String)  # ENTRADA o SALIDA
    estado = Column(String) # PRESENTE, TARDANZA

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
