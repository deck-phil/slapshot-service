from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from stats.ingest import ingest_all_players
from stats.models import IngestionRun


class Command(BaseCommand):
    help = "Ingest match history for all players"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Optional max number of players to ingest",
        )

    def handle(self, *args, **options):
        limit = options["limit"]

        ingestion_run = IngestionRun.objects.create(
            ingestion_type=IngestionRun.IngestionType.ALL_PLAYERS,
        )

        try:
            matches_added = ingest_all_players(limit=limit)
            ingestion_run.matches_added = matches_added
        except Exception as exc:
            ingestion_run.error_message = str(exc)
            raise CommandError(
                f"All-players ingestion failed (limit={limit!r}): {exc}"
            )
        finally:
            ingestion_run.finished_at = timezone.now()
            ingestion_run.save(
                update_fields=["matches_added", "error_message", "finished_at"]
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"All-players ingestion completed, "
                f"new matches inserted: {ingestion_run.matches_added}"
            )
        )
