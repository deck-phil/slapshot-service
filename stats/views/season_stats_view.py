from django.shortcuts import render

from stats.models import IngestionRun
from stats.services.season_aggregation import compute_season_stats, current_month_window


def season_stats_view(request):
    season_start, _season_end, season_label, _ = current_month_window()

    # Current Season page intentionally does not pass an end bound, preserving
    # the historical behavior of "everything since the start of this month."
    players = compute_season_stats(season_start)

    last_ingestion = IngestionRun.last_successful_run()

    return render(request, "stats/season_stats.html", {
        "last_ingestion": last_ingestion,
        "players": players,
        "season_label": season_label,
    })
