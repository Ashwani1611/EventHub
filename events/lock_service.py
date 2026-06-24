import logging
from django.conf import settings
from redis import Redis
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

LOCK_TTL_SECONDS = 600
LOCK_PREFIX = "seat_lock"

redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True
)


def _lock_key(seat_id: int) -> str:
    return f"{LOCK_PREFIX}:{seat_id}"


def _broadcast_seat_update(event_id: int, seat_id: int, status_value: str):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"event_{event_id}_seats",
        {
            "type": "seat_update",
            "seat_id": seat_id,
            "status": status_value,
        }
    )


def _broadcast_current_seat_status(seat_id: int):
    """
    Reads the seat's actual current DB status and broadcasts it.
    Used after lock/release so the WebSocket always reports truth,
    not an assumption about what status "should" be at that point.
    """
    try:
        from events.models import Seat
        seat = Seat.objects.only("event_id", "status").get(id=seat_id)
        _broadcast_seat_update(seat.event_id, seat_id, seat.status)
    except Exception:
        logger.exception(f"Failed to broadcast seat update | seat_id={seat_id}")


def acquire_seat_lock(seat_id: int, user_id: int) -> bool:
    key = _lock_key(seat_id)
    value = str(user_id)

    acquired = redis_client.set(key, value, nx=True, ex=LOCK_TTL_SECONDS)

    if acquired:
        logger.info(f"Seat lock acquired | seat_id={seat_id} | user_id={user_id}")
    else:
        logger.info(f"Seat lock failed (already locked) | seat_id={seat_id} | user_id={user_id}")

    return bool(acquired)


def release_seat_lock(seat_id: int, user_id: int) -> bool:
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
    return redis_client.exists(_lock_key(seat_id)) == 1


def get_lock_owner(seat_id: int):
    return redis_client.get(_lock_key(seat_id))


def extend_seat_lock(seat_id: int, user_id: int) -> bool:
    key = _lock_key(seat_id)
    current_owner = redis_client.get(key)

    if current_owner != str(user_id):
        return False

    redis_client.expire(key, LOCK_TTL_SECONDS)
    logger.info(f"Seat lock extended | seat_id={seat_id} | user_id={user_id}")
    return True