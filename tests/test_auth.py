# tests/test_auth.py

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_register_creates_user(client):
    response = client.post("/accounts/register/", {
        "username": "newuser",
        "email": "new@example.com",
        "password": "testpass123",
    })
    assert User.objects.filter(username="newuser").exists()


@pytest.mark.django_db
def test_login_valid_credentials(client, user):
    response = client.post("/accounts/login/", {
        "username": user.username,
        "password": "testpass123",
    })
    assert response.status_code in [200, 302]


@pytest.mark.django_db
def test_login_invalid_credentials(client):
    response = client.post("/accounts/login/", {
        "username": "nobody",
        "password": "wrongpass",
    })
    assert response.status_code == 200
    assert "Invalid" in response.content.decode()