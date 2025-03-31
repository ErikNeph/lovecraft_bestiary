import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from database import engine
from models.creature import CreatureDB

# Устанавливаем кодировку для консоли
if sys.platform == "win32":
    import os
    os.system("chcp 65001")
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

async def add_creatures():
    async with AsyncSession(engine) as db:
        new_creatures = [
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
                quote="Мне показалось, что в своей массе они были серовато-зеленого цвета, но с белыми животами. Большинство из них блестели и казались осклизлыми, а края их спин были покрыты чем-то вроде чешуи.",
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
            CreatureDB(
                name="Ньярлатотеп",
                description="Ползущий Хаос с тысячью ликов, посланник внешних богов, обманщик и разрушитель.",
                danger_level=95,
                habitat="Межпространственные врата",
                quote="Я — голос Азатота, шепчущий в пустоте.",
                category="Внешний Бог",
                abilities="обман,телепортация,контроль разума",
                related_works="Ползущий Хаос,Маска Ньярлатотепа",
                image_url="https://static.wikia.nocookie.net/some-charasters/images/6/60/Ni23.png/revision/latest/scale-to-width-down/732?cb=20230416135623&path-prefix=ru",
                status="Активен",
                min_insanity=0,
                relations="",
                audio_url=None,
                video_url="https://www.youtube.com/watch?v=95SNbOH27BA&t=42s&ab_channel=Lore"
            ),
            CreatureDB(
                name="Азатот",
                description="Ядерный хаос или же Султан Демонов",
                danger_level=100,
                habitat="Центр Космоса",
                quote="Вся наша реальность, это всего лишь миг сна Азатота.",
                category="Внешний Бог",
                abilities="Разрушение,Безумие,Созидание,Бессмертие",
                related_works="Некрономикон,Сны в ведьмином доме,Ужас в музее,Обитающий во тьме,Тварь на пороге",
                image_url="https://upload.wikimedia.org/wikipedia/commons/2/28/Azathoth.jpg",
                status="Спит",
                min_insanity=100,
                relations="Ньярлатотеп",
                audio_url="https://akniga.org/lavkraft-govard-azatot-potomok-kniga",
                video_url="https://www.youtube.com/watch?v=4V9N6g05hLs&t=342s&ab_channel=Lore"
            ),
            CreatureDB(
                name="Дагон",
                description="Отец Глубоководных, древний морской бог, покровитель подводных тварей.",
                danger_level=70,
                habitat="Глубины океана",
                quote="Из пучин он зовёт своих детей.",
                category="Древний",
                abilities="контроль воды,призыв Глубоководных,Вселяет ужас в людей",
                related_works="Тень над Иннсмутоом,Дагон",
                image_url="https://lovecraft.country/images/bestiary/dagon/d2.webp",
                status="Активен",
                min_insanity=0,
                relations="Глубоководные,Гидра,Ктулху",
                audio_url=None,
                video_url="https://www.youtube.com/watch?v=azsJvpwWTIo&ab_channel=KTHULHU%2F%D0%9A%D0%A2%D0%A3%D0%9B%D0%A5%D0%A3"
            ),
            CreatureDB(
                name="Гхасты",
                description="Светящиеся твари из подземных пещер, пожирающие всё на своём пути.",
                danger_level=40,
                habitat="Подземелья Сновидений",
                quote="Их визги эхом разносятся в тёмных глубинах.",
                category="Раса",
                abilities="ночное зрение,быстрая регенерация",
                related_works="Сомнамбулический поиск неведомого Кадата",
                image_url=None,
                status="Активны",
                min_insanity=0,
                relations="",
                audio_url=None,
                video_url=None
            ),
            CreatureDB(
                name="Ми-Го",
                description="Инопланетные существа, напоминающие насекомых, мастера хирургии и технологий.",
                danger_level=60,
                habitat="Юггот и горы Вермонта",
                quote="Их крылья жужжат в ночи, унося разумы смертных.",
                category="Звездная раса",
                abilities="полёт,извлечение мозга,мимикрия",
                related_works="Шепчущий во тьме,Грибы Юггота",
                image_url=None,
                status="Активны",
                min_insanity=0,
                relations="",
                audio_url=None,
                video_url="https://www.youtube.com/watch?v=cDSoFzuU3TA&ab_channel=Valaybalalay"
            ),
            CreatureDB(
                name="Шоготты",
                description="Амёбоподобные создания, созданные Древними как рабы, но восставшие против своих хозяев.",
                danger_level=60,
                habitat="Подземные города и Антарктика",
                quote="Текели-ли! Текели-ли!",
                category="Раса",
                abilities="изменение формы,сверхсила,разъедание",
                related_works="Хребты Безумия",
                image_url="https://static.wikia.nocookie.net/lovecraft/images/e/e1/MfLvnp9FEH4.jpg/revision/latest?cb=20160223125500&path-prefix=ru",
                status="Активны",
                min_insanity=0,
                relations="",
                audio_url=None,
                video_url="https://www.youtube.com/watch?v=6iVXiQ8FoC4&t=23s&ab_channel=Valaybalalay"
            ),
            CreatureDB(
                name="Хастур",
                description="Неназываемый, Король в Жёлтом, загадочное божество, приносящее безумие и хаос.",
                danger_level=90,
                habitat="Звезда Каркоза",
                quote="Ты видел Жёлтый Знак?",
                category="Внешний Бог",
                abilities="безумие,манипуляция реальностью,телепортация",
                related_works="Король в жёлтом",
                image_url="https://static.wikia.nocookie.net/anime-characters-fight/images/f/ff/0_c39a8_b950d5e5_orig_%281%29.jpg/revision/latest?cb=20150503170929&path-prefix=ru",
                status="Существует",
                min_insanity=0,
                relations="Ньярлатотеп",
                audio_url=None,
                video_url="https://www.youtube.com/watch?v=HmpitUA-H3w&ab_channel=KTHULHU%2F%D0%9A%D0%A2%D0%A3%D0%9B%D0%A5%D0%A3"
            )
        ]
        db.add_all(new_creatures)
        await db.commit()
        print("Новые существа добавлены, во славу Древних!")

if __name__ == "__main__":
    asyncio.run(add_creatures())
