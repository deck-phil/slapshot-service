from datetime import timezone as dt_timezone

from django.db.models import Sum, Count
from django.shortcuts import render
from django.utils import timezone

from stats.models import PlayerMatchStats, IngestionRun


def season_stats_view(request):
    app_tz = timezone.get_default_timezone()

    now_local = timezone.now().astimezone(app_tz)
    season_start_local = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    season_start = season_start_local.astimezone(dt_timezone.utc)
    season_label = now_local.strftime("%B %Y")

    qs = (
        PlayerMatchStats.objects
        .filter(
            match__archived=False,
            match__created__gte=season_start,
        )
        .values("player_id", "player__slapshot_id", "player__username")
        .annotate(
            sum_wins=Sum("wins"),
            sum_losses=Sum("losses"),
            sum_ot_wins=Sum("overtime_wins"),
            sum_ot_losses=Sum("overtime_losses"),
            total_goals=Sum("goals"),
            total_shots=Sum("shots"),
            total_assists=Sum("assists"),
            total_saves=Sum("saves"),
            total_conceded=Sum("conceded_goals"),
            total_blocks=Sum("blocks"),
            total_takeaways=Sum("takeaways"),
            total_turnovers=Sum("turnovers"),
            total_gwg=Sum("game_winning_goals"),
            total_ot_goals=Sum("overtime_goals"),
            total_faceoffs_won=Sum("faceoffs_won"),
            total_faceoffs_lost=Sum("faceoffs_lost"),
            total_passes=Sum("passes"),
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
        ot_wins = row["sum_ot_wins"] or 0
        ot_losses = row["sum_ot_losses"] or 0

        total_wins = raw_wins
        total_losses = max(games - total_wins, raw_losses)

        goals = row["total_goals"] or 0
        assists = row["total_assists"] or 0
        shots = row["total_shots"] or 0
        saves = row["total_saves"] or 0
        conceded = row["total_conceded"] or 0
        faceoffs_won = row["total_faceoffs_won"] or 0
        faceoffs_lost = row["total_faceoffs_lost"] or 0
        total_score = row["total_score"] or 0

        points = goals + assists

        if games > 0:
            goals_per_game = goals / games
            assists_per_game = assists / games
            points_per_game = points / games
            score_per_game = total_score / games
            win_pct = (total_wins / games) * 100
        else:
            goals_per_game = assists_per_game = points_per_game = score_per_game = win_pct = 0.0

        shot_pct = (goals / shots * 100) if shots else None
        save_pct = (saves / (saves + conceded) * 100) if (saves + conceded) else None
        faceoff_pct = (faceoffs_won / (faceoffs_won + faceoffs_lost) * 100) if (faceoffs_won + faceoffs_lost) else None

        players.append(
            {
                "slapshot_id": row["player__slapshot_id"],
                "player_username": row["player__username"],
                "total_games": games,
                "total_wins": total_wins,
                "total_losses": total_losses,
                "total_ot_wins": ot_wins,
                "total_ot_losses": ot_losses,
                "total_goals": goals,
                "total_assists": assists,
                "total_points": points,
                "total_shots": shots,
                "total_saves": saves,
                "total_blocks": row["total_blocks"] or 0,
                "total_takeaways": row["total_takeaways"] or 0,
                "total_turnovers": row["total_turnovers"] or 0,
                "total_gwg": row["total_gwg"] or 0,
                "total_ot_goals": row["total_ot_goals"] or 0,
                "total_passes": row["total_passes"] or 0,
                "goals_per_game": goals_per_game,
                "assists_per_game": assists_per_game,
                "points_per_game": points_per_game,
                "score_per_game": score_per_game,
                "win_pct": win_pct,
                "shot_pct": shot_pct,
                "save_pct": save_pct,
                "faceoff_pct": faceoff_pct,
            }
        )

    last_ingestion = IngestionRun.last_successful_run()

    return render(request, "stats/season_stats.html", {
        "last_ingestion": last_ingestion,
        "players": players,
        "season_label": season_label,
    })
