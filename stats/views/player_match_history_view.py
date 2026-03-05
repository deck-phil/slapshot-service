# stats/views/player_match_history_view.py
from django.shortcuts import render, get_object_or_404

from stats.models import Player, PlayerMatchStats


def player_match_history_view(request, game_user_id):
    player = get_object_or_404(Player, game_user_id=game_user_id)

    stats_qs = (
        PlayerMatchStats.objects
        .select_related("match")
        .filter(player=player)
        .order_by("-match__created")
    )

    rows = []

    for ps in stats_qs:
        match = ps.match

        home_players = []
        away_players = []
        home_goals = 0
        away_goals = 0

        for s in match.player_stats.all():
            name = s.player.username

            if s.team == "home":
                home_players.append(name)
                home_goals += s.goals or 0
            elif s.team == "away":
                away_players.append(name)
                away_goals += s.goals or 0

        rows.append(
            {
                "match": match,
                "home_players": home_players,
                "away_players": away_players,
                "home_goals": home_goals,
                "away_goals": away_goals,
                "goals": ps.goals or 0,
                "assists": ps.assists or 0,
                "saves": ps.saves or 0,
                "wins": ps.wins or 0,
                "losses": ps.losses or 0,
                "is_win": (ps.wins or 0) > 0,  # highlight condition
            }
        )

    context = {
        "player": player,
        "rows": rows,
    }
    return render(request, "stats/player_match_history.html", context)
