from typing import Optional
from sqlalchemy import Column, Integer, String, Text
from pydantic import BaseModel, Field, ConfigDict ,conlist
from database import Base


class CreatureDB(Base):
    __tablename__ = "creatures"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    danger_level = Column(Integer, nullable=False)
    habitat = Column(String(100), nullable=False)
    quote = Column(String(400), nullable=True)
    category = Column(String(30), nullable=False)
    abilities = Column(Text, nullable=True)
    related_works = Column(Text, nullable=True)
    image_url = Column(String(350), nullable=True)
    status = Column(String(30), nullable=False)
    min_insanity = Column(Integer, nullable=False, default=0)
    relations = Column(Text, nullable=True)
    audio_url = Column(String(350), nullable=True)
    video_url = Column(String(350), nullable=True)


class Creature(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=3, max_length=50, description="Названия(имя) существа")
    description: str = Field(..., min_length=10, max_length=500, description="Описания существа")
    danger_level: int = Field(..., ge=1, le=100, description="Уровень угрозы (1-100)")
    habitat: str = Field(..., min_length=2, max_length=100, description="Место обитания")
    quote: str = Field(None, max_length=400, description="Цитата или фраза, связанная с существом")
    category: str = Field(..., min_length=3, max_length=30,description="Категория существа (Древний, Иной(Внешний), Страший, Звездная раса и т.д.)")
    abilities: conlist(str, max_length=15) = Field([], description="Список способностей (максимум 15)")  # type: ignore
    related_works: conlist(str, max_length=50) = Field([], description="Произведения где упоминается существо (максимум 50)")  # type: ignore
    image_url: Optional[str] = Field(None, max_length=350, description="URL изображения существа")
    status: str = Field(..., min_length=3, max_length=30, description="Текущий статус (живой, мертвый, спящий и т.д.)")
    min_insanity: int = Field(0, ge=0, le=100, description="Минимальное безумие для призыва")
    relations: conlist(str, max_length=20) = Field([], description="Связанные существа (максимум 20)")  # type: ignore
    audio_url: Optional[str] = Field(None, max_length=350, description="URL аудиозаписи с описанием существ")
    video_url: Optional[str] = Field(None, max_length=350, description="URL видео о существе")


class CreatureUpdate(BaseModel):
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    danger_level: Optional[int] = Field(None, ge=1, le=100)
    habitat: Optional[str] = Field(None, min_length=2, max_length=100)
    quote: Optional[str] = Field(None, max_length=400)
    category: Optional[str] = Field(None, min_length=3, max_length=30)
    abilities: Optional[conlist(str, max_length=15)] = Field(None)  # type: ignore
    related_works: Optional[conlist(str, max_length=50)] = Field(None)  # type: ignore
    image_url: Optional[str] = Field(None, max_length=350)
    status: Optional[str] = Field(None, min_length=3, max_length=30)
    min_insanity: Optional[int] = Field(None, ge=0, le=100)
    relations: Optional[conlist(str, max_length=20)] = Field(None)  # type: ignore
    audio_url: Optional[str] = Field(None, max_length=350)
    video_url: Optional[str] = Field(None, max_length=350)


# Определяем модель ответа для документации
# class CreatureResponse(BaseModel):
#     Id: int
#     Имя: str
#     Описание: str
#     Уровень_опасности: int
#     Среда_обитания: str
#     Цитата: str
#     Категория: str
#     Способности: str