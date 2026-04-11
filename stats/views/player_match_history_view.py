from django.db.models import Sum, Count
from django.shortcuts import render, get_object_or_404

from stats.models import Player, PlayerMatchStats


def player_match_history_view(request, slapshot_id):
    player = get_object_or_404(Player, slapshot_id=slapshot_id)

    stats_qs = (
        PlayerMatchStats.objects
        .select_related("match")
        .filter(player=player, match__archived=False)
        .order_by("-match__created")
    )

    agg = PlayerMatchStats.objects.filter(player=player, match__archived=False).aggregate(
        wins=Sum('wins'),
        losses=Sum('losses'),
        ot_wins=Sum('overtime_wins'),
        ot_losses=Sum('overtime_losses'),
        ot_goals=Sum('overtime_goals'),
        goals=Sum('goals'),
        assists=Sum('assists'),
        shots=Sum('shots'),
        saves=Sum('saves'),
        conceded_goals=Sum('conceded_goals'),
        blocks=Sum('blocks'),
        takeaways=Sum('takeaways'),
        turnovers=Sum('turnovers'),
        passes=Sum('passes'),
        faceoffs_won=Sum('faceoffs_won'),
        faceoffs_lost=Sum('faceoffs_lost'),
        post_hits=Sum('post_hits'),
        game_winning_goals=Sum('game_winning_goals'),
        shutouts=Sum('shutouts'),
        games=Count("match", distinct=True),
    )

    # Derived totals
    total_shots = agg['shots'] or 0
    total_goals = agg['goals'] or 0
    total_saves = agg['saves'] or 0
    total_conceded = agg['conceded_goals'] or 0
    total_fo_won = agg['faceoffs_won'] or 0
    total_fo_lost = agg['faceoffs_lost'] or 0

    totals = {
        **agg,
        'shot_pct': round((total_goals / total_shots) * 100, 1) if total_shots > 0 else None,
        'save_pct': round((total_saves / (total_saves + total_conceded)) * 100, 1) if (total_saves + total_conceded) > 0 else None,
        'faceoff_pct': round((total_fo_won / (total_fo_won + total_fo_lost)) * 100, 1) if (total_fo_won + total_fo_lost) > 0 else None,
        'points': total_goals + (agg['assists'] or 0),
    }

    match_history = []

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

        home_players = sorted(home_players, key=str.lower)
        away_players = sorted(away_players, key=str.lower)

        match_history.append(
            {
                "match": match,
                "home_players": home_players,
                "away_players": away_players,
                "home_goals": home_goals,
                "away_goals": away_goals,
                "score": ps.score or 0,
                "goals": ps.goals or 0,
                "shots": ps.shots or 0,
                "assists": ps.assists or 0,
                "saves": ps.saves or 0,
                "wins": ps.wins or 0,
                "losses": ps.losses or 0,
                "is_win": (ps.wins or 0) > 0,
            }
        )

    context = {
        "player": player,
        "match_history": match_history,
        "totals": totals,
    }
    return render(request, "stats/player_match_history.html", context)