import csv
import logging
from io import StringIO
from random import choice
from sqlalchemy import select, func
from sqlalchemy.sql import asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from models.creature import Creature, CreatureDB
from database import get_db


router = APIRouter()
logger = logging.getLogger(__name__)


def transform_creature(creature: CreatureDB, for_csv: bool = False) -> dict:
    """Преобразует строковые поля в списки."""

    def clean_string(text):
        """Для очистки строк от лишних \n"""
        if isinstance(text, str):
            return text.replace("\n", " ").strip()
        return text

    # Разбиваем строки на списки, если они не пустые
    abilities = [
        clean_string(ability)
        for ability in (creature.abilities.split(",") if creature.abilities else [])
    ]
    related_works = [
        clean_string(work)
        for work in (
            creature.related_works.split(",") if creature.related_works else []
        )
    ]
    relations = [
        clean_string(relation)
        for relation in (creature.relations.split(",") if creature.relations else [])
    ]

    data = {
        "Id": creature.id,
        "Имя": clean_string(creature.name),
        "Описание": clean_string(creature.description),
        "Уровень_опасности": creature.danger_level,
        "Среда_обитания": clean_string(creature.habitat),
        "Цитата": clean_string(creature.quote),
        "Категория": clean_string(creature.category),
        "Способности": abilities,
        "Связанные_произведения": related_works,
        "Url_изображения": creature.image_url,
        "Статус": clean_string(creature.status),
        "Минимальное_безумие": creature.min_insanity,
        "Связи": relations,
        "Url_аудио": creature.audio_url,
        "Url_видео": creature.video_url,
    }
    # Для JSON оставляем списки как есть, для CSV преобразуем в строки
    if not for_csv:
        data["Способности"] = (
            ", ".join(data["Способности"]) if data["Способности"] else ""
        )
        data["Связанные_произведения"] = (
            ", ".join(data["Связанные_произведения"])
            if data["Связанные_произведения"]
            else ""
        )
        data["Связи"] = ", ".join(data["Связи"]) if data["Связи"] else ""
    return data


