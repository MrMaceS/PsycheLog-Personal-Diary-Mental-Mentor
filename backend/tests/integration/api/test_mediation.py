from tests.helpers import make_user_data


def test_request_mediation(client):
    """Тест: создание запроса на медиацию."""
    user1_data = make_user_data()
    user2_data = make_user_data()

    register1 = client.post("/api/v1/auth/register", json=user1_data)
    assert register1.status_code == 201
    tokens1 = register1.json()
    headers1 = {"Authorization": f"Bearer {tokens1['access_token']}"}

    register2 = client.post("/api/v1/auth/register", json=user2_data)
    assert register2.status_code == 201
    user2_id = register2.json().get("user_id") or 2

    user2_response = client.get("/api/v1/users/me",
                                headers={"Authorization": f"Bearer {register2.json()['access_token']}"})
    user2_id = user2_response.json()["id"]

    request_response = client.post(
        "/api/v1/mediation/request",
        headers=headers1,
        json={
            "recipient_id": user2_id,
            "topic": "Конфликт по рабочим вопросам",
        },
    )

    assert request_response.status_code == 201
    session_data = request_response.json()
    assert session_data["initiator_id"] != session_data["recipient_id"]
    assert session_data["status"] == "pending"
    assert session_data["topic"] == "Конфликт по рабочим вопросам"

    headers2 = {"Authorization": f"Bearer {register2.json()['access_token']}"}
    notifications = client.get("/api/v1/notifications/", headers=headers2)
    assert notifications.status_code == 200
    notif_data = notifications.json()
    assert notif_data["unread_count"] == 1
    assert notif_data["notifications"][0]["type"] == "mediation_request"


def test_cannot_request_mediation_with_self(client):
    """Тест: нельзя запросить медиацию с самим собой."""
    user_data = make_user_data()
    register = client.post("/api/v1/auth/register", json=user_data)
    tokens = register.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    me_response = client.get("/api/v1/users/me", headers=headers)
    my_id = me_response.json()["id"]

    request_response = client.post(
        "/api/v1/mediation/request",
        headers=headers,
        json={
            "recipient_id": my_id,
            "topic": "Тест",
        },
    )

    assert request_response.status_code == 400
    assert "самим собой" in request_response.json()["detail"]


def test_accept_mediation(client):
    """Тест: принятие запроса на медиацию."""
    user1_data = make_user_data()
    user2_data = make_user_data()

    register1 = client.post("/api/v1/auth/register", json=user1_data)
    tokens1 = register1.json()
    headers1 = {"Authorization": f"Bearer {tokens1['access_token']}"}

    register2 = client.post("/api/v1/auth/register", json=user2_data)
    tokens2 = register2.json()
    headers2 = {"Authorization": f"Bearer {tokens2['access_token']}"}

    user2_response = client.get("/api/v1/users/me", headers=headers2)
    user2_id = user2_response.json()["id"]

    request_response = client.post(
        "/api/v1/mediation/request",
        headers=headers1,
        json={"recipient_id": user2_id, "topic": "Тест"},
    )
    session_id = request_response.json()["id"]

    respond_response = client.patch(
        f"/api/v1/mediation/{session_id}/respond",
        headers=headers2,
        json={
            "is_accepted": True,
            "response_message": "Согласен обсудить",
        },
    )

    assert respond_response.status_code == 200
    session_data = respond_response.json()
    assert session_data["status"] == "active"

    notifications = client.get("/api/v1/notifications/", headers=headers1)
    assert notifications.status_code == 200
    notif_data = notifications.json()
    assert notif_data["unread_count"] == 1
    assert "согласился" in notif_data["notifications"][0]["message"]


def test_decline_mediation(client):
    """Тест: отклонение запроса на медиацию."""
    user1_data = make_user_data()
    user2_data = make_user_data()

    register1 = client.post("/api/v1/auth/register", json=user1_data)
    tokens1 = register1.json()
    headers1 = {"Authorization": f"Bearer {tokens1['access_token']}"}

    register2 = client.post("/api/v1/auth/register", json=user2_data)
    tokens2 = register2.json()
    headers2 = {"Authorization": f"Bearer {tokens2['access_token']}"}

    user2_response = client.get("/api/v1/users/me", headers=headers2)
    user2_id = user2_response.json()["id"]

    request_response = client.post(
        "/api/v1/mediation/request",
        headers=headers1,
        json={"recipient_id": user2_id, "topic": "Тест"},
    )
    session_id = request_response.json()["id"]

    respond_response = client.patch(
        f"/api/v1/mediation/{session_id}/respond",
        headers=headers2,
        json={
            "is_accepted": False,
            "response_message": "Не хочу участвовать",
        },
    )

    assert respond_response.status_code == 200
    session_data = respond_response.json()
    assert session_data["status"] == "declined"


