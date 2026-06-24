# tests/test_events.py

import pytest
from events.models import Seat
from events.lock_service import acquire_seat_lock, release_seat_lock, is_seat_locked


@pytest.mark.django_db
def test_event_list_public(client, event):
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_event_detail_public(client, event):
    response = client.get(f"/events/{event.id}/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_acquire_seat_lock(seat, user):
    acquired = acquire_seat_lock(seat.id, user.id)
    assert acquired is True
    assert is_seat_locked(seat.id) is True
    release_seat_lock(seat.id, user.id)


@pytest.mark.django_db
def test_seat_lock_prevents_double_lock(seat, user, organizer):
    acquired_first = acquire_seat_lock(seat.id, user.id)
    acquired_second = acquire_seat_lock(seat.id, organizer.id)
    assert acquired_first is True
    assert acquired_second is False
    release_seat_lock(seat.id, user.id)


@pytest.mark.django_db
def test_release_seat_lock_wrong_user(seat, user, organizer):
    acquire_seat_lock(seat.id, user.id)
    released = release_seat_lock(seat.id, organizer.id)
    assert released is False
    release_seat_lock(seat.id, user.id)


@pytest.mark.django_db
def test_confirm_booking_requires_login(client, seat):
    response = client.get(f"/bookings/confirm/{seat.id}/")
    assert response.status_code == 302
    assert "/login/" in response.url