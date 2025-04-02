from typing import List, Optional
from pydantic import BaseModel, HttpUrl, ConfigDict


class CreatureResponse(BaseModel):
    Id: int
    Имя: str
    Описание: str
    Уровень_опасности: int  # Изменяем на int
    Среда_обитания: str
    Цитата: str
    Категория: str
    Способности: str
    Связанные_произведения: str
    Url_изображения: Optional[HttpUrl] = None
    Статус: str
    Минимальное_безумие: int  # Изменяем на int
    Связи: str
    Url_аудио: Optional[HttpUrl] = None
    Url_видео: Optional[HttpUrl] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "Id": 1,
                "Имя": "Йог-Сотот",
                "Описание": "Ключ и врата",
                "Уровень_опасности": 100,
                "Среда_обитания": "Вне пространства и времени",
                "Цитата": "Прошлое, настоящее и будущее, всё в руках Йог-Сотота.",
                "Категория": "Внешний Бог",
                "Способности": "Всезнание, Бессмертие, Управление временем",
                "Связанные_произведения": "Ужас Данвича, Ночь в музее",
                "Url_изображения": "https://static.wikia.nocookie.net/zlodei/images/6/6f/Main-qimg-faf9b8ff02eaf92b6af6de9a77210d0b.jpg/revision/latest?cb=20200523143046&path-prefix=ru",
                "Статус": "За пределами смерти и жизни",
                "Минимальное_безумие": 90,
                "Связи": "Азатот",
                "Url_аудио": "https://knigavuhe.org/book/4099-uzhas-danvicha/",
                "Url_видео": "https://www.youtube.com/watch?v=cVxuoekM4UI",
            }
        }
    )


class ListBestiaryResponse(BaseModel):
    Существа: List[CreatureResponse]
    Всего: int
    Лимит: int
    Смещение: int


class SearchCreaturesResponse(BaseModel):
    Существа: List[CreatureResponse]


class CreaturesByCategoryResponse(BaseModel):
    Существа: List[CreatureResponse]


class Category(BaseModel):
    Имя: str
    Количество: int


class CategoriesResponse(BaseModel):
    categories: List[Category]


class DangerousCreaturesResponse(BaseModel):
    Опасные_существа: List[CreatureResponse]


class RandomCreatureResponse(BaseModel):
    Существо: CreatureResponse


class DangerStat(BaseModel):
    Имя: str
    Уровень_опасности: int  # Изменяем на int


class StatsResponse(BaseModel):
    Общее_количество: int
    Средний_уровень: float
    Самое_безопасное: Optional[DangerStat]
    Самое_опасное: Optional[DangerStat]


class AddCreatureResponse(BaseModel):
    Существо: str
    Сообщение: str


class UpdateCreatureResponse(BaseModel):
    Сообщение: str
    Существо: CreatureResponse


class RemoveCreatureResponse(BaseModel):
    Сообщение: str
