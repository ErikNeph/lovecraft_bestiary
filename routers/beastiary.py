from random import choice
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends ,HTTPException
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
        "related_works": creature.related_works.split(",") if creature.related_works else [],
        "image_url": creature.image_url,
        "status": creature.status,
        "min_insanity": creature.min_insanity,
        "relations": creature.relations.split(",") if creature.relations else [],
        "audio_url": creature.audio_url,
        "video_url": creature.video_url
    }


@router.get("/list")
def get_creatures(db: Session = Depends(get_db)):
    creatures = db.query(CreatureDB).all()
    return {"creatures": [transform_creature(c) for c in creatures]}


@router.get("/info/{creature_name}")
def get_creature_info(creature_name: str, db: Session = Depends(get_db)):
    creature = db.query(CreatureDB).filter(CreatureDB.name == creature_name).first()
    if not creature:
        raise HTTPException(status_code=404, detail="Существо не найдено в бестиарии!")
    return transform_creature(creature)


@router.post("/add")
def add_creature(creature: Creature, db: Session = Depends(get_db)):
    db_creature = db.query(CreatureDB).filter(CreatureDB.name == creature.name).first()
    if db_creature:
        raise HTTPException(status_code=400, detail="Это существо уже есть в бестиарии!")
    
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
    db.commit()
    db.refresh(new_creature)
    return {"creature": creature.name, "message": "Существо добавлено в бестиарий!"}


@router.delete("/remove/{creature_name}")
def remove_creature(creature_name: str, db: Session = Depends(get_db)):
    creature = db.query(CreatureDB).filter(CreatureDB.name == creature_name).first()
    if not creature:
        raise HTTPException(status_code=404, detail="Существо не найдено в бестиарии!")
    db.delete(creature)
    db.commit()
    return {"message": f"{creature_name} удалён из бестиария!"}


@router.get("/dangerous")
def get_dangerous_creatures(threshold: int = 50, db: Session = Depends(get_db)):
    creatures = db.query(CreatureDB).filter(CreatureDB.danger_level > threshold).all()
    return {"dangerous_creatures": [transform_creature(c) for c in creatures]}


@router.get("/random")
def get_random_creature(db: Session = Depends(get_db)):
    creatures = db.query(CreatureDB).all()
    if not creatures:
        raise HTTPException(status_code=404, detail="Бестиарий пуст!")
    return transform_creature(choice(creatures))
