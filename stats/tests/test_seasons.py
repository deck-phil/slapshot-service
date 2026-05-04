import uuid
from datetime import datetime, timezone as dt_timezone

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from stats.models import Match, Player, PlayerMatchStats
from stats.services.season_aggregation import (
    compute_season_stats,
    is_current_month,
    is_future_month,
    list_available_seasons,
    month_window,
    neighbor_seasons,
)


def _make_match(*, year, month, day=15, hour=12, archived=False):
    """Create a Match dated within a given month in the app local timezone."""
    app_tz = timezone.get_default_timezone()
    created_local = datetime(year, month, day, hour, 0, 0, 0, tzinfo=app_tz)
    created_utc = created_local.astimezone(dt_timezone.utc)
    return Match.objects.create(
        match_id=uuid.uuid4(),
        region="na",
        created=created_utc,
        gamemode="hockey",
        match_type="ranked",
        archived=archived,
    )


def _add_stats(match, player, **overrides):
    defaults = dict(
        team="home",
        wins=1,
        losses=0,
        overtime_wins=0,
        overtime_losses=0,
        goals=2,
        assists=1,
        shots=5,
        saves=0,
        conceded_goals=0,
        score=10,
    )
    defaults.update(overrides)
    return PlayerMatchStats.objects.create(match=match, player=player, **defaults)


class SeasonAggregationTests(TestCase):
    def setUp(self):
        self.alice = Player.objects.create(username="alice", slapshot_id="100001")
        self.bob = Player.objects.create(username="bob", slapshot_id="100002")

    def test_month_window_returns_app_tz_bounds(self):
        start, end, label, last_day = month_window(2025, 3)
        self.assertEqual(label, "March 2025")
        # March has 31 days; end should land on April 1 local.
        self.assertEqual(last_day, 31)
        self.assertLess(start, end)

    def test_compute_season_stats_filters_by_window(self):
        in_match = _make_match(year=2025, month=4, day=10)
        before_match = _make_match(year=2025, month=3, day=20)
        after_match = _make_match(year=2025, month=5, day=2)
        _add_stats(in_match, self.alice, goals=3, assists=1, wins=1)
        _add_stats(before_match, self.alice, goals=10, assists=10, wins=1)
        _add_stats(after_match, self.alice, goals=10, assists=10, wins=1)

        start, end, _, _ = month_window(2025, 4)
        result = compute_season_stats(start, end)

        self.assertEqual(len(result), 1)
        row = result[0]
        self.assertEqual(row["player_username"], "alice")
        self.assertEqual(row["total_games"], 1)
        self.assertEqual(row["total_goals"], 3)
        self.assertEqual(row["total_assists"], 1)
        self.assertEqual(row["total_points"], 4)

    def test_compute_season_stats_excludes_archived(self):
        active = _make_match(year=2025, month=4, day=10, archived=False)
        archived = _make_match(year=2025, month=4, day=11, archived=True)
        _add_stats(active, self.alice)
        _add_stats(archived, self.alice, goals=99)

        start, end, _, _ = month_window(2025, 4)
        result = compute_season_stats(start, end)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["total_goals"], 2)

    def test_compute_season_stats_no_end_includes_everything_after_start(self):
        m1 = _make_match(year=2025, month=4, day=10)
        m2 = _make_match(year=2025, month=5, day=10)
        _add_stats(m1, self.alice)
        _add_stats(m2, self.alice)

        start, _, _, _ = month_window(2025, 4)
        result = compute_season_stats(start)
        self.assertEqual(result[0]["total_games"], 2)

    def test_list_available_seasons_orders_newest_first(self):
        m_apr = _make_match(year=2025, month=4, day=15)
        m_jun = _make_match(year=2025, month=6, day=2)
        m_archived = _make_match(year=2025, month=5, day=15, archived=True)
        _add_stats(m_apr, self.alice)
        _add_stats(m_jun, self.alice)
        _add_stats(m_archived, self.alice)

        seasons = list_available_seasons()
        keys = [(s["year"], s["month"]) for s in seasons]
        self.assertEqual(keys, [(2025, 6), (2025, 4)])
        self.assertEqual(seasons[0]["games"], 1)
        self.assertEqual(seasons[0]["players"], 1)

    def test_neighbor_seasons(self):
        for month in (3, 4, 6):
            m = _make_match(year=2025, month=month, day=10)
            _add_stats(m, self.alice)
        seasons = list_available_seasons()
        prev_, next_ = neighbor_seasons(2025, 4, seasons)
        self.assertEqual((prev_["year"], prev_["month"]), (2025, 3))
        self.assertEqual((next_["year"], next_["month"]), (2025, 6))

    def test_is_future_and_current_month(self):
        app_tz = timezone.get_default_timezone()
        now_local = timezone.now().astimezone(app_tz)
        self.assertTrue(is_current_month(now_local.year, now_local.month))
        future_year = now_local.year + 1
        self.assertTrue(is_future_month(future_year, 1))
        self.assertFalse(is_future_month(2000, 1))


class SeasonViewsTests(TestCase):
    def setUp(self):
        self.alice = Player.objects.create(username="alice", slapshot_id="100001")

    def test_seasons_index_empty(self):
        resp = self.client.get(reverse("seasons_index"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No seasons recorded yet")

    def test_seasons_index_lists_buckets(self):
        m = _make_match(year=2025, month=4, day=10)
        _add_stats(m, self.alice)
        resp = self.client.get(reverse("seasons_index"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "April 2025")

    def _assert_404_or_redirect(self, resp):
        # Project's custom 404 handler redirects 404s to "/", so accept either
        # a real 404 (raise_request_exception=False path) or the redirect to "/".
        self.assertIn(resp.status_code, (302, 404))
        if resp.status_code == 302:
            self.assertEqual(resp["Location"], "/")

    def test_season_detail_404_invalid_month(self):
        # Note: the URL converter `<int:month>` rejects "13" formatting via the path,
        # but our view also defends with a 1-12 range check. Probe with reverse only
        # for valid ints; for "0" we exercise the view-level guard.
        resp = self.client.get("/seasons/2025-0/")
        self._assert_404_or_redirect(resp)
        resp = self.client.get("/seasons/2025-13/")
        self._assert_404_or_redirect(resp)

    def test_season_detail_404_future_month(self):
        app_tz = timezone.get_default_timezone()
        now_local = timezone.now().astimezone(app_tz)
        future_year = now_local.year + 5
        resp = self.client.get(reverse("season_detail", args=[future_year, 1]))
        self._assert_404_or_redirect(resp)

    def test_season_detail_404_no_data_past(self):
        # An old month with no matches at all should 404.
        resp = self.client.get(reverse("season_detail", args=[2000, 1]))
        self._assert_404_or_redirect(resp)

    def test_season_detail_renders_with_data(self):
        m = _make_match(year=2025, month=4, day=10)
        _add_stats(m, self.alice)
        resp = self.client.get(reverse("season_detail", args=[2025, 4]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "April 2025")
        self.assertContains(resp, "alice")

    def test_season_detail_current_month_renders_even_with_no_data(self):
        app_tz = timezone.get_default_timezone()
        now_local = timezone.now().astimezone(app_tz)
        resp = self.client.get(reverse("season_detail", args=[now_local.year, now_local.month]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "current")

    def test_current_season_page_still_works(self):
        m = _make_match(
            year=timezone.now().astimezone(timezone.get_default_timezone()).year,
            month=timezone.now().astimezone(timezone.get_default_timezone()).month,
            day=1,
        )
        _add_stats(m, self.alice)
        resp = self.client.get(reverse("season_stats"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "alice")
