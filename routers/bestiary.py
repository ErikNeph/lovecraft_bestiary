from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class Creature(BaseModel):
    name: str
    description: str
    danger_level: int  # Уровень угрозы (1-100)


# Временная база существ
creatures = [
    {
        "name": "Ктулху",
        "description": "Спящий в Р’льехе, ждёт звёзд",
        "danger_level": 100,
    },
    {
        "name": "Шоггот",
        "description": "Аморфное создание из текучей плоти",
        "danger_level": 70,
    },
]


@router.get("/list")
def get_creatures():
    return {"creatures": creatures}


@router.post("/add")
def add_creature(creature: Creature):
    if any(c["name"] == creature.name for c in creatures):
        raise HTTPException(
            status_code=400, detail="Это существо уже есть в бестиарии!"
        )
    creatures.append(creature.dict())
    return {"creature": creature.name, "message": "Существо добавлено в бестиарий!"}
