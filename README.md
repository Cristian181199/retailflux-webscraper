# RetailFlux WebScraper 🕷️

> AI-powered web scraper for German supermarkets with advanced data processing and semantic search capabilities

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://docker.com)
[![Python](https://img.shields.io/badge/Python-3.12-green)](https://python.org)
[![Scrapy](https://img.shields.io/badge/Scrapy-Latest-red)](https://scrapy.org)
[![AI](https://img.shields.io/badge/AI-Enabled-purple)](https://openai.com)

## 🎯 Overview

RetailFlux WebScraper is a modern, production-ready web scraping solution designed specifically for German supermarket data collection. Built with Scrapy, SQLAlchemy, and AI capabilities, it provides:

- **Intelligent product scraping** from Edeka24.de
- **AI-powered data enrichment** with OpenAI embeddings
- **PostgreSQL + pgvector** for semantic search
- **Docker-ready deployment** with GitHub Actions
- **Modular architecture** for easy extension

## 🏗️ Architecture

```
retailflux-webscraper/
├── src/
│   ├── scraper/                    # Scrapy project
│   │   └── modern_scraper/
│   │       ├── spiders/            # Spider implementations
│   │       ├── pipelines/          # Data processing pipelines
│   │       ├── items/              # Scrapy items
│   │       └── settings.py         # Scrapy configuration
│   └── shared/                     # Shared modules
│       ├── database/               # SQLAlchemy models & repos
│       ├── config/                 # Configuration management
│       └── ai/                     # AI functionality
├── .github/workflows/              # CI/CD pipelines
├── Dockerfile                      # Production container
└── entrypoint.sh                  # Container entry point
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- PostgreSQL with pgvector extension
- OpenAI API key (optional, for AI features)

### 1. Clone & Environment Setup

```bash
# Clone repository
git clone https://github.com/your-username/retailflux-webscraper.git
cd retailflux-webscraper

# Create environment file
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file:

```bash
# Database Configuration
POSTGRES_HOST=postgres_db
POSTGRES_PORT=5432
POSTGRES_DB=products_db
POSTGRES_USER=cristian
POSTGRES_PASSWORD=your_secure_password

# AI Features (Optional)
OPENAI_API_KEY=your_openai_api_key
ENABLE_AI_FEATURES=true
GENERATE_EMBEDDINGS=true

# Scraper Configuration
SCRAPER_CONCURRENT_REQUESTS=2
SCRAPER_DOWNLOAD_DELAY=2.0
```

### 3. Run with Docker

```bash
# Build and run
docker-compose up --build

# Run scraper in specific mode
docker run -e MODE=run retailflux-scraper
```

### 4. Local Development

```bash
# Install dependencies
pip install -r src/scraper/requirements.txt
pip install -r src/shared/requirements.txt

# Set Python path
export PYTHONPATH="$PWD/src"

# Run spider
cd src/scraper
scrapy crawl edeka24_spider
```

## 🕷️ Scraper Features

### Supported Stores

- **Edeka24.de** - German online supermarket
- Extensible architecture for additional stores

### Data Collection

- **Product Information**: Name, SKU, URL, images
- **Pricing**: Current price, base price per unit
- **Availability**: Stock status, delivery information
- **Categories**: Hierarchical categorization
- **Manufacturers**: Brand/manufacturer detection
- **Details**: Nutritional info, characteristics

### Smart Features

- **Rate limiting** and politeness controls
- **Error handling** and retry mechanisms
- **Duplicate detection** and data validation
- **Development limits** for testing
- **Sitemap-based discovery**

## 🤖 AI Capabilities

### Semantic Search

```python
# Product embeddings for similarity search
from shared.ai.embeddings import EmbeddingGenerator

generator = EmbeddingGenerator()
embedding = generator.generate_product_embedding(product)
```

### Features

- **OpenAI embeddings** (text-embedding-3-small)
- **pgvector integration** for efficient similarity search
- **Automatic text optimization** for AI processing
- **Batch processing** capabilities

## 🗄️ Database Schema

### Core Models

```sql
-- Products with AI support
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    sku VARCHAR(50),
    product_url VARCHAR UNIQUE NOT NULL,
    price_amount DECIMAL(10,2),
    embedding vector(1536),  -- OpenAI embedding
    search_text TEXT,
    store_id INTEGER REFERENCES stores(id),
    category_id INTEGER REFERENCES categories(id),
    manufacturer_id INTEGER REFERENCES manufacturers(id)
);

-- Vector similarity index
CREATE INDEX ON products USING ivfflat (embedding vector_cosine_ops);
```

### Repository Pattern

```python
from shared.database.repositories import ProductRepository

repo = ProductRepository()
products = repo.search_by_similarity(query_embedding, limit=10)
```

## 📊 Monitoring & Stats

### Scraper Statistics

- Items scraped/updated/skipped
- New categories/stores/manufacturers discovered
- Error rates and performance metrics
- Price change detection

### Development Mode

```python
DEV_SCRAPER_SETTINGS = {
    'max_sitemaps': 1,              # Limit sitemaps for testing
    'max_products_per_category': 5,  # Limit products per category
    'test_mode': True,              # Continue on errors
    'enable_data_export': True,     # Export data to files
}
```

## 🚢 Deployment

### GitHub Actions

Automatic Docker image building and publishing to GitHub Container Registry:

```yaml
name: Build and Push Scraper Image to GHCR
on:
  push:
    branches: [main]
```

### Production Modes

```bash
# Run once and exit
docker run -e MODE=run retailflux-scraper

# Wait mode for scheduled execution
docker run -e MODE=wait retailflux-scraper
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `MODE` | Container mode (run/wait) | `wait` |
| `POSTGRES_HOST` | Database host | `localhost` |
| `POSTGRES_PORT` | Database port | `5432` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ENABLE_AI_FEATURES` | Enable AI processing | `false` |
| `SCRAPER_DOWNLOAD_DELAY` | Delay between requests | `2.0` |

## 🔧 Configuration

### Scrapy Settings

```python
# Politeness settings
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# User agent
USER_AGENT = "ModernEdekaScraper/1.0 (+cristian181199@gmail.com)"
```

### Database Configuration

```python
# Pydantic settings with environment variables
class DatabaseSettings(BaseSettings):
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    # ...
```

## 🧪 Testing

```bash
# Run tests
pytest src/tests/

# Test specific spider
scrapy check edeka24_spider

# Dry run
scrapy crawl edeka24_spider --dry-run
```

## 📝 Development Guide

### Adding New Spiders

1. Create spider class extending `BaseSpider`
2. Implement required methods: `parse_category`, `parse_product`
3. Add store configuration to settings
4. Update pipelines if needed

### Extending Data Models

1. Update SQLAlchemy models in `shared/database/models/`
2. Create Alembic migration
3. Update Scrapy items
4. Modify pipelines for new fields

### AI Features

1. Implement embedding generators in `shared/ai/`
2. Add vector similarity methods to repositories
3. Configure embedding pipeline

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- 📧 Email: cristian181199@gmail.com
- 💻 GitHub Issues: [Create an issue](https://github.com/your-username/retailflux-webscraper/issues)

## 🙏 Acknowledgments

- **Scrapy** - The web scraping framework
- **SQLAlchemy** - The database toolkit
- **OpenAI** - AI capabilities
- **pgvector** - Vector similarity search