import logging
import json
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from database import Base, engine
from routers import beastiary

# Принудительно устанавливаем кодировку консоли на UTF-8 (для Windows)
if sys.platform == "win32":
    import os
    os.system("chcp 65001")  # Переключаем консоль на UTF-8
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Настройка логирования с явной кодировкой UTF-8
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bestiary.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class PrettyJSONMiddleware(BaseHTTPMiddleware):
    """Middleware для возврата отформатированного JSON при экспорте."""
    async def dispatch(self, request: Request, call_next):
        # Если это JSON-ответ, форматируем его с отступами
        response = await call_next(request)
        if isinstance(response, JSONResponse):
            try:
                content = json.loads(response.body.decode("utf-8"))
                response.body = json.dumps(content, ensure_ascii=False, indent=2).encode("utf-8")
                response.headers["Content-Length"] = str(len(response.body))
            except Exception as e:
                logger.error(f"Ошибка при форматировании JSON: {e}")

        return response


# Асинхронный обработчик жизненного цикла
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Создание таблиц в базе данных...")
    # Код перед запуском приложения (startup)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблицы созданы, приложение запущено!")
    yield  # Здесь приложение работает


app = FastAPI(lifespan=lifespan)
app.add_middleware(PrettyJSONMiddleware)
app.include_router(beastiary.router, prefix="/beastiary", tags=["Beastiary"])


@app.get("/")
def root():
    logger.info("Запрос на главную страницу.")
    return {"Сообщение": "Добро пожаловать в Бестиарий Лавкрафта!"}
