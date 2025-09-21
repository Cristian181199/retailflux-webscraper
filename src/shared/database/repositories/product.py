"""
Repository especializado para productos con búsqueda vectorial y semántica.
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func
from pgvector.sqlalchemy import Vector
import logging

from .base import BaseRepository
from ..models.product import Product

logger = logging.getLogger(__name__)


class ProductRepository(BaseRepository[Product]):
    """
    Repository especializado para productos con capacidades de IA y búsqueda vectorial.
    """
    
    def __init__(self):
        super().__init__(Product)
    
    def search_by_text(
        self, 
        db: Session, 
        query: str, 
        *,
        store_id: Optional[int] = None,
        category_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Product]:
        """
        Búsqueda de texto completo usando PostgreSQL full-text search.
        """
        # Base query with full-text search
        search_query = db.query(Product).filter(
            func.to_tsvector('english', Product.search_text).op('@@')(
                func.plainto_tsquery('english', query)
            )
        )
        
        # Add filters
        if store_id:
            search_query = search_query.filter(Product.store_id == store_id)
        if category_id:
            search_query = search_query.filter(Product.category_id == category_id)
        
        # Order by relevance
        search_query = search_query.order_by(
            func.ts_rank(
                func.to_tsvector('english', Product.search_text),
                func.plainto_tsquery('english', query)
            ).desc()
        )
        
        return search_query.limit(limit).all()
    
    def search_by_embedding(
        self,
        db: Session,
        embedding: List[float],
        *,
        store_id: Optional[int] = None,
        category_id: Optional[int] = None,
        similarity_threshold: float = 0.8,
        limit: int = 20
    ) -> List[Tuple[Product, float]]:
        """
        Búsqueda por similitud vectorial usando embeddings.
        Retorna productos con su puntuación de similitud.
        """
        # Build the similarity query
        similarity_expr = Product.embedding.cosine_distance(embedding)
        
        query = db.query(
            Product,
            (1 - similarity_expr).label('similarity')
        ).filter(
            Product.embedding.is_not(None),
            similarity_expr < (1 - similarity_threshold)
        )
        
        # Add filters
        if store_id:
            query = query.filter(Product.store_id == store_id)
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        # Order by similarity (descending)
        query = query.order_by(similarity_expr)
        
        results = query.limit(limit).all()
        return [(product, similarity) for product, similarity in results]
    
    def hybrid_search(
        self,
        db: Session,
        text_query: str,
        embedding: Optional[List[float]] = None,
        *,
        store_id: Optional[int] = None,
        category_id: Optional[int] = None,
        text_weight: float = 0.6,
        vector_weight: float = 0.4,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda híbrida que combina texto y vectores para mejores resultados.
        """
        results = {}
        
        # Text search results
        text_results = self.search_by_text(
            db, text_query,
            store_id=store_id,
            category_id=category_id,
            limit=limit * 2  # Get more candidates
        )
        
        # Score text results
        for i, product in enumerate(text_results):
            score = (len(text_results) - i) / len(text_results) * text_weight
            results[product.id] = {
                'product': product,
                'text_score': score,
                'vector_score': 0.0,
                'total_score': score
            }
        
        # Vector search results (if embedding provided)
        if embedding:
            vector_results = self.search_by_embedding(
                db, embedding,
                store_id=store_id,
                category_id=category_id,
                limit=limit * 2
            )
            
            for product, similarity in vector_results:
                vector_score = similarity * vector_weight
                
                if product.id in results:
                    # Update existing result
                    results[product.id]['vector_score'] = vector_score
                    results[product.id]['total_score'] += vector_score
                else:
                    # New result from vector search only
                    results[product.id] = {
                        'product': product,
                        'text_score': 0.0,
                        'vector_score': vector_score,
                        'total_score': vector_score
                    }
        
        # Sort by total score and return top results
        sorted_results = sorted(
            results.values(),
            key=lambda x: x['total_score'],
            reverse=True
        )
        
        return sorted_results[:limit]
    
    def get_products_needing_embeddings(
        self,
        db: Session,
        limit: int = 100
    ) -> List[Product]:
        """
        Obtiene productos que necesitan generar o actualizar embeddings.
        """
        return db.query(Product).filter(
            or_(
                Product.embedding.is_(None),
                Product.embedding_updated_at.is_(None),
                Product.updated_at > Product.embedding_updated_at
            )
        ).limit(limit).all()
    
    def update_embedding(
        self,
        db: Session,
        product_id: int,
        embedding: List[float],
        model: str
    ) -> Optional[Product]:
        """
        Actualiza el embedding de un producto.
        """
        product = self.get(db, product_id)
        if not product:
            return None
        
        try:
            product.embedding = embedding
            product.embedding_model = model
            product.embedding_updated_at = func.now()
            
            # Also update search_text if needed
            if not product.search_text:
                product.update_search_text()
            
            db.commit()
            db.refresh(product)
            logger.info(f"Updated embedding for product {product_id}")
            return product
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating embedding for product {product_id}: {e}")
            raise
    
    def get_by_url(self, db: Session, url: str) -> Optional[Product]:
        """
        Obtiene un producto por su URL.
        """
        return db.query(Product).filter(Product.product_url == url).first()
    
    def get_by_store_and_category(
        self,
        db: Session,
        store_id: int,
        category_id: Optional[int] = None,
        *,
        skip: int = 0,
        limit: int = 100,
        in_stock_only: bool = False
    ) -> List[Product]:
        """
        Obtiene productos por tienda y categoría.
        """
        query = db.query(Product).filter(Product.store_id == store_id)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if in_stock_only:
            query = query.filter(Product.in_stock == 'in_stock')
        
        return query.offset(skip).limit(limit).all()
    
    def get_products_by_price_range(
        self,
        db: Session,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        *,
        store_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """
        Obtiene productos por rango de precios.
        """
        query = db.query(Product).filter(Product.price_amount.is_not(None))
        
        if min_price is not None:
            query = query.filter(Product.price_amount >= min_price)
        if max_price is not None:
            query = query.filter(Product.price_amount <= max_price)
        if store_id:
            query = query.filter(Product.store_id == store_id)
        
        return query.order_by(Product.price_amount).offset(skip).limit(limit).all()
    
    def get_similar_products(
        self,
        db: Session,
        product_id: int,
        limit: int = 10
    ) -> List[Tuple[Product, float]]:
        """
        Encuentra productos similares basado en embeddings.
        """
        base_product = self.get(db, product_id)
        if not base_product or not base_product.embedding:
            return []
        
        return self.search_by_embedding(
            db,
            base_product.embedding,
            store_id=base_product.store_id,  # Same store
            limit=limit + 1  # +1 to exclude the base product
        )[1:]  # Remove the first result (the product itself)
    
    def bulk_update_search_text(self, db: Session) -> int:
        """
        Actualiza el search_text para todos los productos que no lo tienen.
        """
        products_without_search = db.query(Product).filter(
            or_(Product.search_text.is_(None), Product.search_text == '')
        ).all()
        
        updated_count = 0
        for product in products_without_search:
            try:
                product.update_search_text()
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating search text for product {product.id}: {e}")
        
        if updated_count > 0:
            db.commit()
            logger.info(f"Updated search_text for {updated_count} products")
        
        return updated_count
    
    def create_vector_index(self, db: Session) -> bool:
        """
        Crea índices vectoriales cuando hay suficientes datos.
        """
        try:
            # Check if we have enough data for indexes
            count = db.query(func.count(Product.id)).filter(
                Product.embedding.is_not(None)
            ).scalar()
            
            if count < 1000:  # Need at least 1000 products for efficient indexing
                logger.warning(f"Only {count} products with embeddings. Need at least 1000 for indexing.")
                return False
            
            # Create IVFFlat index for embeddings
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_products_embedding_ivfflat 
                ON products USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100)
            """))
            
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_products_search_vector_ivfflat 
                ON products USING ivfflat (search_vector vector_cosine_ops) 
                WITH (lists = 100)
            """))
            
            db.commit()
            logger.info("Successfully created vector indexes")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating vector indexes: {e}")
            return False


# Global instance
product_repository = ProductRepository()
