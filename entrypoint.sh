#!/bin/bash
set -e

echo "🕷️ RetailFlux Scraper"
echo "======================"

# Debug environment variables
echo "🔍 Debug: Database connection parameters:"
echo "  POSTGRES_HOST: ${POSTGRES_HOST:-not set}"
echo "  POSTGRES_PORT: ${POSTGRES_PORT:-not set}"
echo "  POSTGRES_DB: ${POSTGRES_DB:-not set}"
echo "  POSTGRES_USER: ${POSTGRES_USER:-not set}"
echo "  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:+[SET]}"

# Test DNS resolution
echo "🌐 Testing DNS resolution..."
if command -v nslookup >/dev/null 2>&1; then
    nslookup "${POSTGRES_HOST}" || echo "❌ DNS resolution failed"
else
    echo "ℹ️ nslookup not available, trying direct connection"
fi

# Test connectivity with detailed output
echo "⏳ Testing database connection..."
echo "Command: pg_isready -h '${POSTGRES_HOST:-localhost}' -p '${POSTGRES_PORT:-5432}' -U '${POSTGRES_USER:-postgres}'"

# Try connection with timeout
max_attempts=10
attempt=0

while [ $attempt -lt $max_attempts ]; do
    attempt=$((attempt + 1))
    echo "📡 Connection attempt $attempt/$max_attempts..."
    
    if pg_isready -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER}"; then
        echo "✅ Database connection established!"
        break
    else
        echo "❌ Connection failed. Error details:"
        pg_isready -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER}" 2>&1 || true
        
        if [ $attempt -eq $max_attempts ]; then
            echo "💥 Maximum connection attempts reached. Exiting with debug info."
            echo "🔧 Possible solutions:"
            echo "   1. Check if both services are in the same Docker network"
            echo "   2. Verify database service is running and healthy"
            echo "   3. Confirm POSTGRES_HOST matches the database service name in Dokploy"
            echo "   4. Check firewall/security group settings"
            exit 1
        fi
        
        echo "⏸️ Waiting 5 seconds before retry..."
        sleep 5
    fi
done

# Move to the scraper directory
cd /app/src/scraper

MODE=${1:-${SCRAPER_MODE:-wait}}

case "$MODE" in
    "run")
        echo "🚀 Starting scraper execution..."
        # Ejecuta el spider principal de Edeka
        scrapy crawl edeka24_spider
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 0 ]; then
            echo "✅ Scraping completed successfully!"
        else
            echo "❌ Scraping failed with exit code: $EXIT_CODE"
        fi
        ;;
    "wait")
        echo "⏸️  Scraper in WAIT mode. Ready for scheduled execution via Dokploy."
        # Mantener el contenedor vivo
        tail -f /dev/null
        ;;
    *)
        echo "❓ Unknown mode: $MODE. Available modes: run, wait"
        exit 1
        ;;
esac