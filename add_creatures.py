import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database import engine
from models.creature import CreatureDB


async def add_creatures():
    async with AsyncSession(engine) as db:
        new_creatures = [
            CreatureDB(
                name="Шоготты",
                description="Амёбоподобные создания, созданные Древними как рабы, но восставшие против своих хозяев.",
                danger_level=60,
                habitat="Подземные города и Антарктика",
                category="Раса",
                status="Активны",
                abilities="изменение формы,сверхсила,разъедание",
                quote="Текели-ли! Текели-ли!",
                related_works="Хребты Безумия",
                image_url="https://static.wikia.nocookie.net/lovecraft/images/e/e1/MfLvnp9FEH4.jpg/revision/latest?cb=20160223125500&path-prefix=ru",
                video_url="https://www.youtube.com/watch?v=6iVXiQ8FoC4&t=23s&ab_channel=Valaybalalay"
            ),
            CreatureDB(
                name="Хастур",
                description="Неназываемый, Король в Жёлтом, загадочное божество, приносящее безумие и хаос.",
                danger_level=90,
                habitat="Звезда Каркоза",
                category="Внешний Бог",
                status="Существует",
                abilities="безумие,манипуляция реальностью,телепортация",
                quote="Ты видел Жёлтый Знак?",
                related_works="Король в жёлтом",
                video_url="https://www.youtube.com/watch?v=HmpitUA-H3w&ab_channel=KTHULHU%2F%D0%9A%D0%A2%D0%A3%D0%9B%D0%A5%D0%A3",
                image_url="https://static.wikia.nocookie.net/anime-characters-fight/images/f/ff/0_c39a8_b950d5e5_orig_%281%29.jpg/revision/latest?cb=20150503170929&path-prefix=ru",
                relations="Ньярлатотеп",
            )
        ]
        db.add_all(new_creatures)
        await db.commit()
        print("Новые существа добавлены, во славу Древних!")


if __name__ == "__main__":
    asyncio.run(add_creatures())
