from calendar import monthrange
from datetime import datetime, timezone as dt_timezone

from django.db.models import Count, Sum
from django.utils import timezone

from stats.models import PlayerMatchStats


def month_window(year, month):
    """Return (start_utc, end_utc, label) for the given calendar month in app TZ."""
    app_tz = timezone.get_default_timezone()
    start_local = datetime(year, month, 1, 0, 0, 0, 0, tzinfo=app_tz)
    last_day = monthrange(year, month)[1]
    if month == 12:
        end_local = datetime(year + 1, 1, 1, 0, 0, 0, 0, tzinfo=app_tz)
    else:
        end_local = datetime(year, month + 1, 1, 0, 0, 0, 0, tzinfo=app_tz)
    label = start_local.strftime("%B %Y")
    return (
        start_local.astimezone(dt_timezone.utc),
        end_local.astimezone(dt_timezone.utc),
        label,
        last_day,
    )


def current_month_window():
    app_tz = timezone.get_default_timezone()
    now_local = timezone.now().astimezone(app_tz)
    return month_window(now_local.year, now_local.month)


def is_current_month(year, month):
    app_tz = timezone.get_default_timezone()
    now_local = timezone.now().astimezone(app_tz)
    return now_local.year == year and now_local.month == month


def is_future_month(year, month):
    app_tz = timezone.get_default_timezone()
    now_local = timezone.now().astimezone(app_tz)
    if year > now_local.year:
        return True
    if year == now_local.year and month > now_local.month:
        return True
    return False


def compute_season_stats(start, end=None):
    """Aggregate PlayerMatchStats into a leaderboard list.

    Args:
        start: timezone-aware UTC datetime (inclusive lower bound on match.created).
        end: optional timezone-aware UTC datetime (exclusive upper bound on match.created).

    Returns:
        A list of player-stat dicts shaped to match the season template's expectations.
    """
    filters = {
        "match__archived": False,
        "match__created__gte": start,
    }
    if end is not None:
        filters["match__created__lt"] = end

    qs = (
        PlayerMatchStats.objects
        .filter(**filters)
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

    return players


def list_available_seasons():
    """Return list of {year, month, label, start, end, games, players} dicts.

    Includes every (year, month) bucket that has at least one non-archived match,
    newest first. Bucketing is based on match.created in the app local timezone.
    """
    from stats.models import Match  # local import to avoid cycles

    app_tz = timezone.get_default_timezone()

    match_to_key = {}
    for match_id, created in Match.objects.filter(archived=False).values_list("match_id", "created"):
        local = created.astimezone(app_tz)
        match_to_key[match_id] = (local.year, local.month)

    buckets = {}
    for match_id, key in match_to_key.items():
        bucket = buckets.setdefault(key, {"match_ids": set(), "players": set()})
        bucket["match_ids"].add(match_id)

    pms_rows = (
        PlayerMatchStats.objects
        .filter(match__archived=False)
        .values_list("match_id", "player_id")
    )
    for match_id, player_id in pms_rows:
        key = match_to_key.get(match_id)
        if key is not None:
            buckets[key]["players"].add(player_id)

    seasons = []
    for (year, month), data in buckets.items():
        start, end, label, _ = month_window(year, month)
        seasons.append({
            "year": year,
            "month": month,
            "label": label,
            "start": start,
            "end": end,
            "games": len(data["match_ids"]),
            "players": len(data["players"]),
            "is_current": is_current_month(year, month),
        })

    seasons.sort(key=lambda s: (s["year"], s["month"]), reverse=True)
    return seasons


def neighbor_seasons(year, month, available_seasons=None):
    """Return (previous, next) season dicts adjacent to (year, month) in available list.

    `available_seasons` is the list returned by list_available_seasons(); if None it is
    fetched. Returns the chronologically previous and next entries that have data, or
    None when no neighbor exists. Newest entries appear first in the source list, so
    "previous" (older) is the next index and "next" (newer) is the prior index.
    """
    if available_seasons is None:
        available_seasons = list_available_seasons()

    target_index = None
    for i, s in enumerate(available_seasons):
        if s["year"] == year and s["month"] == month:
            target_index = i
            break

    previous = None
    next_ = None
    if target_index is not None:
        if target_index + 1 < len(available_seasons):
            previous = available_seasons[target_index + 1]
        if target_index - 1 >= 0:
            next_ = available_seasons[target_index - 1]
    else:
        # Target month has no data; find nearest neighbors anyway.
        # available_seasons is sorted newest-first.
        target_key = (year, month)
        for s in available_seasons:
            s_key = (s["year"], s["month"])
            if s_key > target_key:
                next_ = s  # keep overwriting; the last one wins (closest above target)
            elif s_key < target_key and previous is None:
                previous = s

    return previous, next_
