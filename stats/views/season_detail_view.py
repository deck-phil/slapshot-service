from django.http import Http404
from django.shortcuts import render

from stats.models import IngestionRun
from stats.services.season_aggregation import (
    compute_season_stats,
    is_current_month,
    is_future_month,
    list_available_seasons,
    month_window,
    neighbor_seasons,
)


def season_detail_view(request, year, month):
    if month < 1 or month > 12:
        raise Http404("Invalid month")
    if is_future_month(year, month):
        raise Http404("Future season")

    available = list_available_seasons()
    has_data = any(s["year"] == year and s["month"] == month for s in available)
    current = is_current_month(year, month)

    # No data and not the current month -> 404. Allow current month even with no data.
    if not has_data and not current:
        raise Http404("No data for this season")

    start, end, label, _ = month_window(year, month)
    players = compute_season_stats(start, end)
    last_ingestion = IngestionRun.last_successful_run()
    previous_season, next_season = neighbor_seasons(year, month, available)

    return render(request, "stats/season_detail.html", {
        "season_label": label,
        "season_year": year,
        "season_month": month,
        "season_start": start,
        "season_end": end,
        "is_current": current,
        "players": players,
        "last_ingestion": last_ingestion,
        "previous_season": previous_season,
        "next_season": next_season,
    })
