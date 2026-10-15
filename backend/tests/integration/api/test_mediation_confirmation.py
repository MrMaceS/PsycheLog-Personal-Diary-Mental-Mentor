from tests.helpers import make_user_data


def test_confirm_resolution_both_agree(client):
    """Тест: оба участника подтверждают AI-резюме → статус CONFIRMED."""
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
        json={"recipient_id": user2_id, "topic": "Тест подтверждения"},
    )
    session_id = request_response.json()["id"]

    client.patch(
        f"/api/v1/mediation/{session_id}/respond",
        headers=headers2,
        json={"is_accepted": True},
    )

    client.post(
        f"/api/v1/mediation/{session_id}/submit",
        headers=headers1,
        json={"content": "Позиция инициатора по тестовому вопросу"},
    )

    client.post(
        f"/api/v1/mediation/{session_id}/submit",
        headers=headers2,
        json={"content": "Позиция получателя по тестовому вопросу"},
    )

    analyze_response = client.post(
        f"/api/v1/mediation/{session_id}/analyze",
        headers=headers1,
    )
    assert analyze_response.status_code == 200
    assert analyze_response.json()["status"] == "resolution_proposed"

    confirm1_response = client.post(
        f"/api/v1/mediation/{session_id}/confirm-resolution",
        headers=headers1,
        json={"is_confirmed": True},
    )
    assert confirm1_response.status_code == 200

    confirm2_response = client.post(
        f"/api/v1/mediation/{session_id}/confirm-resolution",
        headers=headers2,
        json={"is_confirmed": True},
    )
    assert confirm2_response.status_code == 200
    assert confirm2_response.json()["status"] == "confirmed"


def test_dispute_resolution(client):
    """Тест: один участник отклоняет AI-резюме → статус DISPUTED."""
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
        json={"recipient_id": user2_id, "topic": "Тест отклонения"},
    )
    session_id = request_response.json()["id"]

    client.patch(
        f"/api/v1/mediation/{session_id}/respond",
        headers=headers2,
        json={"is_accepted": True},
    )

    client.post(
        f"/api/v1/mediation/{session_id}/submit",
        headers=headers1,
        json={"content": "Позиция инициатора"},
    )

    client.post(
        f"/api/v1/mediation/{session_id}/submit",
        headers=headers2,
        json={"content": "Позиция получателя"},
    )

    client.post(
        f"/api/v1/mediation/{session_id}/analyze",
        headers=headers1,
    )

    confirm_response = client.post(
        f"/api/v1/mediation/{session_id}/confirm-resolution",
        headers=headers1,
        json={"is_confirmed": False},
    )
    assert confirm_response.status_code == 200
    assert confirm_response.json()["status"] == "disputed"