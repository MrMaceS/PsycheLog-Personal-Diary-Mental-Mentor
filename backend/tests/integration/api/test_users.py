from tests.helpers import make_user_data


def test_get_current_user(client):
    user_data = make_user_data()

    register_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201, register_response.text

    tokens = register_response.json()

    response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert data["display_name"] == user_data["display_name"]


def test_get_current_user_without_token(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code in (401, 403)


def test_update_current_user(client):
    user_data = make_user_data()

    register_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201

    tokens = register_response.json()

    response = client.patch(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
        json={
            "display_name": "Новое имя",
            "avatar_url": "https://example.com/avatar.png",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["display_name"] == "Новое имя"
    assert data["avatar_url"] == "https://example.com/avatar.png"


def test_update_user_consents(client):
    user_data = make_user_data()

    register_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201

    tokens = register_response.json()

    response = client.patch(
        "/api/v1/users/me/consents",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
        json={
            "consent_data_processing": True,
            "consent_local_cache": True,
            "consent_cloud_ai": False,
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["consent_data_processing"] is True
    assert data["consent_local_cache"] is True
    assert data["consent_cloud_ai"] is False


def test_delete_account(client):
    user_data = make_user_data()

    register_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201

    tokens = register_response.json()

    response = client.request(
        "DELETE",
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
        json={
            "pin": user_data["pin"],
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "Аккаунт удалён"

    profile_response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
    )

    assert profile_response.status_code == 401


def test_delete_account_with_wrong_pin(client):
    user_data = make_user_data()

    register_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201

    tokens = register_response.json()

    response = client.request(
        "DELETE",
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
        json={
            "pin": "9999",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Неверный PIN"