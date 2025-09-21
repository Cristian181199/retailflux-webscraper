# Dokploy Deployment Guide 🚀

Esta guía te ayudará a desplegar RetailFlux WebScraper en Dokploy con scheduling automático.

## 📋 Prerrequisitos

- ✅ Dokploy configurado y funcionando
- ✅ Base de datos PostgreSQL existente en Dokploy
- ✅ Variables de entorno de base de datos configuradas a nivel de proyecto
- ✅ Repositorio GitHub: `https://github.com/Cristian181199/retailflux-webscraper`

## 🗄️ Variables de Entorno Requeridas

### En Dokploy UI (Configuración del Servicio)

#### **Base de Datos (si no están a nivel de proyecto)**
```bash
POSTGRES_HOST=nombre_del_servicio_postgres
POSTGRES_PORT=5432
POSTGRES_DB=products_db
POSTGRES_USER=tu_usuario
POSTGRES_PASSWORD=tu_password
```

#### **Configuración del Scraper**
```bash
# Modo de ejecución
SCRAPER_MODE=wait

# Configuración de scraping
SCRAPER_CONCURRENT_REQUESTS=2
SCRAPER_DOWNLOAD_DELAY=2.0
SCRAPER_USER_AGENT=ModernEdekaScraper/1.0 (+cristian181199@gmail.com)

# Rate limiting
ENABLE_RATE_LIMITING=true
REQUESTS_PER_MINUTE=30

# Base de datos
SQLALCHEMY_ECHO=false
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Variables de aplicación
APP_ENV=production
PYTHONPATH=/app/src
```

#### **AI Features (Opcional)**
```bash
OPENAI_API_KEY=tu_openai_api_key_aqui
ENABLE_AI_FEATURES=true
GENERATE_EMBEDDINGS=true
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

## 🐳 Configuración del Servicio en Dokploy

### 1. Crear Nuevo Servicio

1. **Ir a tu proyecto en Dokploy**
2. **Crear nuevo servicio** → "Application"
3. **Configurar origen**:
   - **Source Type**: GitHub
   - **Repository**: `Cristian181199/retailflux-webscraper`
   - **Branch**: `main`

### 2. Configuración Docker

```yaml
# Dokploy detectará automáticamente el Dockerfile
# El Dockerfile ya está optimizado para producción
```

### 3. Configurar Variables de Entorno

En la sección **Environment Variables** del servicio, agregar todas las variables listadas arriba.

### 4. Configuración de Red

- **Port Mapping**: No necesario (servicio de background)
- **Internal Network**: Conectar con la red donde está tu base de datos

### 5. Configuración de Recursos

```yaml
# Recursos recomendados
CPU: 0.5 - 1.0 vCPU
Memory: 512MB - 1GB RAM
```

## ⚙️ Despliegue del Servicio

### 1. Primera Ejecución

```bash
# El servicio se desplegará en modo "wait" por defecto
# Esto mantiene el contenedor corriendo esperando comandos
```

### 2. Verificar el Deployment

1. **Check Logs**: Deberías ver:
   ```
   🕷️ RetailFlux Scraper
   ======================
   ⏳ Waiting for database connection...
   ✅ Database connection established.
   ⏸️  Scraper in WAIT mode. Ready for scheduled execution via Dokploy.
   ```

2. **Verificar Variables**: En los logs deberías ver que la base de datos se conecta correctamente.

## 📅 Configurar Schedule (Sábados 03:00)

### Método 1: Dokploy Native Schedule

1. **Ir a la configuración del servicio**
2. **Buscar sección "Scheduled Jobs" o "Cron Jobs"**
3. **Crear nuevo job**:
   ```bash
   # Cron Expression: Sábados a las 03:00
   0 3 * * 6
   
   # Comando
   docker exec [container_name] /usr/local/bin/entrypoint.sh run
   ```

### Método 2: Schedule Manual (Si Dokploy no tiene scheduling nativo)

Crear un servicio adicional con un contenedor cron:

1. **Crear archivo `docker-compose.scheduler.yml`**:
   ```yaml
   version: '3.8'
   services:
     scraper-scheduler:
       image: alpine/cron:latest
       volumes:
         - /var/run/docker.sock:/var/run/docker.sock:ro
       environment:
         - DOCKER_HOST=unix:///var/run/docker.sock
         - SCRAPER_CONTAINER_NAME=retailflux-scraper
       command: |
         sh -c 'echo "0 3 * * 6 docker exec $SCRAPER_CONTAINER_NAME /usr/local/bin/entrypoint.sh run" | crontab - && crond -f'
   ```

### Método 3: Ejecutar Manualmente

Si prefieres controlar la ejecución manualmente:

```bash
# Ejecutar inmediatamente desde Dokploy Terminal
docker exec [container_name] /usr/local/bin/entrypoint.sh run

# O cambiar el modo del servicio
# Actualizar variable SCRAPER_MODE=run y redeploy
```

## 🔍 Monitoreo y Logs

### Ver Logs de Ejecución

```bash
# En Dokploy, ir a la sección de Logs del servicio
# Filtrar por timestamp para ver ejecuciones específicas
```

### Logs Típicos de Ejecución Exitosa

```
🚀 Starting scraper execution...
📄 Processing main sitemap: https://www.edeka24.de/sitemaps/sitemap.xml
🔗 Found X sitemaps in index
🧪 Dev mode: Limited to Y product sitemaps
✅ Scraped: Product Name - 5.29 EUR
=== DATABASE PIPELINE STATS ===
Items saved: X
Items updated: Y
✅ Scraping completed successfully!
```

## 🛠️ Troubleshooting

### Error de Conexión a Base de Datos

1. **Verificar variables de entorno**
2. **Comprobar que el servicio de BD esté corriendo**
3. **Revisar conectividad de red entre servicios**

```bash
# Test de conexión manual
docker exec [container_name] pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER
```

### Error de Memoria

```bash
# Aumentar límites de memoria en la configuración del servicio
# Recomendado: 1GB RAM mínimo para scraping completo
```

### Error de Rate Limiting

```bash
# Ajustar variables:
SCRAPER_DOWNLOAD_DELAY=3.0
REQUESTS_PER_MINUTE=20
```

## 📊 Optimización para Producción

### Variables Recomendadas para Producción

```bash
# Modo producción (no dev limits)
APP_ENV=production

# Logging optimizado
SQLALCHEMY_ECHO=false

# Scraping responsable
SCRAPER_DOWNLOAD_DELAY=2.0
SCRAPER_CONCURRENT_REQUESTS=2
ROBOTSTXT_OBEY=true

# Pool de conexiones optimizado
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```

### Verificación Final

1. ✅ **Servicio desplegado** y corriendo en modo wait
2. ✅ **Variables de entorno** configuradas
3. ✅ **Conexión a BD** verificada
4. ✅ **Schedule configurado** para sábados 03:00
5. ✅ **Logs monitoreados** para verificar ejecuciones

## 🎯 Comandos Útiles de Dokploy

```bash
# Ver logs en tiempo real
dokploy logs follow [service_name]

# Restart del servicio
dokploy service restart [service_name]

# Ejecutar comando en contenedor
dokploy exec [service_name] [command]
```

¡Tu RetailFlux WebScraper estará listo para scrapear automáticamente cada sábado a las 03:00! 🕷️✨