@router.get("/export")
async def export_bestiary(
    format: str = Query(
        "json", description="Формат экспорта: 'json' или 'csv'", regex="^(json|csv)$"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Экспортируем всех существ из бестиария в формат JSON или CSV.

    Args:
        format (str): Формат экспорта: 'json' или 'csv'. По умолчанию 'json'.
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        JSONResponse: Файл с данными всех существ для скачивания (с отступами).

    Examples:
        - `/beastiary/export` - возвращает JSON-файл со всеми существами.
    """
    # Получаем всех существ
    result = await db.execute(select(CreatureDB))
    creatures = result.scalars().all()

    # Преобразуем в список словарей
    export_data_json = [transform_creature(c, for_csv=False) for c in creatures]
    export_data_csv = [transform_creature(c, for_csv=True) for c in creatures]

    logger.info(f"Export data length: {len(export_data_json)}")
    if export_data_json:
        logger.info(f"First item type: {type(export_data_json[0])}")

    if format == "json":
        return JSONResponse(
            content={"Существа": export_data_json},
            headers={
                "Content-Disposition": "attachment; filename=bestiary_export.json"
            },
            media_type="application/json",
        )
    elif format == "csv":
        # Создаём CSV в памяти
        output = StringIO()
        fieldnames = [
            "Id",
            "Имя",
            "Описание",
            "Уровень_опасности",
            "Среда_обитания",
            "Цитата",
            "Категория",
            "Способности",
            "Связанные_произведения",
            "Url_изображения",
            "Статус",
            "Минимальное_безумие",
            "Связи",
            "Url_аудио",
            "Url_видео",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()

        # Записываем данные, если они есть
        if export_data_csv:
            writer.writerows(export_data_csv)
        csv_content = output.getvalue()
        output.close()

        return Response(
            content=csv_content.encode("utf-8"),
            headers={"Content-Disposition": "attachment; filename=bestiary_export.csv"},
            media_type="text/csv; charset=utf-8",
        )


@router.get("/list")
async def list_bestiary(
    limit: int = Query(10, ge=1, le=100, description="Количество записей на странице (максимум 100)"),
    offset: int = Query(0, ge=0, description="Смещение (с какой записи начинать)"),
    db: AsyncSession = Depends(get_db)
):
    """Возвращает список существ из бестиария с пагинацией.

    Args:
        limit (int, optional): Количество записей на странице. Должны быть от 1 до 100 по умолчанию 10.
        offset (int, optional): Смещение (с какой записи начинать). Должно быть >= 0. По умолчанию 0.
        db (AsyncSession, optional): Сессия базы данных, предоставляемая через зависимость.

    Returns:
        dict: Словарь с ключами:
            - "Существа": список существ в формате JSON.
            - "Всего": общее количество существ в бестиарии.
            - "Лимит": текущий лимит записей.
            - "Смещение": текущие смещение.
    
    Raises:
        HTTPException: Если существа не найдены (404).
    """
    count_query = await db.execute(select(CreatureDB).with_only_columns(func.count()))
    total_count = count_query.scalar()
    
    # Получаем записи с пагинацей
    result = await db.execute(select(CreatureDB).limit(limit).offset(offset))
    creatures = result.scalars().all()
    
    if not creatures:
        raise HTTPException(status_code=404, detail="Существа не найдены")
    
    logger.info(f"Возвращено {len(creatures)} существ на бестиария с limit={limit}, offset={offset}")
    return {
        "Существа": [transform_creature(c) for c in creatures],
        "Всего": total_count,
        "Лимит": limit,
        "Смещение": offset
    }


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
    q: str = Query(None, min_length=1, description="Поиск по имени (начало имени)"),
    category: str = Query(None, description="Фильтр по категории"),
    min_danger: int = Query(
        None, ge=0, le=100, description="Минимальный уровень опасности"
    ),
    max_danger: int = Query(
        None, ge=0, le=100, description="Максимальный уровень опасности"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Ищем существ по имени, категории и/или уровню опасности.

    Args:
        q (str, optional): Поиск по началу имени.
        category (str, optional): Фильтр по категории.
        min_danger (int, optional): Минимальный уровень опасности.
        max_danger (int, optional): Максимальный уровень опасности.
        db (AsyncSession: Асинхронная сессия базы данных.

    Returns:
        dict: Словарь с ключом 'существа' и список найденных существ.

    Raises:
        HTTPException: Если ничего не найдено (ошибка 404).
    """
    query = select(CreatureDB)

    # Фильтр по имени
    if q:
        query = query.filter(func.lower(CreatureDB.name).like(f"{q.lower()}%"))

    # Фильтр по категории
    if category:
        query = query.filter(CreatureDB.category == category)

    # Фильтро по уровню опасности
    if min_danger is not None:
        query = query.filter(CreatureDB.danger_level >= min_danger)
    if max_danger is not None:
        query = query.filter(CreatureDB.danger_level <= max_danger)

    result = await db.execute(query)
    creatures = result.scalars().all()

    if not creatures:
        raise HTTPException(
            status_code=404, detail="Существа с заданным фильтрам не найдены"
        )

    return {"Существа": [transform_creature(c) for c in creatures]}


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
    return {"Существа": [transform_creature(c) for c in creatures]}


@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Возвращает список всех категорий и количество существ в каждой.

    Args:
        db (AsyncSession): Асинхронная сессия для базы данных.

    Returns:
        dict: Словарь с ключом 'categories' и список категорий с их количеством.
    """
    # Группируем по категории и считаем количество
    result = await db.execute(
        select(CreatureDB.category, func.count(CreatureDB.id).label("count")).group_by(
            CreatureDB.category
        )
    )
    categories = result.all()

    return {
        "categories": [
            {"Имя": category, "Количество": count} for category, count in categories
        ]
    }


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
    return {"Опасные существа": [transform_creature(c) for c in creatures]}


@router.get("/random")
async def get_random_creature(
    category: str = Query(
        None, description="Категория для случайного выбора (например, 'Внешний Бог')"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Возвращает случайное существо из бестиария, опционально из указанной категории.

    Args:
        category (str, optional): Категория для фильтрации (например, 'Монстр', 'Внешний Бог'). Если не указана, выбирается из всех существ.
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        dict: Словарь с данными случайного существа.

    Raises:
        HTTPException: Если бестиарий пуст или в категории нет существ (404).

    Examples:
        - `/beastiary/random` - случайное существо из всех.
        - `/beastiary/random?category=Внешний Бог` - случайный Внешний Бог.
    """
    # Формируем запрос в зависимости от наличия категории
    if category:
        result = await db.execute(
            select(CreatureDB).filter(CreatureDB.category == category)
        )
    else:
        result = await db.execute(select(CreatureDB))

    creatures = result.scalars().all()

    if not creatures:
        if category:
            raise HTTPException(
                status_code=404, detail=f"В категории '{category}' нет существ!"
            )
        raise HTTPException(status_code=404, detail="Бестиарий пуст")

    random_creature = choice(creatures)
    return {"Существо": transform_creature(random_creature)}


@router.get("/stats")
async def get_beastiary_stats(db: AsyncSession = Depends(get_db)):
    """Возвращает статистику бестиария: общее число существ, средний уровень опасности
    и самого опасного.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        dict: Словарь со статистикой бестиария.

    Examples:
        - `/beastiary/stats` - возвращает общую статистику.
    """
    # Получаем общее число существ
    total_count = await db.scalar(select(func.count(CreatureDB.id)))
    # Получаем средний уровень опасности
    avg_danger = await db.scalar(select(func.avg(CreatureDB.danger_level)))
    # Получаем самое безопасное существо
    least_dangerous_result = await db.execute(
        select(CreatureDB.name, CreatureDB.danger_level)
        .order_by(CreatureDB.danger_level.asc())
        .limit(1)
    )
    least_dangerous = least_dangerous_result.first()

    # Получаем самое опасное существо
    most_dangerous_result = await db.execute(
        select(CreatureDB.name, CreatureDB.danger_level)
        .order_by(CreatureDB.danger_level.desc())
        .limit(1)
    )
    most_dangerous = most_dangerous_result.first()

    if total_count == 0:
        return {
            "Общее количество существ": 0,
            "Средний уровень опасности": 0.0,
            "Самое безопасное существо": None,
            "Самое опасное существо": None,
        }

    stats = {
        "Общее количество существ": total_count or 0,
        "Средний уровень опасности": round(float(avg_danger), 1) if avg_danger else 0.0,
        "Самое безопасное существо": (
            {
                "Имя": least_dangerous.name,
                "Уровень опасности": least_dangerous.danger_level,
            }
            if least_dangerous
            else None
        ),
        "Самое опасное существо": (
            {
                "Имя": most_dangerous.name,
                "Уровень опасности": most_dangerous.danger_level,
            }
            if most_dangerous
            else None
        ),
    }

    return stats


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
    return {"Существо": creature.name, "Сообщение": "Существо добавлено в бестиарий!"}


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
        "Сообщение": f"Существо '{creature_name}' обновлено",
        "Существо": transform_creature(db_creature),
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
    return {"Сообщение": f"{creature_name} удалён из бестиария!"}
