import pytest
from fastapi.testclient import TestClient

# Настраиваем pytest для асинхронных тестов
pytestmark = pytest.mark.asyncio


# Тест для корневого маршрута
def test_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["Сообщение"] == "Добро пожаловать в Бестиарий Лавкрафта!"


# Тесты для маршрутов бестиария
def test_list_bestiary(client: TestClient, setup_test_data):
    # Тест с пагинацией: первые 2 существа
    response = client.get("/beastiary/list?limit=2&offset=0")
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}: {response.text}"
    data = response.json()
    print(f"Существа в ответе: {data['Существа']}")
    assert len(data["Существа"]) == 2, f"Expected 2 creatures, got {len(data['Существа'])}"
    assert data["Всего"] == 3, f"Expected total 3, got {data['Всего']}"
    assert data["Лимит"] == 2
    assert data["Смещение"] == 0
    assert data["Существа"][0]["Имя"] == "Йог-Сотот"
    assert data["Существа"][1]["Имя"] == "Шуб-Ниггурат"

    # Тест с пагинацией: пропускаем первые 2 существа
    response = client.get("/beastiary/list?limit=2&offset=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["Существа"]) == 1
    assert data["Существа"][0]["Имя"] == "Глубоководные"

    # Тест с пустым результатом (слишком большое смещение)
    response = client.get("/beastiary/list?limit=2&offset=10")
    assert response.status_code == 404
    assert response.json()["detail"] == "Существа не найдены"


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
    assert len(data["Опасные существа"]) == 2
    assert data["Опасные существа"][0]["Имя"] == "Йог-Сотот"
    assert data["Опасные существа"][1]["Имя"] == "Шуб-Ниггурат"


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
    assert data["Общее количество существ"] == 3
    assert data["Средний уровень опасности"] == 75.0  # (100 + 85 + 40) / 3
    assert data["Самое безопасное существо"]["Имя"] == "Глубоководные"
    assert data["Самое безопасное существо"]["Уровень опасности"] == 40
    assert data["Самое опасное существо"]["Имя"] == "Йог-Сотот"
    assert data["Самое опасное существо"]["Уровень опасности"] == 100


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
