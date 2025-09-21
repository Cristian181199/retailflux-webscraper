"""
Pipelines Package

Contiene los pipelines modernos para procesamiento de datos scrapeados.
Incluye validación, enriquecimiento, y integración con base de datos.
"""

from .validation import ValidationPipeline, DuplicateDetectionPipeline
from .enrichment import EnrichmentPipeline
# TODO: Fix shared module imports before enabling
# from .database import DatabasePipeline

__all__ = [
    'ValidationPipeline',
    'DuplicateDetectionPipeline', 
    'EnrichmentPipeline',
    # 'DatabasePipeline',
]
