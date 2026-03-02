import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.dependencies import shutdown_services, get_redis_service
from app.exceptions import BalanceServiceException
from app.config import get_settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения"""
    # Startup
    logger.info("Starting Balance Service...")

    try:
        # Инициализируем Redis
        await get_redis_service()
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Balance Service...")
    await shutdown_services()
    logger.info("Services shut down successfully")


app = FastAPI(
    title="Game Balance Service",
    description="Сервис для балансировки команд в играх",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(BalanceServiceException)
async def balance_exception_handler(request: Request, exc: BalanceServiceException):
    """Обработчик исключений балансировки"""
    return JSONResponse(
        status_code=exc.code,
        content={"success": False, "error": exc.message, "code": exc.code, "details": exc.details},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Общий обработчик исключений"""
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error", "code": 500, "details": {}},
    )


# Подключаем роутер
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
