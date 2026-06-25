from django.core.management.base import BaseCommand
from events.models import Event
from events.embedding_service import index_event


class Command(BaseCommand):
    help = "Index all published events into ChromaDB"

    def handle(self, *args, **kwargs):
        events = Event.objects.filter(status=Event.Status.PUBLISHED)
        total = events.count()

        if total == 0:
            self.stdout.write("No published events found.")
            return

        self.stdout.write(f"Indexing {total} events...")

        for event in events:
            index_event(event)
            self.stdout.write(f"  ✓ [{event.id}] {event.title}")

        self.stdout.write(self.style.SUCCESS(f"\nDone. {total} events indexed."))