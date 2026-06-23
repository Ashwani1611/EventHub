import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import Seat
from .lock_service import is_seat_locked

logger = logging.getLogger(__name__)


@shared_task
def release_expired_seat_locks():
    """
    Periodic task — runs every minute.
    Finds seats that are LOCKED in the DB but whose Redis lock has expired.
    Resets them back to AVAILABLE.
    """
    lock_ttl_minutes = 10
    cutoff_time = timezone.now() - timedelta(minutes=lock_ttl_minutes)

    # Seats marked locked in DB but locked_at is older than TTL
    expired_in_db = Seat.objects.filter(
        status=Seat.Status.LOCKED,
        locked_at__lte=cutoff_time
    )

    released_count = 0

    for seat in expired_in_db:
        # Double check — if Redis lock is also gone, it's truly expired
        if not is_seat_locked(seat.id):
            seat.status = Seat.Status.AVAILABLE
            seat.locked_by = None
            seat.locked_at = None
            seat.save(update_fields=["status", "locked_by", "locked_at"])

            released_count += 1
            logger.info(f"Expired seat lock released | seat_id={seat.id}")

    if released_count:
        logger.info(f"Seat lock cleanup complete | released={released_count}")

    return released_count