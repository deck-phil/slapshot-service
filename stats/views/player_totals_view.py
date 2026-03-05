from django.db.models import Sum, Count
from django.shortcuts import render

from stats.models import PlayerMatchStats


def player_totals_view(request):
    qs = (
        PlayerMatchStats.objects
        .values("player_id", "player__game_user_id", "player__username")
        .annotate(
            total_wins=Sum("wins"),
            total_losses=Sum("losses"),
            total_goals=Sum("goals"),
            total_assists=Sum("assists"),
            total_saves=Sum("saves"),
            # count distinct matches per player
            total_games=Count("match", distinct=True),
        )
        .order_by("-total_games")
    )

    players = []
    for row in qs:
        games = row["total_games"] or 0
        wins = row["total_wins"] or 0
        goals = row["total_goals"] or 0

        if games > 0:
            goals_per_game = goals / games
            win_pct = (wins / games) * 100
        else:
            goals_per_game = 0.0
            win_pct = 0.0

        players.append(
            {
                "player_id": row["player__game_user_id"],
                "player_username": row["player__username"],
                "total_games": games,
                "total_wins": wins,
                "total_losses": row["total_losses"] or 0,
                "total_goals": goals,
                "total_assists": row["total_assists"] or 0,
                "total_saves": row["total_saves"] or 0,
                "goals_per_game": goals_per_game,
                "win_pct": win_pct,
            }
        )

    return render(request, "stats/player_totals.html", {"players": players})
