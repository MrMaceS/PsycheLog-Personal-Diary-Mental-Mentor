import uuid


def make_user_data():
    suffix = uuid.uuid4().hex[:10]

    return {
        "email": f"test_{suffix}@example.com",
        "username": f"user_{suffix}",
        "display_name": "Test User",
        "pin": "1234",
    }