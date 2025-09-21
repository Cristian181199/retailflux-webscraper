"""
Repository base con funcionalidades CRUD comunes.
"""
from typing import TypeVar, Generic, List, Optional, Dict, Any, Type, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError
import logging

from ..models.base import BaseModel

# Type variable for generic repository
ModelType = TypeVar("ModelType", bound=BaseModel)

logger = logging.getLogger(__name__)


class BaseRepository(Generic[ModelType]):
    """
    Repository base que proporciona operaciones CRUD comunes.
    """
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def create(self, db: Session, *, obj_in: Dict[str, Any]) -> ModelType:
        """
        Crea una nueva instancia del modelo.
        """
        try:
            db_obj = self.model(**obj_in)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Created {self.model.__name__} with ID: {db_obj.id}")
            return db_obj
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error creating {self.model.__name__}: {e}")
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise
    
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Obtiene una instancia por ID.
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """
        Obtiene múltiples instancias con filtros opcionales.
        """
        query = db.query(self.model)
        
        # Apply filters
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    attr = getattr(self.model, key)
                    if isinstance(value, list):
                        filter_conditions.append(attr.in_(value))
                    else:
                        filter_conditions.append(attr == value)
            
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))
        
        # Apply ordering
        if order_by:
            if order_by.startswith('-'):
                # Descending order
                order_field = order_by[1:]
                if hasattr(self.model, order_field):
                    query = query.order_by(getattr(self.model, order_field).desc())
            else:
                # Ascending order
                if hasattr(self.model, order_by):
                    query = query.order_by(getattr(self.model, order_by))
        else:
            # Default order by ID
            query = query.order_by(self.model.id)
        
        return query.offset(skip).limit(limit).all()
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: ModelType, 
        obj_in: Dict[str, Any]
    ) -> ModelType:
        """
        Actualiza una instancia existente.
        """
        try:
            # Use the model's update method if available
            if hasattr(db_obj, 'update_from_dict'):
                db_obj.update_from_dict(obj_in)
            else:
                # Fallback to manual update
                for field, value in obj_in.items():
                    if hasattr(db_obj, field):
                        setattr(db_obj, field, value)
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Updated {self.model.__name__} with ID: {db_obj.id}")
            return db_obj
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error updating {self.model.__name__}: {e}")
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating {self.model.__name__}: {e}")
            raise
    
    def delete(self, db: Session, *, id: int) -> Optional[ModelType]:
        """
        Elimina una instancia por ID.
        """
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
            logger.info(f"Deleted {self.model.__name__} with ID: {id}")
        return obj
    
    def count(self, db: Session, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Cuenta el número total de registros con filtros opcionales.
        """
        query = db.query(func.count(self.model.id))
        
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    attr = getattr(self.model, key)
                    if isinstance(value, list):
                        filter_conditions.append(attr.in_(value))
                    else:
                        filter_conditions.append(attr == value)
            
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))
        
        return query.scalar()
    
    def exists(self, db: Session, **filters) -> bool:
        """
        Verifica si existe al menos un registro con los filtros dados.
        """
        query = db.query(self.model)
        
        filter_conditions = []
        for key, value in filters.items():
            if hasattr(self.model, key):
                attr = getattr(self.model, key)
                filter_conditions.append(attr == value)
        
        if filter_conditions:
            query = query.filter(and_(*filter_conditions))
        
        return query.first() is not None
    
    def get_or_create(
        self, 
        db: Session, 
        defaults: Optional[Dict[str, Any]] = None,
        **filters
    ) -> tuple[ModelType, bool]:
        """
        Obtiene o crea un registro. Retorna (objeto, creado).
        """
        # Try to get existing
        query = db.query(self.model)
        
        filter_conditions = []
        for key, value in filters.items():
            if hasattr(self.model, key):
                attr = getattr(self.model, key)
                filter_conditions.append(attr == value)
        
        if filter_conditions:
            query = query.filter(and_(*filter_conditions))
        
        obj = query.first()
        
        if obj:
            return obj, False
        
        # Create new object
        create_data = {**filters}
        if defaults:
            create_data.update(defaults)
        
        obj = self.create(db, obj_in=create_data)
        return obj, True
    
    def bulk_create(self, db: Session, objects: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Crea múltiples objetos de forma eficiente.
        """
        try:
            db_objs = [self.model(**obj_data) for obj_data in objects]
            db.add_all(db_objs)
            db.commit()
            
            # Refresh all objects
            for obj in db_objs:
                db.refresh(obj)
            
            logger.info(f"Bulk created {len(db_objs)} {self.model.__name__} objects")
            return db_objs
        except Exception as e:
            db.rollback()
            logger.error(f"Error bulk creating {self.model.__name__}: {e}")
            raise
