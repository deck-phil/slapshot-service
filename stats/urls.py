from django.urls import path

from stats.views.ingest_trigger_view import ingest_trigger_view
from stats.views.match_history_view import match_history_view
from stats.views.player_match_history_view import player_match_history_view
from stats.views.player_totals_view import player_totals_view
from stats.views.season_stats_view import season_stats_view

urlpatterns = [
    path("", season_stats_view, name="season_stats"),
    path("all-time/", player_totals_view, name="player_totals"),
    path("ingest/", ingest_trigger_view, name="ingest_trigger"),
    path("history/", match_history_view, name="match_history"),
    path("history/<int:slapshot_id>/", player_match_history_view, name="player_match_history"),
]
