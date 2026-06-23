import logging
from django.utils import timezone
from django.conf import settings
from redis import Redis

logger = logging.getLogger(__name__)

LOCK_TTL_SECONDS = 600  # 10 minutes
LOCK_PREFIX = "seat_lock"

redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True
)


def _lock_key(seat_id: int) -> str:
    return f"{LOCK_PREFIX}:{seat_id}"


def acquire_seat_lock(seat_id: int, user_id: int) -> bool:
    """
    Try to acquire a Redis lock for a seat.
    Returns True if lock was acquired, False if seat is already locked.
    Uses SET NX PX — atomic operation, safe under concurrent requests.
    """
    key = _lock_key(seat_id)
    value = str(user_id)

    acquired = redis_client.set(
        key,
        value,
        nx=True,        # Only set if key does NOT exist
        ex=LOCK_TTL_SECONDS
    )

    if acquired:
        logger.info(f"Seat lock acquired | seat_id={seat_id} | user_id={user_id}")
    else:
        logger.info(f"Seat lock failed (already locked) | seat_id={seat_id} | user_id={user_id}")

    return bool(acquired)


def release_seat_lock(seat_id: int, user_id: int) -> bool:
    """
    Release the lock only if the requesting user owns it.
    Prevents a user from releasing another user's lock.
    """
    key = _lock_key(seat_id)
    current_owner = redis_client.get(key)

    if current_owner != str(user_id):
        logger.warning(
            f"Seat lock release denied | seat_id={seat_id} | "
            f"requester={user_id} | owner={current_owner}"
        )
        return False

    redis_client.delete(key)
    logger.info(f"Seat lock released | seat_id={seat_id} | user_id={user_id}")
    return True


def is_seat_locked(seat_id: int) -> bool:
    """Check if a seat lock exists in Redis."""
    return redis_client.exists(_lock_key(seat_id)) == 1


def get_lock_owner(seat_id: int):
    """Return the user_id who holds the lock, or None."""
    return redis_client.get(_lock_key(seat_id))


def extend_seat_lock(seat_id: int, user_id: int) -> bool:
    """
    Extend the lock TTL if the user still owns it.
    Useful if the frontend needs to keep the seat held longer.
    """
    key = _lock_key(seat_id)
    current_owner = redis_client.get(key)

    if current_owner != str(user_id):
        return False

    redis_client.expire(key, LOCK_TTL_SECONDS)
    logger.info(f"Seat lock extended | seat_id={seat_id} | user_id={user_id}")
    return True