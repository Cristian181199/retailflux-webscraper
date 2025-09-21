"""
Modelo base con funcionalidades comunes para todos los modelos.
"""
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
from typing import Dict, Any

from ..config import Base


class TimestampMixin:
    """Mixin que añade timestamps automáticos a los modelos."""
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class BaseModel(Base, TimestampMixin):
    """
    Modelo base abstracto que proporciona funcionalidades comunes.
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    @declared_attr
    def __tablename__(cls):
        """Genera automáticamente el nombre de la tabla basado en el nombre de la clase."""
        return cls.__name__.lower() + 's'
    
    def to_dict(self, exclude: set = None) -> Dict[str, Any]:
        """
        Convierte el modelo a diccionario.
        
        Args:
            exclude: Set de campos a excluir del diccionario
            
        Returns:
            Diccionario con los datos del modelo
        """
        exclude = exclude or set()
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                # Convert datetime objects to ISO string format
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value
                
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude: set = None):
        """
        Actualiza el modelo desde un diccionario.
        
        Args:
            data: Diccionario con los datos a actualizar
            exclude: Set de campos a excluir de la actualización
        """
        exclude = exclude or {'id', 'created_at'}
        
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        """Representación string del modelo."""
        return f"<{self.__class__.__name__}(id={self.id})>"
