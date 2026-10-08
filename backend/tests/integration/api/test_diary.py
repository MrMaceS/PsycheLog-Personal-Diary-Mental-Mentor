from tests.helpers import make_user_data


def register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json=make_user_data(),
    )

    assert response.status_code == 201, response.text
    return response.json()


def create_entry(client, access_token):
    response = client.post(
        "/api/v1/diary/",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "title": "Первая запись",
            "content": "Текст записи",
            "mood": "happy",
            "tags": "тест,день1",
        },
    )

    assert response.status_code == 200, response.text
    return response.json()


def test_create_diary_entry(client):
    tokens = register_user(client)

    data = create_entry(client, tokens["access_token"])

    assert data["title"] == "Первая запись"
    assert data["content"] == "Текст записи"
    assert data["mood"] == "happy"
    assert data["tags"] == "тест,день1"
    assert data["user_id"] is not None
    assert data["is_deleted"] is False


def test_list_diary_entries(client):
    tokens = register_user(client)
    token = tokens["access_token"]

    create_entry(client, token)

    response = client.get(
        "/api/v1/diary/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Первая запись"


def test_list_diary_entries_with_pagination(client):
    tokens = register_user(client)
    token = tokens["access_token"]

    create_entry(client, token)
    create_entry(client, token)

    response = client.get(
        "/api/v1/diary/?limit=1&offset=1",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_diary_entry(client):
    tokens = register_user(client)
    token = tokens["access_token"]

    entry = create_entry(client, token)

    response = client.get(
        f"/api/v1/diary/{entry['id']}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == entry["id"]


def test_get_nonexistent_diary_entry(client):
    tokens = register_user(client)
    token = tokens["access_token"]

    response = client.get(
        "/api/v1/diary/999999",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Запись не найдена"


def test_update_diary_entry(client):
    tokens = register_user(client)
    token = tokens["access_token"]

    entry = create_entry(client, token)

    response = client.patch(
        f"/api/v1/diary/{entry['id']}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "title": "Обновлённая запись",
            "content": "Обновлённый текст",
            "mood": "calm",
            "tags": "обновлено",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["id"] == entry["id"]
    assert data["title"] == "Обновлённая запись"
    assert data["content"] == "Обновлённый текст"
    assert data["mood"] == "calm"
    assert data["tags"] == "обновлено"


def test_update_diary_entry_partially(client):
    tokens = register_user(client)
    token = tokens["access_token"]

    entry = create_entry(client, token)

    response = client.patch(
        f"/api/v1/diary/{entry['id']}",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "title": "Только новый заголовок",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["title"] == "Только новый заголовок"
    assert data["content"] == entry["content"]
    assert data["mood"] == entry["mood"]
    assert data["tags"] == entry["tags"]


def test_update_nonexistent_diary_entry(client):
    tokens = register_user(client)
    token = tokens["access_token"]

    response = client.patch(
        "/api/v1/diary/999999",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "title": "Новый заголовок",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Запись не найдена"


def test_delete_diary_entry(client):
    tokens = register_user(client)
    token = tokens["access_token"]

    entry = create_entry(client, token)

    response = client.delete(
        f"/api/v1/diary/{entry['id']}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Запись удалена"}

    get_response = client.get(
        f"/api/v1/diary/{entry['id']}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert get_response.status_code == 404


def test_delete_nonexistent_diary_entry(client):
    tokens = register_user(client)
    token = tokens["access_token"]

    response = client.delete(
        "/api/v1/diary/999999",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Запись не найдена"


def test_create_diary_without_token(client):
    response = client.post(
        "/api/v1/diary/",
        json={
            "title": "Без токена",
            "content": "Текст",
        },
    )

    assert response.status_code == 401


def test_list_diary_without_token(client):
    response = client.get("/api/v1/diary/")
    assert response.status_code == 401


def test_get_diary_without_token(client):
    response = client.get("/api/v1/diary/1")
    assert response.status_code == 401