from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import Base, engine
from routers import beastiary


# Асинхронный обработчик жизненного цикла
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код перед запуском приложения (startup)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield  # Здесь приложение работает


app = FastAPI(lifespan=lifespan)

app.include_router(beastiary.router, prefix="/beastiary", tags=["Beastiary"])


@app.get("/")
def root():
    return {"message": "Добро пожаловать в Бестиарий Лавкрафта!"}
