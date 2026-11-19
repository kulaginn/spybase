import pytest

from spybase import collector, db


@pytest.fixture
def con(tmp_path):
    c = db.connect(tmp_path / "test.db")
    yield c
    c.close()


@pytest.fixture
def filled(con):
    collector.collect(con, collector.load_json("data/demo_ads.json"))
    return con
