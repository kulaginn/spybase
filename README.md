# SpyBase — учебный прототип

SpyBase — веб-сервис для медиабайеров: база платных рекламных креативов с поиском по нише, стране и сроку показа.
Это учебный прототип MVP. В нём источник данных — демо-набор `data/demo_ads.json`
(вымышленные рекламодатели, домены `.example`). Через тот же интерфейс сборщика подключается реальный источник.

**Команда (РЭУ, 15.27Д-ИВТ02/24б):**

| Участник | Роль | Код в репозитории |
|---|---|---|
| Рязанцев Данил | тимлид, Backend & Data | `db.py`, `models.py`, `collector.py`, `repository.py`, `api.py`, CLI; тесты сборщика и поиска |
| Исматов Амир | Data Analyst / AI-ML | `classifier.py` (ниши, FR-14), `analytics.py` (срок показа, группы похожих, FR-03); их тесты |
| Саргсян Лион | Frontend & QA | `web/` (интерфейс), `errors.py` (ошибки), тесты API и ошибок, CI, pre-commit |

## Архитектура

```
data/demo_ads.json ──► collector (нормализация, отбор только платной рекламы, дедупликация)
                           │  classifier → ниша + уверенность      analytics → ключ группы похожих
                           ▼
                        SQLite (в целевой версии PostgreSQL): ads, advertisers, niches, users, favorites, collect_log
                           ▲
                    repository (поиск с фильтрами, карточка, избранное)
                           ▲
                    api (FastAPI, REST, единый формат ошибок)  ◄──  web (HTML/JS, только через API)
```

## Запуск

```bash
python -m venv .venv && . .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m spybase collect data/demo_ads.json      # загрузить демо-объявления в базу
uvicorn spybase.api:app --reload                  # http://127.0.0.1:8000 — интерфейс, /docs — Swagger
```

## Проверки

```bash
ruff check .      # стиль, типовые ошибки, правила безопасности (S)
mypy              # статическая проверка типов
bandit -r spybase -c pyproject.toml
pytest -q         # модульные и интеграционные тесты
```

Все проверки автоматически запускаются в GitHub Actions на каждый push (`.github/workflows/ci.yml`),
а локально — перед коммитом через pre-commit. Подробнее в [docs/STATIC_TESTING.md](docs/STATIC_TESTING.md).
Как в проекте использовался ИИ — [docs/AI_USAGE.md](docs/AI_USAGE.md).

## API

| Метод | Путь | Что делает |
|---|---|---|
| GET | `/api/ads?q=&country=&niche=&min_days=&sort=&limit=&offset=` | поиск с фильтрами |
| GET | `/api/ads/{id}` | карточка объявления + похожие |
| GET | `/api/niches`, `/api/stats` | справочник ниш, статистика базы |
| GET/POST/DELETE | `/api/favorites[/{id}]` (заголовок `X-User`) | избранное пользователя |

Коды ошибок описаны в [docs/ERRORS.md](docs/ERRORS.md).
