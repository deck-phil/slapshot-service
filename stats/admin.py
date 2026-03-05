# stats/admin.py
from django.contrib import admin
from .models import WhitelistedPlayer, Match, Player, PlayerMatchStats


@admin.register(WhitelistedPlayer)
class WhitelistedPlayerAdmin(admin.ModelAdmin):
    list_display = ("username_hint", "game_user_id")
    search_fields = ("username_hint", "game_user_id")
    ordering = ("-game_user_id",)


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
