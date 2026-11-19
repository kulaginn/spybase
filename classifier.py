"""Определение ниши объявления (Исматов А., FR-14 «Классификатор ниш», решение 5).

Подход MVP — взвешенный словарь ключевых слов на языках стран сбора + признаки домена лендинга.
Каждое совпадение даёт вес; ниша с наибольшей суммой побеждает, если набрала порог.
Уверенность (score) — доля веса победившей ниши от суммы всех весов, 0..1.
В плане развития словарь заменяется ML-классификатором с тем же интерфейсом classify().
"""

from __future__ import annotations

import re
import unicodedata

# ниша → {ключевое слово/фраза: вес}
KEYWORDS: dict[str, dict[str, float]] = {
    "gambling": {
        "casino": 3, "casinò": 3, "kasyno": 3, "slot": 2, "slots": 2, "jackpot": 2, "freespin": 3,
        "free spins": 3, "giros gratis": 3, "fs": 1, "bono": 1.5, "bonus": 1, "apuesta": 2, "apuestas": 2,
        "bet": 1.5, "jugar": 1, "spin": 1, "ruleta": 2, "aviator": 3, "zakłady": 2, "wygraj": 1.5,
        "scommesse": 2, "sportwetten": 2, "depósito": 1.5, "deposit": 1.5,
    },
    "invest": {
        "invest": 2, "inversión": 2, "inwestycje": 2, "investire": 2, "investieren": 2, "trading": 2,
        "bitcoin": 2.5, "crypto": 2, "krypto": 2, "cripto": 2, "forex": 2.5, "acciones": 1.5, "akcje": 1.5,
        "dividend": 1.5, "rendimiento": 1.5, "pasywny dochód": 2, "ingresos pasivos": 2, "ganancia": 1,
        "broker": 2, "staking": 2, "etf": 1.5,
    },
    "ecom": {
        "envío gratis": 2.5, "envíos gratis": 2.5, "darmowa dostawa": 2.5, "spedizione gratuita": 2.5,
        "kostenloser versand": 2.5, "free shipping": 2.5, "descuento": 1.5, "rabat": 1.5, "sconto": 1.5,
        "rabatt": 1.5, "oferta": 1, "comprar": 1, "kup teraz": 1.5, "acquista": 1, "shop": 1,
        "black friday": 2, "stock": 1, "garantía": 1,
    },
    "nutra": {
        "crema": 1.5, "piel": 1.5, "skin": 1.5, "suplemento": 2.5, "suplement": 2.5, "integratore": 2.5,
        "vitamin": 2, "vitaminas": 2, "adelgazar": 3, "odchudzanie": 3, "dimagrire": 3, "abnehmen": 3,
        "colágeno": 2.5, "articulaciones": 2.5, "presión": 2, "dieta": 1.5,
    },
}

DOMAIN_HINTS: dict[str, tuple[str, ...]] = {
    "gambling": ("casino", "bet", "slot", "spin", "jackpot", "apuesta"),
    "invest": ("invest", "trade", "crypto", "broker", "capital", "finance"),
    "ecom": ("shop", "store", "tienda", "market", "outlet"),
    "nutra": ("health", "salud", "vita", "derma", "slim"),
}
DOMAIN_WEIGHT = 2.0
THRESHOLD = 2.0


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "").lower()
    return re.sub(r"\s+", " ", text)


def _count(text: str, phrase: str) -> int:
    return len(re.findall(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text))


def scores(caption: str, domain: str = "") -> dict[str, float]:
    """Сумма весов по каждой нише."""
    text, dom = _norm(caption), _norm(domain)
    out: dict[str, float] = {}
    for niche, words in KEYWORDS.items():
        s = sum(w * min(_count(text, kw), 3) for kw, w in words.items())
        if dom and any(h in dom for h in DOMAIN_HINTS.get(niche, ())):
            s += DOMAIN_WEIGHT
        if s:
            out[niche] = s
    return out


def classify(caption: str, domain: str = "") -> tuple[str, float]:
    """Возвращает (код ниши, уверенность 0..1). Если признаков мало — ('other', 0.0)."""
    sc = scores(caption, domain)
    if not sc:
        return "other", 0.0
    best = max(sc, key=lambda k: sc[k])
    if sc[best] < THRESHOLD:
        return "other", 0.0
    return best, round(sc[best] / sum(sc.values()), 2)
