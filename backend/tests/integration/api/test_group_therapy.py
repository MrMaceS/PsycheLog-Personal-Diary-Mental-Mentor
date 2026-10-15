from tests.helpers import make_user_data
from datetime import datetime, timezone, timedelta


def test_create_group_session(client):
    """Тест: создание групповой сессии."""
    user_data = make_user_data()
    register = client.post("/api/v1/auth/register", json=user_data)
    tokens = register.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    scheduled_time = datetime.now(timezone.utc) + timedelta(days=1, hours=10)

    create_response = client.post(
        "/api/v1/group-therapy/sessions",
        headers=headers,
        json={
            "title": "Групповая терапия: Управление стрессом",
            "description": "Обсудим техники работы со стрессом",
            "scheduled_at": scheduled_time.isoformat(),
            "duration_minutes": 60,
            "max_participants": 8,
        },
    )

    assert create_response.status_code == 201
    session_data = create_response.json()
    assert session_data["title"] == "Групповая терапия: Управление стрессом"
    assert session_data["status"] == "scheduled"
    assert session_data["max_participants"] == 8
    assert session_data["enrolled_count"] == 0


def test_cannot_create_session_in_past(client):
    """Тест: нельзя создать сессию в прошлом."""
    user_data = make_user_data()
    register = client.post("/api/v1/auth/register", json=user_data)
    tokens = register.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    past_time = datetime.now(timezone.utc) - timedelta(days=1)

    create_response = client.post(
        "/api/v1/group-therapy/sessions",
        headers=headers,
        json={
            "title": "Тест",
            "scheduled_at": past_time.isoformat(),
        },
    )

    assert create_response.status_code == 400
    assert "должно быть в будущем" in create_response.json()["detail"]


def test_enroll_in_session(client):
    """Тест: запись на групповую сессию."""
    user_data = make_user_data()
    register = client.post("/api/v1/auth/register", json=user_data)
    tokens = register.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    scheduled_time = datetime.now(timezone.utc) + timedelta(days=1)
    create_response = client.post(
        "/api/v1/group-therapy/sessions",
        headers=headers,
        json={
            "title": "Тестовая сессия",
            "scheduled_at": scheduled_time.isoformat(),
            "max_participants": 5,
        },
    )
    session_id = create_response.json()["id"]

    enroll_response = client.post(
        f"/api/v1/group-therapy/sessions/{session_id}/enroll",
        headers=headers,
    )

    assert enroll_response.status_code == 201
    enrollment_data = enroll_response.json()
    assert enrollment_data["session_id"] == session_id


def test_cannot_enroll_twice(client):
    """Тест: нельзя записаться на сессию дважды."""
    user_data = make_user_data()
    register = client.post("/api/v1/auth/register", json=user_data)
    tokens = register.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    scheduled_time = datetime.now(timezone.utc) + timedelta(days=1)
    create_response = client.post(
        "/api/v1/group-therapy/sessions",
        headers=headers,
        json={
            "title": "Тест",
            "scheduled_at": scheduled_time.isoformat(),
        },
    )
    session_id = create_response.json()["id"]

    client.post(
        f"/api/v1/group-therapy/sessions/{session_id}/enroll",
        headers=headers,
    )

    enroll_response = client.post(
        f"/api/v1/group-therapy/sessions/{session_id}/enroll",
        headers=headers,
    )

    assert enroll_response.status_code == 400
    assert "уже записаны" in enroll_response.json()["detail"]


def test_enrollment_limit(client):
    """Тест: проверка лимита участников."""
    user1_data = make_user_data()
    user2_data = make_user_data()

    register1 = client.post("/api/v1/auth/register", json=user1_data)
    tokens1 = register1.json()
    headers1 = {"Authorization": f"Bearer {tokens1['access_token']}"}

    register2 = client.post("/api/v1/auth/register", json=user2_data)
    tokens2 = register2.json()
    headers2 = {"Authorization": f"Bearer {tokens2['access_token']}"}

    scheduled_time = datetime.now(timezone.utc) + timedelta(days=1)
    create_response = client.post(
        "/api/v1/group-therapy/sessions",
        headers=headers1,
        json={
            "title": "Тест",
            "scheduled_at": scheduled_time.isoformat(),
            "max_participants": 2,
        },
    )
    session_id = create_response.json()["id"]

    client.post(f"/api/v1/group-therapy/sessions/{session_id}/enroll", headers=headers1)
    client.post(f"/api/v1/group-therapy/sessions/{session_id}/enroll", headers=headers2)

    user3_data = make_user_data()
    register3 = client.post("/api/v1/auth/register", json=user3_data)
    tokens3 = register3.json()
    headers3 = {"Authorization": f"Bearer {tokens3['access_token']}"}

    enroll_response = client.post(
        f"/api/v1/group-therapy/sessions/{session_id}/enroll",
        headers=headers3,
    )

    assert enroll_response.status_code == 400
    assert "лимит участников" in enroll_response.json()["detail"]


def test_cancel_enrollment(client):
    """Тест: отмена записи на сессию."""
    user_data = make_user_data()
    register = client.post("/api/v1/auth/register", json=user_data)
    tokens = register.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    scheduled_time = datetime.now(timezone.utc) + timedelta(days=1)
    create_response = client.post(
        "/api/v1/group-therapy/sessions",
        headers=headers,
        json={
            "title": "Тест",
            "scheduled_at": scheduled_time.isoformat(),
        },
    )
    session_id = create_response.json()["id"]

    client.post(f"/api/v1/group-therapy/sessions/{session_id}/enroll", headers=headers)

    cancel_response = client.delete(
        f"/api/v1/group-therapy/sessions/{session_id}/enroll",
        headers=headers,
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["message"] == "Запись отменена"


def test_list_available_sessions(client):
    """Тест: получение списка доступных сессий."""
    user_data = make_user_data()
    register = client.post("/api/v1/auth/register", json=user_data)
    tokens = register.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    for i in range(3):
        scheduled_time = datetime.now(timezone.utc) + timedelta(days=i + 1)
        client.post(
            "/api/v1/group-therapy/sessions",
            headers=headers,
            json={
                "title": f"Сессия {i + 1}",
                "scheduled_at": scheduled_time.isoformat(),
            },
        )

    list_response = client.get("/api/v1/group-therapy/sessions", headers=headers)

    assert list_response.status_code == 200
    sessions = list_response.json()
    assert len(sessions) >= 3


def test_list_my_enrollments(client):
    """Тест: получение списка моих записей."""
    user_data = make_user_data()
    register = client.post("/api/v1/auth/register", json=user_data)
    tokens = register.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    scheduled_time = datetime.now(timezone.utc) + timedelta(days=1)
    session1 = client.post(
        "/api/v1/group-therapy/sessions",
        headers=headers,
        json={
            "title": "Сессия 1",
            "scheduled_at": scheduled_time.isoformat(),
        },
    ).json()["id"]

    session2 = client.post(
        "/api/v1/group-therapy/sessions",
        headers=headers,
        json={
            "title": "Сессия 2",
            "scheduled_at": (scheduled_time + timedelta(days=1)).isoformat(),
        },
    ).json()["id"]

    client.post(f"/api/v1/group-therapy/sessions/{session1}/enroll", headers=headers)
    client.post(f"/api/v1/group-therapy/sessions/{session2}/enroll", headers=headers)

    enrollments_response = client.get(
        "/api/v1/group-therapy/sessions/my-enrollments",
        headers=headers,
    )

    assert enrollments_response.status_code == 200
    enrollments = enrollments_response.json()
    assert len(enrollments) >= 2