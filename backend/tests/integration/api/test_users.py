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


def test_revoke_cloud_ai_consent(client):
    """Тест обновления и отзыва согласия на использование облачного AI."""
    user_data = make_user_data()

    register_response = client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 201
    tokens = register_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    enable_response = client.patch(
        "/api/v1/users/me/consents",
        headers=headers,
        json={
            "consent_data_processing": True,
            "consent_local_cache": True,
            "consent_cloud_ai": True,
        },
    )
    assert enable_response.status_code == 200
    assert enable_response.json()["consent_cloud_ai"] is True
    assert enable_response.json()["consent_data_processing"] is True

    update_response = client.patch(
        "/api/v1/users/me/consents",
        headers=headers,
        json={"consent_cloud_ai": False},
    )
    assert update_response.status_code == 200
    updated_data = update_response.json()

    assert updated_data["consent_cloud_ai"] is False
    assert updated_data["consent_data_processing"] is True
    assert updated_data["consent_local_cache"] is True


def test_delete_account_revokes_all_refresh_sessions(client):
    """
    КРИТИЧЕСКИЙ ТЕСТ БЕЗОПАСНОСТИ:
    При удалении аккаунта все refresh-сессии должны быть отозваны,
    чтобы пользователь не мог использовать API на других устройствах.
    """
    user_data = make_user_data()

    register_response = client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 201
    tokens = register_response.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    refresh_before = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_before.status_code == 200, "Refresh-токен должен работать до удаления"

    delete_response = client.request(
        "DELETE",
        "/api/v1/users/me",
        headers=headers,
        json={"pin": user_data["pin"]},
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Аккаунт удалён"

    refresh_after = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_after.status_code == 401, "Refresh-токен должен быть отозван после удаления аккаунта"


def test_delete_account_blocks_access_token(client):
    """
    Тест: после удаления аккаунта access-токен тоже перестаёт работать,
    потому что зависимость get_current_user проверяет флаги is_active/is_deleted.
    """
    user_data = make_user_data()

    register_response = client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 201
    tokens = register_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    delete_response = client.request(
        "DELETE",
        "/api/v1/users/me",
        headers=headers,
        json={"pin": user_data["pin"]},
    )
    assert delete_response.status_code == 200

    get_response = client.get("/api/v1/users/me", headers=headers)
    assert get_response.status_code == 401, "Удалённый пользователь не должен иметь доступ к API"