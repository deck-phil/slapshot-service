# stats/admin.py
from django.contrib import admin
from django.utils.translation import ngettext
from rangefilter.filters import DateRangeFilter

from .models import Match, Player, PlayerMatchStats, IngestionRun


@admin.action(description="Archive selected matches")
def archive_matches(modeladmin, request, queryset):
    updated = queryset.update(archived=True)
    modeladmin.message_user(
        request,
        ngettext(
            "%d match was archived.",
            "%d matches were archived.",
            updated,
        )
        % updated,
    )


@admin.action(description="Unarchive selected matches")
def unarchive_matches(modeladmin, request, queryset):
    updated = queryset.update(archived=False)
    modeladmin.message_user(
        request,
        ngettext(
            "%d match was unarchived.",
            "%d matches were unarchived.",
            updated,
        )
        % updated,
    )


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("created", "match_id", "winner", "periods_enabled", "archived")
    list_filter = (("created", DateRangeFilter), "periods_enabled")
    search_fields = ("match_id",)
    ordering = ("-created",)
    actions = [archive_matches, unarchive_matches]


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("username", "slapshot_id")
    search_fields = ("username", "slapshot_id")
    ordering = ("-slapshot_id",)


@admin.register(PlayerMatchStats)
class PlayerMatchStatsAdmin(admin.ModelAdmin):
    list_display = ("match__created", "player", "team", "goals", "assists", "score", "wins", "losses")
    list_filter = ("player",)
    search_fields = ("player__username", "player__slapshot_id", "match__match_id")
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
        "player__slapshot_id",
        "error_message",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def short_error(self, obj):
        if not obj.error_message:
            return ""
        return (obj.error_message[:60] + "…") if len(obj.error_message) > 60 else obj.error_message

    short_error.short_description = "Error"
