import csv
import logging
from io import StringIO
from random import choice
from sqlalchemy import select, func
from sqlalchemy.sql import asc, desc  # noqa: F401
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from database import get_db
from models.creature import Creature, CreatureDB, CreatureUpdate
from models.models_for_docs import (
    ListBestiaryResponse,
    SearchCreaturesResponse,
    CreaturesByCategoryResponse,
    CategoriesResponse,
    DangerousCreaturesResponse,
    RandomCreatureResponse,
    StatsResponse,
    AddCreatureResponse,
    UpdateCreatureResponse,
    RemoveCreatureResponse,
    CreatureResponse,
)


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


@router.get(
    "/export",
    response_model=ListBestiaryResponse,
    summary="Экспортировать бестиарии",
    description="Экспортируем всех существ из бестиария в формат JSON или CSV.",
    responses={200: {"description": "Файл успешно экспортирован"}},
)
async def export_bestiary(
    format: str = Query(
        "json", description="Формат экспорта: 'json' или 'csv'", pattern="^(json|csv)$"
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
            content={
                "Существа": export_data_json,
                "Всего": len(export_data_json),
                "Лимит": len(export_data_json),
                "Смещение": 0,
            },
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


@router.get(
    "/list",
    response_model=ListBestiaryResponse,
    summary="Получить список существ из бестиария",
    description="Возвращает список существ из бестиария с пагинацией.",
    response_description="Список существ с информацией о пагинацией.",
    responses={
        200: {"description": "Список существ успешно возвращен"},
        404: {"description": "Существа не найдены"},
    },
)
async def list_bestiary(
    limit: int = Query(
        10, ge=1, le=100, description="Количество записей на странице (максимум 100)"
    ),
    offset: int = Query(0, ge=0, description="Смещение (с какой записи начинать)"),
    db: AsyncSession = Depends(get_db),
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
    print(f"Отладка: Всего записей в базе: {total_count}")

    # Получаем записи с пагинацей
    result = await db.execute(select(CreatureDB).limit(limit).offset(offset))
    creatures = result.scalars().all()

    print(f"Отладка: Найденные существа: {[creature.name for creature in creatures]}")
    logger.info(
        f"Возвращено {len(creatures)} существ на бестиария с limit={limit}, offset={offset}"
    )

    if not creatures:
        raise HTTPException(status_code=404, detail="Существа не найдены")

    logger.info(
        f"Возвращено {len(creatures)} существ на бестиария с limit={limit}, offset={offset}"
    )
    return {
        "Существа": [transform_creature(c) for c in creatures],
        "Всего": total_count,
        "Лимит": limit,
        "Смещение": offset,
    }


@router.get(
    "/info/{creature_name}",
    response_model=CreatureResponse,
    summary="Получить информацию о существе",
    description="Возвращает подробную информацию о существе по его имени.",
    response_description="Данные о существе",
    responses={
        200: {"description": "Информация о существе успешно возрващена"},
        404: {"description": "Существо не найдено в бестиарии"},
    },
)
async def get_creature_info(creature_name: str, db: AsyncSession = Depends(get_db)):
    """Получить информацию о существе по его имени.

    Args:
        creature_name (str): Имя существ (например, 'Йог-Сотот').
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        dict: Данные о существе в формате JSON.

    Raises:
        HTTPException: Если существо не найдено (404).
    """
    result = await db.execute(
        select(CreatureDB).filter(CreatureDB.name == creature_name)
    )
    creature = result.scalars().first()
    if not creature:
        raise HTTPException(status_code=404, detail="Существо не найдено в бестиарии!")
    return transform_creature(creature)


@router.get(
    "/search",
    response_model=SearchCreaturesResponse,
    summary="Поиск существ",
    description="Ищет существ по имени, категории и/или по уровню опасности.",
    response_description="Список найденных существ.",
    responses={
        200: {"description": "Существа найдены"},
        404: {"description": "Существа с заданными фильтрами не найдены"},
    },
)
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
        query = query.filter(func.lower(CreatureDB.name).ilike(f"{q}%"))

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


@router.get(
    "/category/{category_name}",
    response_model=CreaturesByCategoryResponse,
    summary="Получить существ по категории",
    description="Возвращает список существ, принадлежащих к указанной категории.",
    response_description="Список существ в категории.",
    responses={
        200: {"description": "Существа в категории найдены"},
        404: {"description": "Нет существ в указанной категории"},
    },
)
async def get_creatures_by_category(
    category_name: str, db: AsyncSession = Depends(get_db)
):
    """Получить список существ по категории.

    Args:
        category_name (str): Название категории (например 'Внешний Бог')
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        dict: Словарь с ключом 'Существа' и список существ.

    Raises:
        HTTPException: Если в категорий нет существ (404)
    """
    result = await db.execute(
        select(CreatureDB).filter(CreatureDB.category == category_name)
    )
    creatures = result.scalars().all()

    if not creatures:
        raise HTTPException(
            status_code=404, detail=f"Нет существ в категории '{category_name}'"
        )
    return {"Существа": [transform_creature(c) for c in creatures]}


@router.get(
    "/categories",
    response_model=CategoriesResponse,
    summary="Получить список категорий",
    description="Возвращает список всех категории и количество существ в каждой.",
    response_description="Список категории с количеством существ",
    responses={200: {"description": "Список категории успешно возвращён."}},
)
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Возвращает список всех категорий и количество существ в каждой категорий.

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


@router.get(
    "/dangerous",
    response_model=DangerousCreaturesResponse,
    summary="Получить опасных существ",
    description="Возвращает список существ с уровнем опасности в заданном диапазоне.",
    response_description="Список опасных существ.",
    responses={200: {"description": "Список опасных существ успешно возвращён"}},
)
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
    return {"Опасные_существа": [transform_creature(c) for c in creatures]}


@router.get(
    "/random",
    response_model=RandomCreatureResponse,
    summary="Получить случайное существо",
    description="Возвращает случайное существо из бестиария, опционально из указанной категории.",
    response_description="Случайное существо.",
    responses={
        200: {"description": "Случайное существо успешно возвращено"},
        404: {"description": "Бестиарии пуст или в категории нет существ"},
    },
)
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


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Получить статистику бестиария",
    description="Возвращает статистику бестиария: общее число существ, средний уровень опасности, самое безопасное и самое опасное существо.",
    response_description="Статистика бестиария",
    responses={200: {"description": "Статистика успешно возвращена"}},
)
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
            "Общее_количество": 0,
            "Средний_уровень": 0.0,
            "Самое_безопасное": None,
            "Самое_опасное": None,
        }

    stats = {
        "Общее_количество": total_count or 0,
        "Средний_уровень": round(float(avg_danger), 1) if avg_danger else 0.0,
        "Самое_безопасное": (
            {
                "Имя": least_dangerous.name,
                "Уровень_опасности": least_dangerous.danger_level,
            }
            if least_dangerous
            else None
        ),
        "Самое_опасное": (
            {
                "Имя": most_dangerous.name,
                "Уровень_опасности": most_dangerous.danger_level,
            }
            if most_dangerous
            else None
        ),
    }

    return stats


@router.post(
    "/add",
    response_model=AddCreatureResponse,
    summary="Добавить новое существо",
    description="Добавляет новое существо в бестиарии.",
    response_description="Сообщение об успешном добавлении",
    responses={
        200: {"description": "Существо успешно добавлено"},
        400: {"description": "Существо уже существует в бестиарии"},
    },
)
async def add_creature(creature: Creature, db: AsyncSession = Depends(get_db)):
    """Добавляет новое существо в бестиарий.

    Args:
        creature (Creature): Данные нового существа (Pydantic-модели).
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        dict: Сообщение об успешном удалении.

    Raises:
        HTTPException: Если существа с таким именем уже есть (400).
    """
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


@router.put(
    "/update/{creature_name}",
    response_model=UpdateCreatureResponse,
    summary="Обновить данные существа.",
    description="Обновляет данные существа в бестиарии по его имени",
    response_description="Сообщение об успешном обновлении и обновленные данные существа.",
    responses={
        200: {"description": "Существо успешно обновлено"},
        404: {"description": "Существо не найдено"},
    },
)
async def update_creature(
    creature_name: str,
    creature_update: CreatureUpdate,
    db: AsyncSession = Depends(get_db),
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
    query = select(CreatureDB).where(CreatureDB.name == creature_name)
    result = await db.execute(query)
    creature = result.scalar_one_or_none()

    if not creature:
        raise HTTPException(status_code=404, detail="Существо не найдено в бестиарии!")

    for key, value in creature_update.model_dump(exclude_unset=True).items():
        if key in ["abilities", "related_works", "relations"] and value is not None:
            value = ",".join(value)
        if value is not None:
            setattr(creature, key, value)

    await db.commit()
    await db.refresh(creature)

    # Преобразуем объект creature в словарь с русифицированными ключами !ДЛЯ ТЕСТИРОВАНИЯ!.
    creature_dict = {
        "Id": creature.id,
        "Имя": creature.name,
        "Описание": creature.description,
        "Уровень_опасности": creature.danger_level,
        "Среда_обитания": creature.habitat,
        "Цитата": creature.quote,
        "Категория": creature.category,
        "Способности": creature.abilities,
        "Связанные_произведения": creature.related_works,
        "Url_изображения": creature.image_url,
        "Статус": creature.status,
        "Минимальное_безумие": creature.min_insanity,
        "Связи": creature.relations,
        "Url_аудио": creature.audio_url,
        "Url_видео": creature.video_url,
    }

    return {
        "Сообщение": f"Существо '{creature_name}' обновлено",
        "Существо": creature_dict,
    }


@router.delete(
    "/remove/{creature_name}",
    response_model=RemoveCreatureResponse,
    summary="Удалить существо",
    description="Удаляет существо из бестиария по его имени.",
    response_description="Сообщение об успешном удалении.",
    responses={
        200: {"description": "Существо успешно удалено"},
        404: {"description": "Существо не найдено в бестиарии"},
    },
)
async def remove_creature(creature_name: str, db: AsyncSession = Depends(get_db)):
    """Удаляет существо из бестиария по его имени.

    Args:
        creature_name (str): Имя существа для удаления (например, 'Ктулху').
        db (AsyncSession): Асинхронная сессия базы данных.

    Returns:
        dict: Сообщение об успешном удалении.

    Raises:
        HTTPException: Если существо не найдено (404).
    """
    result = await db.execute(
        select(CreatureDB).filter(CreatureDB.name == creature_name)
    )
    creature = result.scalars().first()
    if not creature:
        raise HTTPException(status_code=404, detail="Существо не найдено в бестиарии!")
    await db.delete(creature)
    await db.commit()
    return {"Сообщение": f"{creature_name} удалён из бестиария!"}
