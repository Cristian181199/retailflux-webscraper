"""
Configuración centralizada para el proyecto Edeka Scraper.
"""
import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Configuración de la base de datos."""
    
    # PostgreSQL Configuration
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="products_db", env="POSTGRES_DB")
    postgres_user: str = Field(default="cristian", env="POSTGRES_USER")
    postgres_password: str = Field(default="", env="POSTGRES_PASSWORD")
    
    # SQLAlchemy Configuration
    sqlalchemy_echo: bool = Field(default=False, env="SQLALCHEMY_ECHO")
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    
    @property
    def database_url(self) -> str:
        """Construye la URL de la base de datos."""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    class Config:
        env_file_encoding = "utf-8"


class AISettings(BaseSettings):
    """Configuración para funcionalidades de IA."""
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Embedding Configuration
    embedding_model: str = Field(default="text-embedding-3-small", env="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=1536, env="EMBEDDING_DIMENSION")
    
    # Vector Search Configuration
    similarity_threshold: float = Field(default=0.8, env="SIMILARITY_THRESHOLD")
    max_results: int = Field(default=10, env="MAX_SEARCH_RESULTS")
    
    class Config:
        #env_file = ".env"
        env_file_encoding = "utf-8"


class ScrapingSettings(BaseSettings):
    """Configuración para el scraper."""
    
    # Scraping Configuration
    concurrent_requests: int = Field(default=2, env="SCRAPER_CONCURRENT_REQUESTS")
    download_delay: float = Field(default=1.0, env="SCRAPER_DOWNLOAD_DELAY")
    user_agent: str = Field(
        default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        env="SCRAPER_USER_AGENT"
    )
    
    # Rate Limiting
    enable_rate_limiting: bool = Field(default=True, env="ENABLE_RATE_LIMITING")
    requests_per_minute: int = Field(default=30, env="REQUESTS_PER_MINUTE")
    
    class Config:
        #env_file = ".env"
        env_file_encoding = "utf-8"


class APISettings(BaseSettings):
    """Configuración para la API."""
    
    # FastAPI Configuration
    title: str = Field(default="Supermarket Scraper API", env="API_TITLE")
    description: str = Field(
        default="API for scraping and searching supermarket data with AI capabilities",
        env="API_DESCRIPTION"
    )
    version: str = Field(default="2.0.0", env="API_VERSION")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="API_DEBUG")
    
    # CORS Configuration
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        env="CORS_ORIGINS"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convierte CORS_ORIGINS string a lista."""
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]
    
    # Authentication (for future use)
    jwt_secret_key: Optional[str] = Field(default=None, env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    
    class Config:
        #env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instances
database_settings = DatabaseSettings()
ai_settings = AISettings()
scraping_settings = ScrapingSettings()
api_settings = APISettings()
