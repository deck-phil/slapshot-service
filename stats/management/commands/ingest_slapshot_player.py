from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from stats.ingest import ingest_player_by_id
from stats.models import IngestionRun, Player


class Command(BaseCommand):
    help = "Fetch Slapshot player JSON and store it in the DB (matches + stats only)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--game-user-id",
            type=str,
            default="1831553",
            help="Slapshot game_user_id to ingest",
        )

    def handle(self, *args, **options):
        game_user_id = options["game_user_id"]

        try:
            player = Player.objects.get(game_user_id=game_user_id)
        except Player.DoesNotExist:
            msg = f"Could not find player with game_user_id: {game_user_id}"
            raise CommandError(msg)

        ingestion_run = IngestionRun.objects.create(
            ingestion_type=IngestionRun.IngestionType.SINGLE_PLAYER,
            player=player
        )

        try:
            matches_added = ingest_player_by_id(game_user_id)
            ingestion_run.matches_added = matches_added
        except Exception as exc:
            ingestion_run.error_message = str(exc)
            raise CommandError(f"Ingestion failed for {player} ({game_user_id}): {exc}")
        finally:
            ingestion_run.finished_at = timezone.now()
            ingestion_run.save(
                update_fields=["matches_added", "error_message", "finished_at"]
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Ingested {ingestion_run.matches_added} new matches for {player} ({game_user_id})"
            )
        )
