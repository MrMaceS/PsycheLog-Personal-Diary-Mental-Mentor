from tests.helpers import make_user_data


def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json=make_user_data(),
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


def test_login_user(client):
    user_data = make_user_data()

    register_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201, register_response.text

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "pin": user_data["pin"],
        },
    )

    assert login_response.status_code == 200, login_response.text

    data = login_response.json()

    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


def test_login_with_wrong_pin(client):
    user_data = make_user_data()

    register_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201, register_response.text

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "pin": "9999",
        },
    )

    assert login_response.status_code in (401, 403), login_response.text


def test_refresh_token_rotation(client):
    user_data = make_user_data()

    register_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201, register_response.text

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "pin": user_data["pin"],
        },
    )

    assert login_response.status_code == 200, login_response.text

    old_refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert refresh_response.status_code == 200, refresh_response.text

    refresh_data = refresh_response.json()

    assert refresh_data["access_token"]
    assert refresh_data["refresh_token"]
    assert refresh_data["refresh_token"] != old_refresh_token
    assert refresh_data["token_type"] == "bearer"


def test_reused_refresh_token_returns_401(client):
    user_data = make_user_data()

    register_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201, register_response.text

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "pin": user_data["pin"],
        },
    )

    assert login_response.status_code == 200, login_response.text

    refresh_token = login_response.json()["refresh_token"]

    first_refresh = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert first_refresh.status_code == 200, first_refresh.text

    second_refresh = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert second_refresh.status_code == 401, second_refresh.text


def test_logout_revokes_refresh_token(client):
    user_data = make_user_data()

    register_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201, register_response.text

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "pin": user_data["pin"],
        },
    )

    assert login_response.status_code == 200, login_response.text

    refresh_token = login_response.json()["refresh_token"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert logout_response.status_code in (200, 204), (
        logout_response.text
    )

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert refresh_response.status_code == 401, refresh_response.text


def test_request_otp_for_existing_user(client):
    user_data = make_user_data()

    register_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201, register_response.text

    otp_response = client.post(
        "/api/v1/auth/request-otp",
        json={
            "email": user_data["email"],
        },
    )

    assert otp_response.status_code == 200, otp_response.text
    assert "message" in otp_response.json()


def test_request_otp_for_unknown_user(client):
    response = client.post(
        "/api/v1/auth/request-otp",
        json={
            "email": "unknown@example.com",
        },
    )

    assert response.status_code in (400, 404), response.text


def test_verify_otp(client):
    user_data = make_user_data()

    register_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201, register_response.text

    otp_response = client.post(
        "/api/v1/auth/request-otp",
        json={
            "email": user_data["email"],
        },
    )

    assert otp_response.status_code == 200, otp_response.text

    otp_data = otp_response.json()

    assert "otp" in otp_data

    otp = otp_data["otp"]

    assert len(otp) == 6
    assert otp.isdigit()

    verify_response = client.post(
        "/api/v1/auth/verify-otp",
        json={
            "email": user_data["email"],
            "otp": otp,
        },
    )

    assert verify_response.status_code == 200, verify_response.text


def test_verify_otp_with_wrong_code(client):
    user_data = make_user_data()

    register_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )
    assert register_response.status_code == 201

    otp_response = client.post(
        "/api/v1/auth/request-otp",
        json={"email": user_data["email"]},
    )
    assert otp_response.status_code == 200

    response = client.post(
        "/api/v1/auth/verify-otp",
        json={
            "email": user_data["email"],
            "otp": "000000",
        },
    )

    assert response.status_code == 400


def test_account_locks_after_failed_pins(client):
    user_data = make_user_data()

    register_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201

    for _ in range(3):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": user_data["email"],
                "pin": "9999",
            },
        )

        assert response.status_code == 401

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_data["email"],
            "pin": user_data["pin"],
        },
    )

    assert response.status_code == 423


def test_new_otp_invalidates_previous_otp(client):
    user_data = make_user_data()

    register_response = client.post(
        "/api/v1/auth/register",
        json=user_data,
    )

    assert register_response.status_code == 201

    first_response = client.post(
        "/api/v1/auth/request-otp",
        json={"email": user_data["email"]},
    )

    second_response = client.post(
        "/api/v1/auth/request-otp",
        json={"email": user_data["email"]},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_otp = first_response.json()["otp"]
    second_otp = second_response.json()["otp"]

    assert first_otp != second_otp

    verify_old_response = client.post(
        "/api/v1/auth/verify-otp",
        json={
            "email": user_data["email"],
            "otp": first_otp,
        },
    )

    assert verify_old_response.status_code == 400

    verify_new_response = client.post(
        "/api/v1/auth/verify-otp",
        json={
            "email": user_data["email"],
            "otp": second_otp,
        },
    )

    assert verify_new_response.status_code == 200


def test_get_current_user_with_invalid_token(client):
    response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401