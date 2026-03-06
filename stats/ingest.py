import requests
from uuid import UUID

from django.utils.dateparse import parse_datetime

from .models import Match, Player, PlayerMatchStats


SLAPSHOT_BASE_URL = "https://slapshot.gg/api/game/players"


def ingest_all_players(limit: int | None = None) -> None:
    """
    Loop over Player rows and ingest each one.
    """
    qs = Player.objects.order_by("game_user_id")
    if limit is not None:
        qs = qs[:limit]

    total = qs.count()
    print(f"[all] Found {total} players")

    for idx, player in enumerate(qs, start=1):
        label = player.username or ""
        print(f"[all] [{idx}/{total}] Ingesting {label} ({player.game_user_id})")
        try:
            ingest_player_by_id(player.game_user_id)
        except Exception as e:
            print(f"[all][ERROR] Error ingesting {player.game_user_id}: {e}")

    print("[all] Done ingesting all players")


def ingest_player_by_id(game_user_id: str) -> None:
    """
    High-level helper: fetch JSON from Slapshot API and ingest all whitelisted matches.
    """
    print(f"[ingest] === Ingest run started for game_user_id={game_user_id} ===")
    payload = fetch_player_json(game_user_id)
    ingest_payload(payload)
    print(f"[ingest] === Ingest run finished for game_user_id={game_user_id} ===")


def fetch_player_json(game_user_id: str) -> dict:
    """
    Call the Slapshot API and return the JSON payload for a given game_user_id.
    URL: https://slapshot.gg/api/game/players/<game_user_id>
    """
    url = f"{SLAPSHOT_BASE_URL}/{game_user_id}"
    print(f"[ingest] Fetching data for game_user_id={game_user_id} from {url}")
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data


def get_whitelisted_ids() -> set[str]:
    """
    Load all whitelisted game_user_id values from the database.
    """
    ids = set(Player.objects.values_list("game_user_id", flat=True))
    return ids


def get_non_whitelisted_players(match_data: dict, whitelist_ids: set[str]) -> list[dict]:
    """
    Return a list of player dicts whose game_user_id is NOT in the whitelist.
    """
    game_stats = match_data.get("game_stats") or {}
    players = game_stats.get("players") or []
    return [
        p
        for p in players
        if p.get("game_user_id") not in whitelist_ids
    ]


def match_all_players_whitelisted(match_data: dict, whitelist_ids: set[str]) -> bool:
    """
    True only if every player's game_user_id is in the whitelist.
    """
    game_stats = match_data.get("game_stats") or {}
    players = game_stats.get("players") or []
    if not players:
        return False
    return all(
        (p.get("game_user_id") in whitelist_ids)
        for p in players
    )


def ingest_payload(payload: dict) -> None:
    """
    Given the full JSON payload from the Slapshot API for one player,
    iterate over match_history and ingest only matches that pass the
    whitelist check.
    """
    match_history = payload.get("match_history", [])
    total_matches = len(match_history)
    ingested_matches = 0
    skipped_whitelist = 0
    skipped_no_stats = 0

    whitelist_ids = get_whitelisted_ids()

    print(f"[ingest] Starting ingest for {total_matches} matches")

    for match_data in match_history:
        match_id = match_data.get("id")

        if not match_data.get("game_stats"):
            skipped_no_stats += 1
            print(f"[ingest] Skipping match {match_id} (no game_stats)")
            continue

        if not match_all_players_whitelisted(match_data, whitelist_ids):
            skipped_whitelist += 1
            non_whitelisted = get_non_whitelisted_players(match_data, whitelist_ids)
            details = ", ".join(
                f"{p.get('username')}({p.get('game_user_id')})"
                for p in non_whitelisted
            ) or "no players listed"
            print(
                f"[ingest] Skipping match {match_id} "
                f"(whitelist check failed: non-whitelisted players: {details})"
            )
            continue

        ingest_match(match_data)
        ingested_matches += 1

    print(
        f"[ingest] Done. "
        f"Total: {total_matches}, "
        f"Ingested: {ingested_matches}, "
        f"Skipped (whitelist): {skipped_whitelist}, "
        f"Skipped (no stats): {skipped_no_stats}"
    )


def ingest_match(match_data: dict) -> Match:
    """
    Create or update a Match row and associated Player + PlayerMatchStats rows
    for one match JSON object.
    """
    game_stats = match_data.get("game_stats") or {}
    score = game_stats.get("score") or {}

    match_id = match_data["id"]
    print(f"[ingest] Processing match {match_id}")

    match, created = Match.objects.update_or_create(
        match_id=UUID(match_id),
        defaults={
            "region": match_data.get("region", ""),
            "created": parse_datetime(match_data["created"]),
            "gamemode": match_data.get("gamemode", ""),
            "match_type": match_data.get("match_type", ""),
            "arena": game_stats.get("arena", ""),
            "winner": game_stats.get("winner", ""),
            "score_home": score.get("home"),
            "score_away": score.get("away"),
            "end_reason": game_stats.get("end_reason", match_data.get("end_reason", "")),
            "match_length": int(
                game_stats.get("match_length", match_data.get("match_length", "0")) or 0
            ),
            "current_period": int(
                game_stats.get("current_period", match_data.get("current_period", "0")) or 0
            ),
            "periods_enabled": str(
                game_stats.get("periods_enabled", match_data.get("periods_enabled", "False"))
            ).lower()
            == "true",
            "custom_mercy_rule": int(
                game_stats.get("custom_mercy_rule", match_data.get("custom_mercy_rule", "0")) or 0
            ),
        },
    )

    print(
        f"[ingest] Match {match_id} "
        f"{'created' if created else 'updated'} in DB"
    )

    players = game_stats.get("players") or []
    created_stats = 0

    for player_data in players:
        player_obj, player_created = Player.objects.get_or_create(
            game_user_id=player_data.get("game_user_id", ""),
            defaults={
                "username": player_data.get("username", ""),
            },
        )

        stats = player_data.get("stats") or {}

        _, created_stats_row = PlayerMatchStats.objects.update_or_create(
            match=match,
            player=player_obj,
            team=player_data.get("team", ""),
            defaults={
                "wins": stats.get("wins"),
                "losses": stats.get("losses"),
                "overtime_wins": stats.get("overtime_wins"),
                "overtime_losses": stats.get("overtime_losses"),
                "shutouts": stats.get("shutouts"),
                "shutouts_against": stats.get("shutouts_against"),
                "goals": stats.get("goals"),
                "assists": stats.get("assists"),
                "primary_assists": stats.get("primary_assists"),
                "secondary_assists": stats.get("secondary_assists"),
                "contributed_goals": stats.get("contributed_goals"),
                "game_winning_goals": stats.get("game_winning_goals"),
                "overtime_goals": stats.get("overtime_goals"),
                "score": stats.get("score"),
                "shots": stats.get("shots"),
                "saves": stats.get("saves"),
                "blocks": stats.get("blocks"),
                "passes": stats.get("passes"),
                "takeaways": stats.get("takeaways"),
                "turnovers": stats.get("turnovers"),
                "faceoffs_won": stats.get("faceoffs_won"),
                "faceoffs_lost": stats.get("faceoffs_lost"),
                "post_hits": stats.get("post_hits"),
                "games_played": stats.get("games_played"),
                "conceded_goals": stats.get("conceded_goals"),
                "periods_played": stats.get("periods_played"),
                "possession_time_sec": stats.get("possession_time_sec"),
            },
        )
        if created_stats_row:
            created_stats += 1

    print(
        f"[ingest] For match {match_id}: "
        f"created {created_stats} PlayerMatchStats rows"
    )

    return match

