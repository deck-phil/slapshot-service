from django.db import models
from django.db.models import Q


class Player(models.Model):
    username = models.CharField(max_length=50)
    slapshot_id = models.CharField(max_length=50, unique=True)

    class Meta:
        unique_together = ("username", "slapshot_id")

    def __str__(self):
        return f"{self.username}"


class Match(models.Model):
    match_id = models.UUIDField(primary_key=True)
    region = models.CharField(max_length=50)
    created = models.DateTimeField()
    gamemode = models.CharField(max_length=50)
    match_type = models.CharField(max_length=50)

    arena = models.CharField(max_length=100, blank=True)
    winner = models.CharField(max_length=10, blank=True)
    score_home = models.IntegerField(null=True, blank=True)
    score_away = models.IntegerField(null=True, blank=True)
    end_reason = models.CharField(max_length=50, blank=True)
    match_length = models.IntegerField(null=True, blank=True)
    current_period = models.IntegerField(null=True, blank=True)
    periods_enabled = models.BooleanField(default=False)
    custom_mercy_rule = models.IntegerField(null=True, blank=True)

    archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.match_id}"


class PlayerMatchStats(models.Model):
    TEAM_CHOICES = (("home", "Home"), ("away", "Away"))

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="player_stats")
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="match_stats")
    team = models.CharField(max_length=4, choices=TEAM_CHOICES)

    wins = models.IntegerField(null=True, blank=True)
    losses = models.IntegerField(null=True, blank=True)
    overtime_wins = models.IntegerField(null=True, blank=True)
    overtime_losses = models.IntegerField(null=True, blank=True)
    shutouts = models.IntegerField(null=True, blank=True)
    shutouts_against = models.IntegerField(null=True, blank=True)

    goals = models.IntegerField(null=True, blank=True)
    assists = models.IntegerField(null=True, blank=True)
    primary_assists = models.IntegerField(null=True, blank=True)
    secondary_assists = models.IntegerField(null=True, blank=True)
    contributed_goals = models.IntegerField(null=True, blank=True)
    game_winning_goals = models.IntegerField(null=True, blank=True)
    overtime_goals = models.IntegerField(null=True, blank=True)

    score = models.IntegerField(null=True, blank=True)
    shots = models.IntegerField(null=True, blank=True)
    saves = models.IntegerField(null=True, blank=True)
    blocks = models.IntegerField(null=True, blank=True)
    passes = models.IntegerField(null=True, blank=True)
    takeaways = models.IntegerField(null=True, blank=True)
    turnovers = models.IntegerField(null=True, blank=True)
    faceoffs_won = models.IntegerField(null=True, blank=True)
    faceoffs_lost = models.IntegerField(null=True, blank=True)
    post_hits = models.IntegerField(null=True, blank=True)

    games_played = models.IntegerField(null=True, blank=True)
    conceded_goals = models.IntegerField(null=True, blank=True)
    periods_played = models.IntegerField(null=True, blank=True)
    possession_time_sec = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("match", "player", "team")
        verbose_name = "Player Match Stat"
        verbose_name_plural = "Player Match Stats"

    def __str__(self):
        return f"{self.player} @ {self.match} ({self.team})"


class IngestionRun(models.Model):
    class IngestionType(models.TextChoices):
        ALL_PLAYERS = "ALL_PLAYERS", "All Players"
        SINGLE_PLAYER = "SINGLE_PLAYER", "Single Player"

    ingestion_type = models.CharField(
        max_length=20,
        choices=IngestionType.choices,
        default=IngestionType.ALL_PLAYERS,
    )

    # Only set when type == SINGLE_PLAYER
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ingestion_runs",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    matches_added = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                name="player_required_for_single_player",
                check=(
                        Q(ingestion_type="ALL_PLAYERS", player__isnull=True)
                        |
                        Q(ingestion_type="SINGLE_PLAYER", player__isnull=False)
                ),
            ),
        ]

    @classmethod
    def last_successful_run(cls):
        """
        Return the most recent IngestionRun that completed without an error.
        """
        return (
            cls.objects
            .filter(error_message="")
            .order_by("-created_at")
            .first()
        )

    def __str__(self):
        base = f"{self.ingestion_type}"
        if self.player_id:
            base += f" for {self.player}"
        return f"{base} at {self.created_at:%Y-%m-%d %H:%M:%S}"
