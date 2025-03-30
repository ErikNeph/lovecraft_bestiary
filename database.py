from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Путь к базе данных SQLite с асинхронным драйвером
DATABASE_URL = "sqlite+aiosqlite:///beastiary.db"

# Создаём асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=False)  # echo=True для отладки, можно убрать


# Создаём базовый класс для моделей (в 2.x используется DeclarativeBase вместо declarative_base())
class Base(DeclarativeBase):
    pass


# Асинхронная зависимость для получения сессии
async def get_db():
    async with AsyncSession(engine, expire_on_commit=False) as db:
        yield db
