"""Тесты аналитики: срок показа и группировка похожих (Исматов А.)."""

from datetime import datetime, timezone

from spybase import analytics as a


def test_days_active():
    assert a.days_active("2026-11-01T10:00:00+00:00", "2026-11-01T20:00:00+00:00") == 1
    assert a.days_active("2026-11-01T10:00:00+00:00", "2026-11-10T09:00:00+00:00") == 9


def test_is_active():
    today = datetime(2026, 11, 19, tzinfo=timezone.utc)
    assert a.is_active("2026-11-18T10:00:00+00:00", today)
    assert not a.is_active("2026-11-01T10:00:00+00:00", today)


def test_same_offer_different_bonus_same_group():
    k1 = a.group_key("Jugá en Lucky Joker: 500% de bono + 250 giros gratis", "luckyjoker.example")
    k2 = a.group_key("Jugá en Lucky Joker: 300% de bono + 100 giros gratis", "luckyjoker.example")
    k3 = a.group_key("Jugá en Lucky Joker: 500% de bono + 250 giros gratis", "other.example")
    assert k1 == k2 != k3


def test_jaccard():
    assert a.jaccard("bitcoin trading plattform", "bitcoin trading plattform") == 1.0
    assert a.jaccard("bitcoin trading", "crema colágeno") == 0.0
