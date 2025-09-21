# Retailflux Scraper - Production Dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV PYTHONPATH=/app/src

# Set work directory
WORKDIR /app

# Install system dependencies including pg_isready for health checks
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        curl \
        postgresql-client \
        libpq-dev \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# no-root user creation
RUN groupadd -r scraperuser && useradd -r -g scraperuser scraperuser

# Copy only requirements to cache dependencies
COPY src/scraper/requirements.txt ./requirements-scraper.txt
COPY src/shared/requirements.txt ./requirements-shared.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-scraper.txt \
    && pip install --no-cache-dir -r requirements-shared.txt

# Copy project
COPY src/ ./src/

# Create necessary directories and assign permissions
RUN mkdir -p /app/data /app/logs \
    && chown -R scraperuser:scraperuser /app

# Copy and assign permissions to entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Switch to non-root user
USER scraperuser

# Entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Command to set a default wait state
CMD ["wait"]