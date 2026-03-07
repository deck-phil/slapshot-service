from django.db.models import Sum, Count
from django.shortcuts import render

from stats.models import PlayerMatchStats, IngestionRun


def player_totals_view(request):
    qs = (
        PlayerMatchStats.objects
        .values("player_id", "player__game_user_id", "player__username")
        .annotate(
            sum_wins=Sum("wins"),
            sum_losses=Sum("losses"),
            total_goals=Sum("goals"),
            total_shots=Sum("shots"),
            total_assists=Sum("assists"),
            total_saves=Sum("saves"),
            total_score=Sum("score", distinct=True),
            total_games=Count("match", distinct=True),
        )
        .order_by("-total_games")
    )

    players = []
    for row in qs:
        games = row["total_games"] or 0

        raw_wins = row["sum_wins"] or 0
        raw_losses = row["sum_losses"] or 0

        # Each game must be win or loss. Any game not counted as a win is a loss.
        total_wins = raw_wins
        total_losses = max(games - total_wins, raw_losses)

        goals = row["total_goals"] or 0
        total_score = row["total_score"] or 0

        if games > 0:
            goals_per_game = goals / games
            score_per_game = total_score / games
            win_pct = (total_wins / games) * 100
        else:
            goals_per_game = 0.0
            score_per_game = 0.0
            win_pct = 0.0

        players.append(
            {
                "player_pk": row["player_id"],
                "player_game_user_id": row["player__game_user_id"],
                "player_username": row["player__username"],
                "total_games": games,
                "total_wins": total_wins,
                "total_losses": total_losses,
                "total_goals": goals,
                "total_shots": row["total_shots"] or 0,
                "total_assists": row["total_assists"] or 0,
                "total_saves": row["total_saves"] or 0,
                "goals_per_game": goals_per_game,
                "score_per_game": score_per_game,
                "win_pct": win_pct,
            }
        )

    last_ingestion = IngestionRun.last_successful_run()

    return render(request, "stats/player_totals.html", {"last_ingestion": last_ingestion,
                                                        "players": players})
