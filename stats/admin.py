# stats/admin.py
from django.contrib import admin
from .models import Match, Player, PlayerMatchStats, IngestionRun


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("created", "match_id", "winner", "periods_enabled")
    list_filter = ("gamemode", "match_type", "region", "winner")
    search_fields = ("match_id",)
    ordering = ("-created",)


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("username", "game_user_id")
    search_fields = ("username", "game_user_id")
    ordering = ("-game_user_id",)


@admin.register(PlayerMatchStats)
class PlayerMatchStatsAdmin(admin.ModelAdmin):
    list_display = ("match__created", "player", "team", "goals", "assists", "score", "wins", "losses")
    list_filter = ("team",)
    search_fields = ("player__username", "player__game_user_id", "match__match_id")
    ordering = ("-match__created",)


@admin.register(IngestionRun)
class IngestionRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ingestion_type",
        "player",
        "matches_added",
        "short_error",
        "created_at",
        "finished_at",
    )
    list_filter = ("ingestion_type", "player")
    search_fields = (
        "player__username",
        "player__game_user_id",
        "error_message",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def short_error(self, obj):
        if not obj.error_message:
            return ""
        return (obj.error_message[:60] + "…") if len(obj.error_message) > 60 else obj.error_message

    short_error.short_description = "Error"
