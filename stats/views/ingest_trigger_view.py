from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse

from stats.ingest import ingest_all_players


def staff_check(user):
    return user.is_active and user.is_staff


@login_required
@user_passes_test(staff_check)
def ingest_trigger_view(request):
    if request.method == "POST":
        ingest_all_players()
        messages.success(request, "Ingest completed.")
        return redirect(reverse("ingest_trigger"))

    return render(request, "stats/ingest_trigger.html")
