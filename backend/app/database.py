import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


# Cargar .env desde backend/ y, como fallback, desde la raiz del repo.
app_dir = Path(__file__).resolve().parent
backend_dir = app_dir.parent
repo_root_dir = backend_dir.parent

load_dotenv(backend_dir / ".env")
load_dotenv(repo_root_dir / ".env")

# Configurar conexión a PostgreSQL.
# En Render/Neon esto debe venir por variable de entorno; no usar fallback silencioso.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no está configurada")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
