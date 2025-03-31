import csv
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


def transform_creature(creature: CreatureDB) -> dict:
    """Преобразует строковые поля в списки."""

    def clean_string(text):
        """Для очистки строк от лишних \n"""
        if isinstance(text, str):
            return text.replace("\n", " ").strip()
        return text

    return {
        "Id": creature.id,
        "Имя": clean_string(creature.name),
        "Описание": clean_string(creature.description),
        "Уровень_опасности": creature.danger_level,
        "Среда_обитания": clean_string(creature.habitat),
        "Цитата": clean_string(creature.quote),
        "Категория": clean_string(creature.category),
        "Способности": ", ".join(
            [
                clean_string(ability)
                for ability in (
                    creature.abilities.split(",") if creature.abilities else []
                )
            ]
        ),
        "Связанные_произведения": ", ".join(
            [
                clean_string(work)
                for work in (
                    creature.related_works.split(",") if creature.related_works else []
                )
            ]
        ),
        "Url_изображения": creature.image_url,
        "Статус": clean_string(creature.status),
        "Минимальное_безумие": creature.min_insanity,
        "Связи": ", ".join(
            [
                clean_string(relation)
                for relation in (
                    creature.relations.split(",") if creature.relations else []
                )
            ]
        ),
        "Url_аудио": creature.audio_url,
        "Url_видео": creature.video_url,
    }


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
    export_data = [transform_creature(c) for c in creatures]
    
    # Отладочный вывод
    print(f"Export data: {export_data}")
    print(f"Export data length: {len(export_data)}")
    if export_data:
        print(f"First item type: {type(export_data[0])}")

    if format == "json":
        return JSONResponse(
            content={"Существа": export_data},
            headers={"Content-Disposition": "attachment; filename=bestiary_export.json"},
            media_type="application/json"
        )
    elif format == "csv":
        # Создаём CSV в памяти
        output = StringIO()
        fieldnames = ["Id", "Имя", "Описание", "Уровень_опасности", "Среда_обитания", "Цитата", "Категория", "Способности", "Связанные_произведения", "Url_изображения", "Статус", "Минимальное_безумие", "Связи", "Url_аудио", "Url_видео"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        
        # Записываем данные, если они есть
        if export_data:
            writer.writerows(export_data)
        
        return Response(
            content=output.getvalue(),
            headers={"Content-Disposition": "attachment; filename=bestiary_export.csv"},
            media_type="text/csv"
        )


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
    sort_field = {"name": CreatureDB.name, "danger_level": CreatureDB.danger_level}[
        sort
    ]
    sort_order = asc if order == "asc" else desc

    # Выполняем запрос с сортировкой
    result = await db.execute(select(CreatureDB).order_by(sort_order(sort_field)))
    creatures = result.scalars().all()

    return {"Существа": [transform_creature(c) for c in creatures]}


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
    return {"Существо": creature.name, "message": "Существо добавлено в бестиарий!"}


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
