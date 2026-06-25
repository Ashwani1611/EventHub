import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Event
from .embedding_service import index_event

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Event)
def on_event_saved(sender, instance, created, **kwargs):
    """
    Auto-index event in ChromaDB whenever it is created or updated.
    Only index published events.
    """
    if instance.status != Event.Status.PUBLISHED:
        logger.info(
            f"Skipping ChromaDB index | event_id={instance.id} | "
            f"status={instance.status}"
        )
        return

    logger.info(
        f"Indexing event in ChromaDB | event_id={instance.id} | "
        f"created={created}"
    )
    index_event(instance)