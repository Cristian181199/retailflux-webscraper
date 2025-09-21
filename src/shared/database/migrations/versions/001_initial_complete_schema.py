"""Initial complete schema - Create all tables and structures

Revision ID: 001_initial_complete_schema
Revises: 
Create Date: 2025-09-20 16:06:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '001_initial_complete_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema with all required tables."""
    
    # ========================================
    # ENABLE POSTGRESQL EXTENSIONS
    # ========================================
    
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    op.execute('CREATE EXTENSION IF NOT EXISTS unaccent')
    
    # ========================================
    # CREATE STORES TABLE
    # ========================================
    
    op.create_table('stores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('slug', sa.String(255), nullable=False, index=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website_url', sa.String(500), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('country', sa.String(2), nullable=False, server_default='DE'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='EUR'),
        sa.Column('scraper_config', sa.JSON(), nullable=True),
        sa.Column('api_config', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_scraping_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_scrape_at', sa.DateTime(), nullable=True),
        sa.Column('scrape_frequency', sa.String(50), nullable=False, server_default='daily'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    
    # ========================================
    # CREATE CATEGORIES TABLE
    # ========================================
    
    op.create_table('categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('slug', sa.String(255), nullable=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True, index=True),
        sa.Column('level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('path', sa.String(1000), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'parent_id', name='_category_parent_uc'),
        sa.UniqueConstraint('slug', name='_category_slug_uc')
    )
    
    # ========================================
    # CREATE MANUFACTURERS TABLE
    # ========================================
    
    op.create_table('manufacturers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('slug', sa.String(255), nullable=True, index=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website_url', sa.String(500), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('country', sa.String(2), nullable=True),
        sa.Column('contact_info', sa.JSON(), nullable=True),
        sa.Column('parent_company', sa.String(255), nullable=True),
        sa.Column('brand_category', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('certifications', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # ========================================
    # CREATE PRODUCTS TABLE
    # ========================================
    
    op.create_table('products',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        
        # Basic product information
        sa.Column('name', sa.String(), nullable=False, index=True),
        sa.Column('sku', sa.String(50), nullable=True, index=True),
        sa.Column('product_url', sa.String(), nullable=False, index=True),
        sa.Column('image_url', sa.String(), nullable=True),
        
        # Price information
        sa.Column('price_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('price_currency', sa.String(10), nullable=False, server_default='EUR'),
        sa.Column('base_price_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('base_price_unit', sa.String(20), nullable=True),
        sa.Column('base_price_quantity', sa.Numeric(precision=10, scale=2), nullable=True),
        
        # Detailed product information
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('nutritional_info', sa.JSON(), nullable=True),
        
        # Availability and stock
        sa.Column('in_stock', sa.String(20), nullable=False, server_default='unknown'),
        sa.Column('availability_text', sa.String(), nullable=True),
        
        # AI and Vector Search fields
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('embedding_model', sa.String(50), nullable=True),
        sa.Column('embedding_updated_at', sa.DateTime(), nullable=True),
        
        # Search optimization
        sa.Column('search_text', sa.Text(), nullable=True, index=True),
        sa.Column('search_vector', Vector(1536), nullable=True),
        
        # Metadata
        sa.Column('scraped_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_price_update', sa.DateTime(), nullable=True),
        sa.Column('scrape_count', sa.Numeric(precision=10, scale=0), nullable=False, server_default='1'),
        
        # Foreign keys
        sa.Column('store_id', sa.Integer(), nullable=False, index=True),
        sa.Column('category_id', sa.Integer(), nullable=True, index=True),
        sa.Column('manufacturer_id', sa.Integer(), nullable=True, index=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.ForeignKeyConstraint(['manufacturer_id'], ['manufacturers.id'], ),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_url')
    )
    
    # ========================================
    # CREATE INDEXES FOR PERFORMANCE
    # ========================================
    
    # Products indexes
    op.create_index('ix_products_store_category', 'products', ['store_id', 'category_id'])
    op.create_index('ix_products_price_range', 'products', ['price_amount', 'store_id'])
    op.create_index('ix_products_in_stock', 'products', ['in_stock', 'store_id'])
    op.create_index('ix_products_scraped_at', 'products', ['scraped_at'])
    
    # Full-text search indexes
    op.create_index('ix_products_search_text_gin', 'products', ['search_text'], postgresql_using='gin', postgresql_ops={'search_text': 'gin_trgm_ops'})
    
    # Create full-text search index
    op.execute("""
    CREATE INDEX ix_products_fts ON products USING gin(
        to_tsvector('english', 
            COALESCE(name, '') || ' ' || 
            COALESCE(description, '') || ' ' || 
            COALESCE(search_text, '')
        )
    )
    """)
    
    # Trigram index for fuzzy text search
    op.execute('CREATE INDEX ix_products_name_trgm ON products USING gin (name gin_trgm_ops)')
    
    # Vector indexes will be created after data is populated
    # Note: These require data to build the index properly
    # op.execute('CREATE INDEX ix_products_embedding_vector ON products USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)')
    # op.execute('CREATE INDEX ix_products_search_vector ON products USING ivfflat (search_vector vector_cosine_ops) WITH (lists = 100)')
    
    # ========================================
    # CREATE UTILITY FUNCTIONS
    # ========================================
    
    # Create function for normalized text search
    op.execute("""
    CREATE OR REPLACE FUNCTION normalize_text(text) 
    RETURNS text AS $$
    BEGIN
        RETURN lower(unaccent($1));
    END;
    $$ LANGUAGE plpgsql IMMUTABLE;
    """)
    
    # ========================================
    # INSERT DEFAULT DATA
    # ========================================
    
    # Insert default store (Edeka24)
    op.execute("""
    INSERT INTO stores (name, slug, display_name, description, website_url, country, currency, scraper_config) 
    VALUES (
        'edeka24',
        'edeka24', 
        'EDEKA24',
        'EDEKA online supermarket for grocery delivery',
        'https://www.edeka24.de',
        'DE',
        'EUR',
        '{"base_url": "https://www.edeka24.de", "concurrent_requests": 2, "download_delay": 1.0}'
    )
    """)
    
    # Insert root categories
    op.execute("""
    INSERT INTO categories (name, slug, description, level, path) VALUES
    ('Lebensmittel', 'lebensmittel', 'Grundnahrungsmittel und Lebensmittel', 0, 'lebensmittel'),
    ('Getränke', 'getraenke', 'Alkoholische und alkoholfreie Getränke', 0, 'getraenke'),
    ('Drogerie', 'drogerie', 'Körperpflege und Haushaltsartikel', 0, 'drogerie'),
    ('Tierbedarf', 'tierbedarf', 'Futter und Zubehör für Haustiere', 0, 'tierbedarf')
    """)


def downgrade() -> None:
    """Drop all tables and extensions."""
    
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('products')
    op.drop_table('manufacturers')
    op.drop_table('categories')
    op.drop_table('stores')
    
    # Drop custom functions
    op.execute('DROP FUNCTION IF EXISTS normalize_text(text)')
    
    # Note: We don't drop extensions as they might be used by other databases
    # op.execute('DROP EXTENSION IF EXISTS unaccent')
    # op.execute('DROP EXTENSION IF EXISTS pg_trgm')
    # op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
    # op.execute('DROP EXTENSION IF EXISTS vector')