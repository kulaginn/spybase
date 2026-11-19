"""Тесты сборщика (Рязанцев Д.)."""

import pytest

from spybase import collector


def raw(**kw):
    base = {"id": "a1", "is_ad": True, "advertiser": "@Brand", "country": "ar", "caption": "  hola   mundo ",
            "seen_at": "2026-11-01T10:00:00+00:00",
            "landing": "https://www.shop.example/p?utm_source=tt&id=5&ttclid=zz"}
    base.update(kw)
    return base


def test_normalize_cleans_fields():
    ad = collector.normalize(raw())
    assert ad.advertiser == "brand"
    assert ad.country == "AR"
    assert ad.caption == "hola mundo"
    assert ad.landing_url == "https://www.shop.example/p?id=5"
    assert ad.landing_domain == "shop.example"


@pytest.mark.parametrize("kw, reason", [
    ({"is_ad": False}, "не реклама"),
    ({"id": ""}, "идентификатора"),
    ({"advertiser": ""}, "рекламодателя"),
    ({"country": "ARG"}, "код страны"),
])
def test_normalize_rejects(kw, reason):
    with pytest.raises(ValueError, match=reason):
        collector.normalize(raw(**kw))


def test_collect_counts_and_dedup(con):
    rep = collector.collect(con, [raw(), raw(seen_at="2026-11-05T10:00:00+00:00"), raw(id="x", is_ad=False)])
    assert (rep.received, rep.new_ads, rep.updated, rep.rejected) == (3, 1, 1, 1)
    row = con.execute("SELECT first_seen, last_seen, seen_count FROM ads").fetchone()
    assert row["first_seen"].startswith("2026-11-01") and row["last_seen"].startswith("2026-11-05")
    assert row["seen_count"] == 2
    assert con.execute("SELECT count(*) FROM collect_log").fetchone()[0] == 1


def test_only_paid_ads_in_db(filled):
    assert filled.execute("SELECT count(*) FROM ads WHERE source_id LIKE 'organic%'").fetchone()[0] == 0
