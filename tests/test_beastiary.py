from fastapi.testclient import TestClient


# Тест для корневого маршрута
def test_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["Сообщение"] == "Добро пожаловать в Бестиарий Лавкрафта!"


def test_search_bestiary(client: TestClient, setup_test_data):
    # Поиск по имени
    response = client.get("/beastiary/search?q=Йог")
    assert response.status_code == 200
    data = response.json()
    assert len(data["Существа"]) == 1
    assert data["Существа"][0]["Имя"] == "Йог-Сотот"

    # Поиск по категории
    response = client.get("/beastiary/search?category=Внешний Бог")
    assert response.status_code == 200
    data = response.json()
    assert len(data["Существа"]) == 2
    assert data["Существа"][0]["Имя"] == "Йог-Сотот"
    assert data["Существа"][1]["Имя"] == "Шуб-Ниггурат"

    # Поиск по уровню опасности
    response = client.get("/beastiary/search?min_danger=80&max_danger=100")
    assert response.status_code == 200
    data = response.json()
    assert len(data["Существа"]) == 2
    assert data["Существа"][0]["Имя"] == "Йог-Сотот"
    assert data["Существа"][1]["Имя"] == "Шуб-Ниггурат"

    # Ничего не найдено
    response = client.get("/beastiary/search?q=Ктулху")
    assert response.status_code == 404
    assert response.json()["detail"] == "Существа с заданным фильтрам не найдены"


def test_export_bestiary(client: TestClient, setup_test_data):
    # Экспорт в JSON
    response = client.get("/beastiary/export?format=json")
    assert response.status_code == 200
    assert (
        response.headers["content-disposition"]
        == "attachment; filename=bestiary_export.json"
    )
    data = response.json()
    assert len(data["Существа"]) == 3

    # Экспорт в CSV
    response = client.get("/beastiary/export?format=csv")
    assert response.status_code == 200
    assert (
        response.headers["content-disposition"]
        == "attachment; filename=bestiary_export.csv"
    )
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    content = response.text
    assert "Йог-Сотот" in content
    assert "Шуб-Ниггурат" in content
    assert "Глубоководные" in content


def test_get_creature_info(client: TestClient, setup_test_data):
    # Успешный запрос
    response = client.get("/beastiary/info/Йог-Сотот")
    assert response.status_code == 200
    data = response.json()
    assert data["Имя"] == "Йог-Сотот"

    # Существо не найдено
    response = client.get("/beastiary/info/Ктулху")
    assert response.status_code == 404
    assert response.json()["detail"] == "Существо не найдено в бестиарии!"


def test_get_creatures_by_category(client: TestClient, setup_test_data):
    # Успешный запрос
    response = client.get("/beastiary/category/Внешний Бог")
    assert response.status_code == 200
    data = response.json()
    assert len(data["Существа"]) == 2
    assert data["Существа"][0]["Имя"] == "Йог-Сотот"
    assert data["Существа"][1]["Имя"] == "Шуб-Ниггурат"

    # Категория не найдена
    response = client.get("/beastiary/category/Древний")
    assert response.status_code == 404
    assert response.json()["detail"] == "Нет существ в категории 'Древний'"


def test_get_categories(client: TestClient, setup_test_data):
    response = client.get("/beastiary/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data["categories"]) == 2
    assert data["categories"][0]["Имя"] == "Внешний Бог"
    assert data["categories"][0]["Количество"] == 2
    assert data["categories"][1]["Имя"] == "Раса"
    assert data["categories"][1]["Количество"] == 1


def test_get_dangerous_creatures(client: TestClient, setup_test_data):
    # Успешный запрос
    response = client.get("/beastiary/dangerous?min=80&max=100")
    assert response.status_code == 200
    data = response.json()
    assert len(data["Опасные_существа"]) == 2
    assert data["Опасные_существа"][0]["Имя"] == "Йог-Сотот"
    assert data["Опасные_существа"][1]["Имя"] == "Шуб-Ниггурат"


def test_get_random_creature(client: TestClient, setup_test_data):
    # Случайное существо
    response = client.get("/beastiary/random")
    assert response.status_code == 200
    data = response.json()
    assert "Существо" in data
    assert data["Существо"]["Имя"] in ["Йог-Сотот", "Шуб-Ниггурат", "Глубоководные"]

    # Случайное существо из категории
    response = client.get("/beastiary/random?category=Внешний Бог")
    assert response.status_code == 200
    data = response.json()
    assert data["Существо"]["Имя"] in ["Йог-Сотот", "Шуб-Ниггурат"]

    # Категория не найдена
    response = client.get("/beastiary/random?category=Древний")
    assert response.status_code == 404
    assert response.json()["detail"] == "В категории 'Древний' нет существ!"


def test_get_bestiary_stats(client: TestClient, setup_test_data):
    response = client.get("/beastiary/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["Общее_количество"] == 3
    assert data["Средний_уровень"] == 75.0  # (100 + 85 + 40) / 3
    assert data["Самое_безопасное"]["Имя"] == "Глубоководные"
    assert data["Самое_безопасное"]["Уровень_опасности"] == 40
    assert data["Самое_опасное"]["Имя"] == "Йог-Сотот"
    assert data["Самое_опасное"]["Уровень_опасности"] == 100


def test_add_update_remove_creature(client: TestClient, db_session):
    # Добавляем новое существо
    new_creature = {
        "name": "Ктулху",
        "description": "Великий Древний, спящий в Р'льехе",
        "danger_level": 95,
        "habitat": "Океан",
        "quote": "Фхтагн!",
        "category": "Древний",
        "abilities": ["телепатия", "контроль разума"],
        "related_works": ["Зов Ктулху"],
        "image_url": "https://example.com/cthulhu.jpg",
        "status": "Спит",
        "min_insanity": 80,
        "relations": ["Дагон"],
        "audio_url": None,
        "video_url": "https://youtube.com/cthulhu",
    }
    response = client.post("/beastiary/add", json=new_creature)
    assert response.status_code == 200
    data = response.json()
    assert data["Существо"] == "Ктулху"
    assert data["Сообщение"] == "Существо добавлено в бестиарий!"

    # Проверяем, что существо добавлено
    response = client.get("/beastiary/info/Ктулху")
    assert response.status_code == 200
    data = response.json()
    assert data["Имя"] == "Ктулху"

    # Обновляем существо
    updated_creature = {
        "description": "Великий Древний, пробудившийся в Р'льехе",
        "danger_level": 96,
    }
    response = client.put("/beastiary/update/Ктулху", json=updated_creature)
    assert response.status_code == 200
    data = response.json()
    assert data["Сообщение"] == "Существо 'Ктулху' обновлено"
    assert data["Существо"]["Описание"] == "Великий Древний, пробудившийся в Р'льехе"
    assert data["Существо"]["Уровень_опасности"] == 96

    # Удаляем существо
    response = client.delete("/beastiary/remove/Ктулху")
    assert response.status_code == 200
    data = response.json()
    assert data["Сообщение"] == "Ктулху удалён из бестиария!"

    # Проверяем, что существо удалено
    response = client.get("/beastiary/info/Ктулху")
    assert response.status_code == 404
    assert response.json()["detail"] == "Существо не найдено в бестиарии!"
