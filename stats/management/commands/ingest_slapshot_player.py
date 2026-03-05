from django.core.management.base import BaseCommand
from stats.ingest import ingest_player_by_id


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
        ingest_player_by_id(game_user_id)
        self.stdout.write(self.style.SUCCESS(f"Ingested matches for {game_user_id}"))
