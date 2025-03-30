from random import choice
from sqlalchemy import select, func
from sqlalchemy.sql import asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query
from models.creature import Creature, CreatureDB
from database import get_db

router = APIRouter()


def transform_creature(creature: CreatureDB) -> dict:
    """Преобразует строковые поля в списки."""
    return {
        "id": creature.id,
        "name": creature.name,
        "description": creature.description,
        "danger_level": creature.danger_level,
        "habitat": creature.habitat,
        "quote": creature.quote,
        "category": creature.category,
        "abilities": creature.abilities.split(",") if creature.abilities else [],
        "related_works": creature.related_works.split(",")
        if creature.related_works
        else [],
        "image_url": creature.image_url,
        "status": creature.status,
        "min_insanity": creature.min_insanity,
        "relations": creature.relations.split(",") if creature.relations else [],
        "audio_url": creature.audio_url,
        "video_url": creature.video_url,
    }


@router.get("/list")
async def get_creatures(
    sort: str = Query(
        "name",
        description="Поле для сортировки: 'name' или 'danger_level'",
        regex="^(name|danger_level)$",
    ),
    order: str = Query(
        "asc",
        description="Порядок сортировки: 'asc' (по возрастанию) или 'desc' (по убыванию)",
        regex="^(asc|desc)$",
    ),
    db: AsyncSession = Depends(get_db),
):
    """Возвращает список всех существ с возможностью сортировки.

    Args:
        sort (str): Поле для сортировки: 'name' (имя) или 'danger_level' (уровень опасности). По умолчанию 'name'.
        order (str): Порядок сортировки: 'asc' (по возрастанию) или 'desc' (по убыванию). По умолчанию 'asc'.
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        dict: Словарь с ключом 'creatures' и списком отсортированных существ.

    Examples:
        - `/beastiary/list?sort=name&order=asc` - сортировка по имени от А до Я.
        - `/beastiary/list?sort=danger_level&order=desc` - сортировка по убыванию опасности.
    """
    # Определяем поле и порядок сортировки
    sort_field = {
        "name": CreatureDB.name,
        "danger_level": CreatureDB.danger_level
    }[sort]
    sort_order = asc if order == "asc" else desc
    
    # Выполняем запрос с сортировкой
    result = await db.execute(select(CreatureDB).order_by(sort_order(sort_field)))
    creatures = result.scalars().all()
    
    return {"creatures": [transform_creature(c) for c in creatures]}


@router.get("/info/{creature_name}")
async def get_creature_info(creature_name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CreatureDB).filter(CreatureDB.name == creature_name)
    )
    creature = result.scalars().first()
    if not creature:
        raise HTTPException(status_code=404, detail="Существо не найдено в бестиарии!")
    return transform_creature(creature)


# Маршрут для поиска по имени
@router.get("/search")
async def search_creatures(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    db: AsyncSession = Depends(get_db),
):
    query_lower = q.lower()

    # Ищем существ по частичному совпадению имени
    result = await db.execute(
        select(CreatureDB).filter(func.lower(CreatureDB.name).like(f"%{query_lower}%"))
    )
    creatures = result.scalars().all()

    if not creatures:
        raise HTTPException(
            status_code=404, detail=f"Существа с именем, содержащим '{q}', не найдены"
        )
    return {"creatures": [transform_creature(c) for c in creatures]}


# Маршрут для фильтрации по категориям
@router.get("/category/{category_name}")
async def get_creatures_by_category(
    category_name: str, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(CreatureDB).filter(CreatureDB.category == category_name)
    )
    creatures = result.scalars().all()

    if not creatures:
        raise HTTPException(
            status_code=404, detail=f"Нет существ в категории '{category_name}'"
        )
    return {"creatures": [transform_creature(c) for c in creatures]}


