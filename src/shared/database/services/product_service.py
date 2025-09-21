"""
Servicio de productos con funcionalidades de IA y búsqueda avanzada.
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from ..repositories.product import product_repository
from ..models.product import Product
from ...ai.embeddings.generator import embedding_generator

logger = logging.getLogger(__name__)


class ProductService:
    """
    Servicio de productos que combina repositorio con funcionalidades de IA.
    """
    
    def __init__(self):
        self.repository = product_repository
        self.embedding_gen = embedding_generator
    
    def search_products(
        self,
        db: Session,
        query: str,
        *,
        store_id: Optional[int] = None,
        category_id: Optional[int] = None,
        use_ai: bool = True,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Búsqueda inteligente de productos que combina texto y vectores.
        """
        results = {
            'query': query,
            'total_results': 0,
            'products': [],
            'search_type': 'text_only',
            'ai_available': self.embedding_gen.is_available()
        }
        
        # Always do text search
        text_results = self.repository.search_by_text(
            db, query,
            store_id=store_id,
            category_id=category_id,
            limit=limit
        )
        
        if not use_ai or not self.embedding_gen.is_available():
            # Text-only search
            results['products'] = [product.to_dict() for product in text_results]
            results['total_results'] = len(text_results)
            return results
        
        # Generate embedding for the query
        query_embedding = self.embedding_gen.generate_embedding(query)
        
        if query_embedding:
            # Hybrid search (text + vectors)
            hybrid_results = self.repository.hybrid_search(
                db, query, query_embedding,
                store_id=store_id,
                category_id=category_id,
                limit=limit
            )
            
            results['search_type'] = 'hybrid'
            results['products'] = []
            
            for result in hybrid_results:
                product_data = result['product'].to_dict()
                product_data['search_scores'] = {
                    'text_score': result['text_score'],
                    'vector_score': result['vector_score'],
                    'total_score': result['total_score']
                }
                results['products'].append(product_data)
            
            results['total_results'] = len(results['products'])
        else:
            # Fallback to text search if embedding fails
            results['products'] = [product.to_dict() for product in text_results]
            results['total_results'] = len(text_results)
            results['search_type'] = 'text_fallback'
        
        return results
    
    def get_similar_products(
        self,
        db: Session,
        product_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Encuentra productos similares usando embeddings.
        """
        similar_products = self.repository.get_similar_products(db, product_id, limit)
        
        results = []
        for product, similarity in similar_products:
            product_data = product.to_dict()
            product_data['similarity_score'] = similarity
            results.append(product_data)
        
        return results
    
    def generate_missing_embeddings(self, db: Session, batch_size: int = 50) -> Dict[str, Any]:
        """
        Genera embeddings para productos que no los tienen.
        """
        if not self.embedding_gen.is_available():
            return {
                'success': False,
                'message': 'OpenAI API not available',
                'processed': 0
            }
        
        # Get products needing embeddings
        products = self.repository.get_products_needing_embeddings(db, limit=batch_size)
        
        if not products:
            return {
                'success': True,
                'message': 'All products have embeddings',
                'processed': 0
            }
        
        # Generate embedding texts
        texts = [product.get_embedding_text() for product in products]
        
        # Generate embeddings in batch
        embeddings = self.embedding_gen.generate_batch_embeddings(texts)
        
        processed = 0
        errors = []
        
        for i, product in enumerate(products):
            if i in embeddings:
                try:
                    self.repository.update_embedding(
                        db, product.id, embeddings[i], self.embedding_gen.model
                    )
                    processed += 1
                except Exception as e:
                    errors.append(f"Product {product.id}: {str(e)}")
                    logger.error(f"Error updating embedding for product {product.id}: {e}")
        
        return {
            'success': True,
            'message': f'Processed {processed} products',
            'processed': processed,
            'errors': errors[:5]  # Return first 5 errors
        }
    
    def update_search_texts(self, db: Session) -> int:
        """
        Actualiza el search_text para productos que no lo tienen.
        """
        return self.repository.bulk_update_search_text(db)
    
    def create_vector_indexes(self, db: Session) -> bool:
        """
        Crea índices vectoriales si hay suficientes datos.
        """
        return self.repository.create_vector_index(db)
    
    def get_product_by_url(self, db: Session, url: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un producto por su URL.
        """
        product = self.repository.get_by_url(db, url)
        return product.to_dict() if product else None
    
    def get_products_by_store(
        self,
        db: Session,
        store_id: int,
        *,
        category_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        in_stock_only: bool = False
    ) -> Dict[str, Any]:
        """
        Obtiene productos por tienda con paginación.
        """
        products = self.repository.get_by_store_and_category(
            db, store_id, category_id,
            skip=skip, limit=limit, in_stock_only=in_stock_only
        )
        
        # Get total count for pagination
        filters = {'store_id': store_id}
        if category_id:
            filters['category_id'] = category_id
        if in_stock_only:
            filters['in_stock'] = 'in_stock'
        
        total = self.repository.count(db, filters)
        
        return {
            'products': [product.to_dict() for product in products],
            'total': total,
            'skip': skip,
            'limit': limit,
            'has_next': (skip + limit) < total
        }
    
    def get_products_by_price_range(
        self,
        db: Session,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        *,
        store_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtiene productos por rango de precios.
        """
        products = self.repository.get_products_by_price_range(
            db, min_price, max_price,
            store_id=store_id, skip=skip, limit=limit
        )
        
        return [product.to_dict() for product in products]
    
    def create_product(self, db: Session, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo producto.
        """
        product = self.repository.create(db, obj_in=product_data)
        
        # Generate search text
        if hasattr(product, 'update_search_text'):
            product.update_search_text()
            db.commit()
        
        return product.to_dict()
    
    def update_product(
        self,
        db: Session,
        product_id: int,
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Actualiza un producto existente.
        """
        product = self.repository.get(db, product_id)
        if not product:
            return None
        
        updated_product = self.repository.update(db, db_obj=product, obj_in=update_data)
        
        # Update search text if content changed
        if any(field in update_data for field in ['name', 'description', 'details']):
            if hasattr(updated_product, 'update_search_text'):
                updated_product.update_search_text()
                db.commit()
        
        return updated_product.to_dict()


# Global service instance
product_service = ProductService()
