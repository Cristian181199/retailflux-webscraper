"""
Configuración y gestión de conexiones a la base de datos.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

from ..config import database_settings

# Configure logging
logger = logging.getLogger(__name__)

# Create declarative base for all models
Base = declarative_base()

# Create database engine with connection pooling and pgvector support
engine = create_engine(
    database_settings.database_url,
    poolclass=QueuePool,
    pool_size=database_settings.pool_size,
    max_overflow=database_settings.max_overflow,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recreate connections after 1 hour
    echo=database_settings.sqlalchemy_echo,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class DatabaseManager:
    """Gestor centralizado de base de datos."""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager para obtener una sesión de base de datos.
        Garantiza que la sesión se cierre correctamente.
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            logger.error(f"Database session error: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session_dependency(self) -> Generator[Session, None, None]:
        """
        Dependencia de FastAPI para inyección de sesión de base de datos.
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def create_tables(self):
        """Crea todas las tablas definidas en los modelos."""
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self):
        """Elimina todas las tablas (¡Usar con cuidado!)."""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.info("All database tables dropped")
    
    def check_pgvector_extension(self) -> bool:
        """
        Verifica si la extensión pgvector está instalada y habilitada.
        """
        try:
            with self.get_session() as session:
                result = session.execute(
                    text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                ).first()
                if result:
                    logger.info("pgvector extension is installed and enabled")
                    return True
                else:
                    logger.warning("pgvector extension is not installed")
                    return False
        except Exception as e:
            logger.error(f"Error checking pgvector extension: {e}")
            return False
    
    def enable_pgvector_extension(self):
        """
        Habilita la extensión pgvector en la base de datos.
        Requiere permisos de superusuario.
        """
        try:
            with self.get_session() as session:
                session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                logger.info("pgvector extension enabled successfully")
        except Exception as e:
            logger.error(f"Error enabling pgvector extension: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Prueba la conexión a la base de datos."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                logger.info("Database connection test successful")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions for backward compatibility
def get_db() -> Generator[Session, None, None]:
    """Función de conveniencia para obtener sesión de base de datos."""
    session = db_manager.SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_tables():
    """Función de conveniencia para crear tablas."""
    return db_manager.create_tables()


def test_connection():
    """Función de conveniencia para probar conexión."""
    return db_manager.test_connection()
