from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Путь к базе данных SQLite
DATABASE_URL = "sqlite:///beastiary.db"

# Создается движок
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


# Создаём базовый класс для моделей (в 2.x используется DeclarativeBase вместо declarative_base())
class Base(DeclarativeBase):
    pass


# Создаем фабрику сессий
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


# Зависимость для получения сессии в маршрутах
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
