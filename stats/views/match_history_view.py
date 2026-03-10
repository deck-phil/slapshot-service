from django.shortcuts import render

from stats.models import Match, PlayerMatchStats


def match_history_view(request):
    matches = Match.objects.order_by("-created")[:50]

    # Build a list of dicts with extra info for the template
    match_rows = []

    for match in matches:
        # All stats for this match
        stats_qs = PlayerMatchStats.objects.filter(match=match)

        home_players = []
        away_players = []
        home_goals = 0
        away_goals = 0

        for ps in stats_qs:
            name = ps.player.username
            entry = {
                "name": name,
                "goals": ps.goals or 0,
            }

            if ps.team == "home":
                home_players.append(entry)
                home_goals += entry["goals"]
            elif ps.team == "away":
                away_players.append(entry)
                away_goals += entry["goals"]

        home_players = sorted(home_players, key=lambda p: p["name"].lower())
        away_players = sorted(away_players, key=lambda p: p["name"].lower())

        match_rows.append(
            {
                "match": match,
                "home_players": home_players,
                "away_players": away_players,
                "home_goals": home_goals,
                "away_goals": away_goals,
            }
        )

    return render(request, "stats/match_history.html", {"match_rows": match_rows})
