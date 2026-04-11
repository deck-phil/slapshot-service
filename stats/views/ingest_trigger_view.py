from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

from stats.ingest import ingest_all_players
from stats.models import IngestionRun


def staff_check(user):
    return user.is_active and user.is_staff


@login_required
@user_passes_test(staff_check)
def ingest_trigger_view(request):
    if request.method == "POST":

        ingestion_run = IngestionRun.objects.create(
            ingestion_type=IngestionRun.IngestionType.ALL_PLAYERS,
        )

        try:
            matches_added = ingest_all_players()
            ingestion_run.matches_added = matches_added
        except Exception as exc:
            ingestion_run.error_message = str(exc)
            raise
        finally:
            ingestion_run.finished_at = timezone.now()
            ingestion_run.save(update_fields=["matches_added", "error_message", "finished_at"])

        ran_at = date_format(timezone.localtime(ingestion_run.finished_at), "M j, Y, P")
        match_word = "game" if ingestion_run.matches_added == 1 else "games"
        messages.success(request, "Ingest completed.")
        messages.success(request, f"Ran at {ran_at}.")
        messages.success(request, f"{ingestion_run.matches_added} {match_word} ingested.")
        return redirect(reverse("ingest_trigger"))

    RECENT_RUN_LIMIT = 25
    ingestion_runs = IngestionRun.objects.select_related("player").all()[:RECENT_RUN_LIMIT]

    return render(request, "stats/ingest_trigger.html", {
        "ingestion_runs": ingestion_runs,
        "run_limit": RECENT_RUN_LIMIT,
    })
