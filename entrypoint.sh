#!/bin/bash
set -e

echo "🕷️ RetailFlux Scraper"
echo "======================"

# Wait for the database to be ready
echo "⏳ Waiting for database connection..."
while ! pg_isready -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER}" -q; do
  echo "  Database not ready, waiting 3 seconds..."
  sleep 3
done
echo "✅ Database connection established."

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