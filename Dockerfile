# Multi-stage build for minimal production image
# Stage 1: Build dependencies
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY src/scraper/requirements.txt /tmp/requirements-scraper.txt
COPY src/shared/requirements.txt /tmp/requirements-shared.txt

# Install Python dependencies in virtual environment
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements-scraper.txt \
    && pip install --no-cache-dir -r /tmp/requirements-shared.txt \
    && find /opt/venv -name "*.pyc" -delete \
    && find /opt/venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Stage 2: Production image
FROM python:3.12-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PYTHONPATH=/app/src \
    PATH="/opt/venv/bin:$PATH"

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    dnsutils \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r scraperuser && useradd -r -g scraperuser scraperuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set work directory
WORKDIR /app

# Copy only source code (no cache, no data files)
COPY --chown=scraperuser:scraperuser src/ ./src/
COPY --chown=scraperuser:scraperuser entrypoint.sh /usr/local/bin/entrypoint.sh

# Set permissions and create directories
RUN chmod +x /usr/local/bin/entrypoint.sh \
    && mkdir -p /app/data /app/logs \
    && chown -R scraperuser:scraperuser /app

# Switch to non-root user
USER scraperuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pg_isready -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-postgres}" || exit 1

# Entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Default command
CMD ["wait"]
