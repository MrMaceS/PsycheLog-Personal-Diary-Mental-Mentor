from tests.helpers import make_user_data


def test_create_group_chat(client):
    """Тест создания группового чата."""
    user1_data = make_user_data()
    user2_data = make_user_data()

    register1 = client.post("/api/v1/auth/register", json=user1_data)
    assert register1.status_code == 201
    tokens1 = register1.json()
    headers1 = {"Authorization": f"Bearer {tokens1['access_token']}"}

    register2 = client.post("/api/v1/auth/register", json=user2_data)
    assert register2.status_code == 201

    create_response = client.post(
        "/api/v1/chats/",
        headers=headers1,
        json={
            "name": "Test Group Chat",
            "is_group": True,
            "member_usernames": [user2_data["username"]],
        },
    )

    assert create_response.status_code == 201
    chat_data = create_response.json()
    assert chat_data["name"] == "Test Group Chat"
    assert chat_data["is_group"] is True
    assert len(chat_data["members"]) == 2


def test_send_message_in_chat(client):
    """Тест отправки сообщения в чат."""
    user_data = make_user_data()
    register = client.post("/api/v1/auth/register", json=user_data)
    assert register.status_code == 201
    tokens = register.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    create_chat = client.post(
        "/api/v1/chats/",
        headers=headers,
        json={
            "name": "Personal Chat",
            "is_group": False,
            "member_usernames": [],
        },
    )
    assert create_chat.status_code == 201
    chat_id = create_chat.json()["id"]

    send_response = client.post(
        f"/api/v1/chats/{chat_id}/messages",
        headers=headers,
        json={
            "content": "Привет, это тестовое сообщение!",
        },
    )

    assert send_response.status_code == 201
    message_data = send_response.json()
    assert message_data["content"] == "Привет, это тестовое сообщение!"
    assert message_data["is_deleted"] is False


def test_delete_own_message(client):
    """Тест удаления своего сообщения."""
    user_data = make_user_data()
    register = client.post("/api/v1/auth/register", json=user_data)
    assert register.status_code == 201
    tokens = register.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    create_chat = client.post(
        "/api/v1/chats/",
        headers=headers,
        json={"name": "Test", "is_group": False, "member_usernames": []},
    )
    chat_id = create_chat.json()["id"]

    send_response = client.post(
        f"/api/v1/chats/{chat_id}/messages",
        headers=headers,
        json={"content": "Это сообщение будет удалено"},
    )
    message_id = send_response.json()["id"]

    delete_response = client.delete(
        f"/api/v1/chats/messages/{message_id}",
        headers=headers,
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Сообщение удалено"


def test_cannot_send_message_if_not_member(client):
    """Тест: нельзя отправить сообщение, если не являешься участником чата."""
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
        json={"name": "Private", "is_group": False, "member_usernames": []},
    )
    chat_id = create_chat.json()["id"]

    send_response = client.post(
        f"/api/v1/chats/{chat_id}/messages",
        headers=headers2,
        json={"content": "Я не участник!"},
    )

    assert send_response.status_code == 403
    assert "не являетесь участником" in send_response.json()["detail"]