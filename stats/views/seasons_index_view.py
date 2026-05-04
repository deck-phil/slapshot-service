from django.shortcuts import render

from stats.services.season_aggregation import list_available_seasons


def seasons_index_view(request):
    seasons = list_available_seasons()
    return render(request, "stats/seasons_index.html", {
        "seasons": seasons,
    })
