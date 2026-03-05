from django.db import models


class WhitelistedPlayer(models.Model):
    game_user_id = models.CharField(max_length=50, unique=True)
    username_hint = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional label so you remember who this is",
    )

    def __str__(self):
        return self.username_hint or self.game_user_id

    class Meta:
        verbose_name = "Whitelisted Player"
        verbose_name_plural = "Whitelisted Players"


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

    def __str__(self):
        return f"{self.match_id}"


class Player(models.Model):
    username = models.CharField(max_length=50)
    game_user_id = models.CharField(max_length=50, unique=True)

    class Meta:
        unique_together = ("username", "game_user_id")

    def __str__(self):
        return f"{self.username}"


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