def test_submit_position_in_active_mediation(client):
    """Тест: отправка позиции в активной медиации."""
    user1_data = make_user_data()
    user2_data = make_user_data()

    register1 = client.post("/api/v1/auth/register", json=user1_data)
    tokens1 = register1.json()
    headers1 = {"Authorization": f"Bearer {tokens1['access_token']}"}

    register2 = client.post("/api/v1/auth/register", json=user2_data)
    tokens2 = register2.json()
    headers2 = {"Authorization": f"Bearer {tokens2['access_token']}"}

    user2_response = client.get("/api/v1/users/me", headers=headers2)
    user2_id = user2_response.json()["id"]

    request_response = client.post(
        "/api/v1/mediation/request",
        headers=headers1,
        json={"recipient_id": user2_id, "topic": "Тест"},
    )
    session_id = request_response.json()["id"]

    client.patch(
        f"/api/v1/mediation/{session_id}/respond",
        headers=headers2,
        json={"is_accepted": True},
    )

    submit_response = client.post(
        f"/api/v1/mediation/{session_id}/submit",
        headers=headers1,
        json={
            "content": "Считаю, что проблема возникла из-за недопонимания в коммуникации.",
            "is_final": False,
        },
    )

    assert submit_response.status_code == 201
    submission_data = submit_response.json()
    assert submission_data["session_id"] == session_id
    assert "недопонимания" in submission_data["content"]
    assert submission_data["is_final"] is False


def test_cannot_submit_in_pending_mediation(client):
    """Тест: нельзя отправить позицию в неактивной медиации."""
    user1_data = make_user_data()
    user2_data = make_user_data()

    register1 = client.post("/api/v1/auth/register", json=user1_data)
    tokens1 = register1.json()
    headers1 = {"Authorization": f"Bearer {tokens1['access_token']}"}

    register2 = client.post("/api/v1/auth/register", json=user2_data)
    tokens2 = register2.json()
    headers2 = {"Authorization": f"Bearer {tokens2['access_token']}"}

    user2_response = client.get("/api/v1/users/me", headers=headers2)
    user2_id = user2_response.json()["id"]

    request_response = client.post(
        "/api/v1/mediation/request",
        headers=headers1,
        json={"recipient_id": user2_id, "topic": "Тест"},
    )
    session_id = request_response.json()["id"]

    submit_response = client.post(
        f"/api/v1/mediation/{session_id}/submit",
        headers=headers1,
        json={"content": "Это моя позиция по данному вопросу"},
    )

    assert submit_response.status_code == 400
    assert "не активна" in submit_response.json()["detail"]


def test_list_my_mediations(client):
    """Тест: получение списка моих медиаций."""
    user1_data = make_user_data()
    user2_data = make_user_data()

    register1 = client.post("/api/v1/auth/register", json=user1_data)
    tokens1 = register1.json()
    headers1 = {"Authorization": f"Bearer {tokens1['access_token']}"}

    register2 = client.post("/api/v1/auth/register", json=user2_data)
    tokens2 = register2.json()
    headers2 = {"Authorization": f"Bearer {tokens2['access_token']}"}

    user2_response = client.get("/api/v1/users/me", headers=headers2)
    user2_id = user2_response.json()["id"]

    client.post(
        "/api/v1/mediation/request",
        headers=headers1,
        json={"recipient_id": user2_id, "topic": "Тест 1"},
    )

    list_response = client.get("/api/v1/mediation/", headers=headers1)
    assert list_response.status_code == 200
    mediations = list_response.json()
    assert len(mediations) >= 1
    assert any(m["topic"] == "Тест 1" for m in mediations)


def test_cannot_access_others_mediation(client):
    """Тест: нельзя получить доступ к чужой медиации."""
    user1_data = make_user_data()
    user2_data = make_user_data()
    user3_data = make_user_data()

    register1 = client.post("/api/v1/auth/register", json=user1_data)
    tokens1 = register1.json()
    headers1 = {"Authorization": f"Bearer {tokens1['access_token']}"}

    register2 = client.post("/api/v1/auth/register", json=user2_data)
    tokens2 = register2.json()
    headers2 = {"Authorization": f"Bearer {tokens2['access_token']}"}

    register3 = client.post("/api/v1/auth/register", json=user3_data)
    tokens3 = register3.json()
    headers3 = {"Authorization": f"Bearer {tokens3['access_token']}"}

    user2_response = client.get("/api/v1/users/me", headers=headers2)
    user2_id = user2_response.json()["id"]

    request_response = client.post(
        "/api/v1/mediation/request",
        headers=headers1,
        json={"recipient_id": user2_id, "topic": "Тест"},
    )
    session_id = request_response.json()["id"]

    get_response = client.get(
        f"/api/v1/mediation/{session_id}",
        headers=headers3,
    )

    assert get_response.status_code == 403
    assert "не являетесь участником" in get_response.json()["detail"]