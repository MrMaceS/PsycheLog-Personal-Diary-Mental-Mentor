from tests.helpers import make_user_data


def test_notification_created_on_message(client):
    """Тест: при отправке сообщения создаётся уведомление для участников."""
    user1_data = make_user_data()
    user2_data = make_user_data()

    register1 = client.post("/api/v1/auth/register", json=user1_data)
    tokens1 = register1.json()
    headers1 = {"Authorization": f"Bearer {tokens1['access_token']}"}

    register2 = client.post("/api/v1/auth/register", json=user2_data)
    tokens2 = register2.json()
    headers2 = {"Authorization": f"Bearer {tokens2['access_token']}"}

    create_chat = client.post(
        "/api/v1/chats/",
        headers=headers1,
        json={
            "name": "Test Chat",
            "is_group": False,
            "member_usernames": [user2_data["username"]],
        },
    )
    chat_id = create_chat.json()["id"]

    client.post(
        f"/api/v1/chats/{chat_id}/messages",
        headers=headers1,
        json={"content": "Привет!"},
    )

    notifications_response = client.get("/api/v1/notifications/", headers=headers2)
    assert notifications_response.status_code == 200
    data = notifications_response.json()

    assert data["unread_count"] == 1
    assert len(data["notifications"]) == 1
    assert data["notifications"][0]["type"] == "chat_message"
    assert "Привет!" in data["notifications"][0]["message"]


def test_mark_notification_read(client):
    """Тест: пометка уведомления как прочитанного."""
    user_data = make_user_data()
    register = client.post("/api/v1/auth/register", json=user_data)
    tokens = register.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    notifications = client.get("/api/v1/notifications/", headers=headers)
    assert notifications.status_code == 200