@router.get("/dangerous")
async def get_dangerous_creatures(
    min: int = Query(
        0, ge=0, le=100, description="Минимальный уровень опасности (включительно)"
    ),
    max: int = Query(
        100, ge=0, le=100, description="Максимальный уровень опасности (включительно)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Получает список существ с уровнем опасности в заданном диапазоне.

    Args:
        min (int): Минимальный уровень опасности (по умолчанию 0).
        max (int): Максимальный уровень опасности (по умолчанию 100).
        db (AsyncSession): Асинхронная сессия базы данных (внедряется через Depends).

    Returns:
        dict: Словарь с ключом 'dangerous_creatures' и списком существ в диапазоне.

    Examples:
        - `/beastiary/dangerous?min=80&max=100` - существа с уровнем опасности от 80 до 100.
        - `/beastiary/dangerous?min=50` - существа с уровнем опасности от 50 до 100.
    """
    result = await db.execute(
        select(CreatureDB).filter(
            CreatureDB.danger_level >= min, CreatureDB.danger_level <= max
        )
    )
    creatures = result.scalars().all()
    return {"dangerous_creatures": [transform_creature(c) for c in creatures]}


@router.get("/random")
async def get_random_creature(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CreatureDB))
    creatures = result.scalars().all()
    if not creatures:
        raise HTTPException(status_code=404, detail="Бестиарий пуст!")
    return transform_creature(choice(creatures))


@router.post("/add")
async def add_creature(creature: Creature, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CreatureDB).filter(CreatureDB.name == creature.name)
    )
    db_creature = result.scalars().first()
    if db_creature:
        raise HTTPException(
            status_code=400, detail="Это существо уже есть в бестиарии!"
        )

    new_creature = CreatureDB(
        name=creature.name,
        description=creature.description,
        danger_level=creature.danger_level,
        habitat=creature.habitat,
        quote=creature.quote,
        category=creature.category,
        abilities=",".join(creature.abilities),
        related_works=",".join(creature.related_works),
        image_url=creature.image_url,
        status=creature.status,
        min_insanity=creature.min_insanity,
        relations=",".join(creature.relations),
        audio_url=creature.audio_url,
        video_url=creature.video_url,
    )
    db.add(new_creature)
    await db.commit()
    await db.refresh(new_creature)
    return {"creature": creature.name, "message": "Существо добавлено в бестиарий!"}


@router.put("/update/{creature_name}")
async def update_creature(
    creature_name: str, creature: Creature, db: AsyncSession = Depends(get_db)
):
    """Обновляет данные существа в бестиарии по его имени.

    Args:
        creature_name (str): Имя существа для обновления (например, "Азатот").
        creature (Creature): Объект с новыми данными существа (Pydantic модель).
        db (AsyncSession): Асинхронная сессия базы данных (внедряется через Depends).

    Returns:
        dict: Словарь с сообщением об успехе и обновлёнными данными существа.

    Raises:
        HTTPException: Если существо с указанным именем не найдено (404).
    """
    # Ищем существо по имени
    result = await db.execute(
        select(CreatureDB).filter(CreatureDB.name == creature_name)
    )
    db_creature = result.scalars().first()

    if not db_creature:
        raise HTTPException(
            status_code=404, detail=f"Существо '{creature_name}' не найдено!"
        )

    # Обновляем поля если только они переданы
    for key, value in creature.model_dump(exclude_unset=True).items():
        if key in ["abilities", "related_works", "relations"]:
            setattr(db_creature, key, ",".join(value))
        else:
            setattr(db_creature, key, value)

    await db.commit()
    await db.refresh(db_creature)
    return {
        "message": f"Существо '{creature_name}' обновлено",
        "creture": transform_creature(db_creature),
    }


@router.delete("/remove/{creature_name}")
async def remove_creature(creature_name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CreatureDB).filter(CreatureDB.name == creature_name)
    )
    creature = result.scalars().first()
    if not creature:
        raise HTTPException(status_code=404, detail="Существо не найдено в бестиарии!")
    await db.delete(creature)
    await db.commit()
    return {"message": f"{creature_name} удалён из бестиария!"}
