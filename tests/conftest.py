import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from database import Base, get_db
from main import app
from models.creature import CreatureDB

# Создаём тестовую базу данных
TEST_DATABASE_URL = "sqlite+aiosqlite:///test_beastiary.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

# Фикстура для клиента FastAPI
@pytest.fixture
def client():
    return TestClient(app)

# Асинхронная фикстура для тестовой базы данных
@pytest_asyncio.fixture
async def db_session():
    # Создаём таблицы
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Создаём сессию
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

# Переопределяем зависимость get_db для тестов
async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# Асинхронная фикстура для добавления тестовых данных
@pytest_asyncio.fixture
async def setup_test_data(db_session: AsyncSession):
    test_creatures = [
        CreatureDB(
            name="Йог-Сотот",
            description="Ключ и врата",
            danger_level=100,
            habitat="Вне пространства и времени",
            quote="Прошлое, настоящее и будущее, всё в руках Йог-Сотота.",
            category="Внешний Бог",
            abilities="Всезнание,Бессмертие,Управление временем",
            related_works="Ужас Данвича,Ночь в музее",
            image_url="https://static.wikia.nocookie.net/zlodei/images/6/6f/Main-qimg-faf9b8ff02eaf92b6af6de9a77210d0b.jpg/revision/latest?cb=20200523143046&path-prefix=ru",
            status="За пределами смерти и жизни",
            min_insanity=90,
            relations="Азатот",
            audio_url="https://knigavuhe.org/book/4099-uzhas-danvicha/",
            video_url="https://www.youtube.com/watch?v=cVxuoekM4UI"
        ),
        CreatureDB(
            name="Шуб-Ниггурат",
            description="Чёрная Коза Лесов с тысячью младых, мать ужасающих тварей.",
            danger_level=85,
            habitat="Тёмные леса и иные измерения",
            quote="Иа! Шуб-Ниггурат! Коза с тысячью младенцев!",
            category="Внешний Бог",
            abilities="плодовитость,призыв потомства,тёмная магия",
            related_works="Шепчущий во тьме",
            image_url="https://cs4.pikabu.ru/post_img/big/2016/06/04/7/1465038546141977706.jpg",
            status="Плодится",
            min_insanity=0,
            relations="",
            audio_url=None,
            video_url="https://www.youtube.com/watch?v=sJbXbOH27BA&t=42s&ab_channel=Lore"
        ),
        CreatureDB(
            name="Глубоководные",
            description="Раса гуманоидных амфибий",
            danger_level=40,
            habitat="Инсмунт",
            quote="Мне показалось, что в своей массе они были серовато-зеленого цвета, но с белыми животами.",
            category="Раса",
            abilities="Непредсказуемость",
            related_works="Тень над Инсмунтом,Дагон,Храм,Зов Ктулху,Ужас в Ред Хуке",
            image_url="https://upload.wikimedia.org/wikipedia/ru/thumb/d/dd/Innsmauth_and_deep_ones.jpg/330px-Innsmauth_and_deep_ones.jpg",
            status="Живые",
            min_insanity=0,
            relations="Дагон,Гидра,Ктулху",
            audio_url=None,
            video_url="https://www.youtube.com/watch?v=afQepalNbCw&ab_channel=Lore"
        ),
    ]
    db_session.add_all(test_creatures)
    await db_session.commit()
    # Проверяем, сколько записей добавлено
    count = await db_session.scalar(select(func.count(CreatureDB.id)))
    print(f"Добавлено записей в setup_test_data: {count}")
