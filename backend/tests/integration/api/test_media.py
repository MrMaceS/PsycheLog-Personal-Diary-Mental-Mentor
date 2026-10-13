from tests.helpers import make_user_data


def test_request_upload_without_consent(client):
    """Тест: загрузка медиа блокируется, если отозвано согласие на обработку данных."""
    user_data = make_user_data()

    register_response = client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 201
    tokens = register_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    client.patch(
        "/api/v1/users/me/consents",
        headers=headers,
        json={
            "consent_data_processing": False,
            "consent_cloud_ai": True,
        },
    )

    upload_response = client.post(
        "/api/v1/media/request-upload",
        headers=headers,
        json={
            "file_name": "test.mp3",
            "content_type": "audio/mpeg",
            "media_type": "audio",
        },
    )

    assert upload_response.status_code == 403
    assert "обработку данных" in upload_response.json()["detail"]


def test_request_audio_upload_without_cloud_ai_consent(client):
    """Тест: загрузка аудио блокируется, если отозвано согласие на облачный AI."""
    user_data = make_user_data()

    register_response = client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 201
    tokens = register_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    client.patch(
        "/api/v1/users/me/consents",
        headers=headers,
        json={"consent_data_processing": True},
    )

    client.patch(
        "/api/v1/users/me/consents",
        headers=headers,
        json={"consent_cloud_ai": False},
    )

    upload_response = client.post(
        "/api/v1/media/request-upload",
        headers=headers,
        json={
            "file_name": "test.mp3",
            "content_type": "audio/mpeg",
            "media_type": "audio",
        },
    )

    assert upload_response.status_code == 403
    assert "облачный AI" in upload_response.json()["detail"]


def test_request_video_upload_with_cloud_ai_revoked(client):
    """Тест: загрузка видео разрешена, даже если отозвано согласие на облачный AI."""
    user_data = make_user_data()

    register_response = client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 201
    tokens = register_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    client.patch(
        "/api/v1/users/me/consents",
        headers=headers,
        json={
            "consent_data_processing": True,
            "consent_cloud_ai": False,
        },
    )

    upload_response = client.post(
        "/api/v1/media/request-upload",
        headers=headers,
        json={
            "file_name": "test.mp4",
            "content_type": "video/mp4",
            "media_type": "video",
        },
    )

    assert upload_response.status_code == 200
    assert "presigned_url" in upload_response.json()


def test_list_user_media(client):
    """Тест: пользователь может получить список своих медиафайлов."""
    user_data = make_user_data()

    register_response = client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 201
    tokens = register_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    client.patch(
        "/api/v1/users/me/consents",
        headers=headers,
        json={
            "consent_data_processing": True,
            "consent_cloud_ai": True,
        },
    )

    upload_response = client.post(
        "/api/v1/media/request-upload",
        headers=headers,
        json={
            "file_name": "test1.mp3",
            "content_type": "audio/mpeg",
            "media_type": "audio",
        },
    )
    assert upload_response.status_code == 200

    list_response = client.get("/api/v1/media/", headers=headers)
    assert list_response.status_code == 200
    media_list = list_response.json()
    assert len(media_list) == 1
    assert media_list[0]["media_type"] == "audio"
    assert media_list[0]["status"] == "pending"