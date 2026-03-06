from django.core.management.base import BaseCommand
from stats.ingest import ingest_all_players


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
        ingest_all_players(limit=limit)
