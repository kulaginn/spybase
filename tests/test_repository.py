"""Тесты поиска и избранного (Рязанцев Д.)."""

from spybase import repository as r


def test_search_filters(filled):
    res = r.search(filled, r.AdFilter(country="PL"))
    assert res["total"] > 0
    assert all(a["country"] == "PL" for a in res["items"])


def test_search_text_and_niche(filled):
    res = r.search(filled, r.AdFilter(niche="gambling", limit=100))
    assert res["total"] > 0 and all(a["niche_code"] == "gambling" for a in res["items"])
    assert r.search(filled, r.AdFilter(q="kasyno"))["total"] > 0


def test_search_is_injection_safe(filled):
    res = r.search(filled, r.AdFilter(q="' OR 1=1 --"))
    assert res["total"] == 0
    assert filled.execute("SELECT count(*) FROM ads").fetchone()[0] > 0


def test_sort_and_paging(filled):
    a = r.search(filled, r.AdFilter(sort="days_active", limit=5))
    days = [x["days_active"] for x in a["items"]]
    assert days == sorted(days, reverse=True)
    b = r.search(filled, r.AdFilter(sort="days_active", limit=5, offset=5))
    assert {x["id"] for x in a["items"]}.isdisjoint({x["id"] for x in b["items"]})


def test_card_and_favorites(filled):
    ad_id = r.search(filled, r.AdFilter(limit=1))["items"][0]["id"]
    card = r.get_ad(filled, ad_id)
    assert card and "similar" in card
    assert r.get_ad(filled, 10**9) is None
    assert r.add_favorite(filled, "demo_user", ad_id) is True
    assert r.add_favorite(filled, "demo_user", ad_id) is False      # повторное добавление
    assert [a["id"] for a in r.favorites(filled, "demo_user")] == [ad_id]
    assert r.remove_favorite(filled, "demo_user", ad_id) is True
    assert r.favorites(filled, "demo_user") == []
