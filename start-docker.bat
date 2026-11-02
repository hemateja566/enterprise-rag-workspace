@echo off
:: ============================================================
:: Enterprise RAG Workspace - Quick Start (Docker)
:: ============================================================
:: 1. Copy .env.example to .env and fill values
:: 2. Run: docker compose up -d
:: 3. Wait for services to start (mysql + redis turn green)
:: 4. Visit: http://localhost:3000 (frontend) and http://localhost:5000/api (API)

echo.
echo [Enterprise RAG Workspace] Starting infrastructure...
echo.

:: Check if Docker is running
docker info >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Docker is not running or not installed.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

:: Check if docker-compose is available
docker compose version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: docker-compose plugin not found.
    echo Please install Docker Compose v2+.
    pause
    exit /b 1
)

:: Pull images and start containers
echo [Building and starting containers...]
docker compose up --build -d

echo.
echo Waiting for services to become healthy...
echo.

:: Wait for MySQL
echo Waiting for MySQL...
for /L %i in (1,1,30) do (
    docker exec enterprise-rag-mysql mysqladmin ping -u root -p%MYSQL_ROOT_PASSWORD% >nul 2>&1
    if %errorLevel% equ 0 (
        echo MySQL is up!
        goto :mysql_up
    )
    timeout /t 2 >nul
)
echo ERROR: MySQL did not start in time.
goto :eof

:mysql_up
echo.

:: Wait for Redis
echo Waiting for Redis...
for /L %i in (1,1,15) do (
    docker exec enterprise-rag-redis redis-cli ping >nul 2>&1
    if %errorLevel% equ 0 (
        echo Redis is up!
        goto :redis_up
    )
    timeout /t 1 >nul
)
echo ERROR: Redis did not start in time.
goto :eof

:redis_up
echo.

:: Wait for API health
echo Waiting for Flask API...
for /L %i in (1,1,30) do (
    curl -s -f http://localhost:5000/api/health >nul 2>&1
    if %errorLevel% equ 0 (
        echo Flask API is up!
        goto :api_up
    )
    timeout /t 2 >nul
)
echo ERROR: Flask API did not start in time.
goto :eof

:api_up
echo.

:: Summary
echo ============================================================
echo Deployment Complete!
echo ============================================================
echo - Frontend:     http://localhost:3000
echo - API (SSE):    http://localhost:5000/api
echo - API Health:   http://localhost:5000/api/health
echo - MySQL:        3306 (container: enterprise-rag-mysql)
echo - Redis:        6379 (container: enterprise-rag-redis)
echo ============================================================
echo Next steps:
echo 1. Register a new account at http://localhost:3000/auth/register
echo 2. Upload a PDF document via the Dashboard
echo 3. Wait for processing (Celery background task)
echo 4. Query with grounded Q&A and source citations
echo.
pause