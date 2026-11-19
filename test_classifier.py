"""Тесты классификатора ниш (Исматов А.)."""

import pytest

from spybase.classifier import classify


@pytest.mark.parametrize("text, domain, niche", [
    ("Jugá: 500% de bono + 250 giros gratis en tu primer depósito", "", "gambling"),
    ("Kasyno Plus: 200% bonusu i 100 free spins", "", "gambling"),
    ("Krypto investieren mit KI: Bitcoin Trading Plattform", "", "invest"),
    ("Inwestycje z AI: pasywny dochód, trading", "", "invest"),
    ("Black Friday: 40% Rabatt, kostenloser Versand", "", "ecom"),
    ("Crema de colágeno para piel firme", "", "nutra"),
    ("Nuevo modelo", "superbet-promo.example", "gambling"),
])
def test_classify(text, domain, niche):
    code, score = classify(text, domain)
    assert code == niche
    assert 0 < score <= 1


def test_unknown_is_other():
    assert classify("mi gato bailando en la cocina") == ("other", 0.0)
    assert classify("") == ("other", 0.0)


def test_word_boundaries():
    # «bet» внутри слова «alphabet» не должен давать гемблу
    assert classify("Learn the alphabet with us")[0] == "other"
