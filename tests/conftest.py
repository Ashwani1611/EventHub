# tests/conftest.py

import pytest
from faker import Faker
from django.contrib.auth import get_user_model
from events.models import Event, Seat
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()
fake = Faker()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username=fake.user_name(),
        email=fake.email(),
        password="testpass123",
        role="attendee"
    )


@pytest.fixture
def organizer(db):
    return User.objects.create_user(
        username=fake.user_name(),
        email=fake.email(),
        password="testpass123",
        role="organizer"
    )


@pytest.fixture
def event(db, organizer):
    return Event.objects.create(
        organizer=organizer,
        title=fake.sentence(nb_words=4),
        description=fake.paragraph(),
        venue=fake.city(),
        date=timezone.now() + timedelta(days=30),
        total_capacity=100,
        price=499.00,
        status=Event.Status.PUBLISHED
    )


@pytest.fixture
def seat(db, event):
    return Seat.objects.create(
        event=event,
        row="A",
        number=1,
        status=Seat.Status.AVAILABLE
    )


@pytest.fixture
def client(db):
    from django.test import Client
    return Client()


@pytest.fixture
def auth_client(db, user):
    from django.test import Client
    c = Client()
    c.force_login(user)
    return c, user