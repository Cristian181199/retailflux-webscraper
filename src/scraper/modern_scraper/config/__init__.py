"""
Configuration Package

Gestiona la configuración del scraper por entornos.
"""
import os

def get_settings_module():
    """
    Retorna el módulo de configuración basado en la variable de entorno SCRAPER_ENV.
    
    Returns:
        str: Nombre del módulo de configuración
    """
    env = os.getenv('SCRAPER_ENV', 'development').lower()
    
    if env == 'production':
        return 'modern_scraper.config.production'
    elif env == 'development':
        return 'modern_scraper.config.development'
    else:
        return 'modern_scraper.config.development'  # Default to development

# For easy importing
SETTINGS_MODULE = get_settings_module()

print(f"🔧 Loading scraper configuration: {SETTINGS_MODULE}")
