"""Pruebas de integración contra Postgres real.

Requieren TEST_DATABASE_URL apuntando a una base de datos DEDICADA a pruebas: se
reconstruye el esquema con las migraciones y se vacían las tablas entre pruebas.
Sin esa variable, las pruebas se omiten (en CI siempre está definida).
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from alembic import command
from app.core.config import get_settings
from app.core.db import get_db
from app.main import app
from app.modules.users.models import User
from app.scripts.seed_dev_user import seed_dev_user

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
ROOT = Path(__file__).resolve().parents[2]


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    here = Path(__file__).parent
    for item in items:
        if here in Path(item.fspath).parents:
            item.add_marker(pytest.mark.integration)
            if not TEST_DATABASE_URL:
                item.add_marker(pytest.mark.skip(reason="TEST_DATABASE_URL no está definida"))


def alembic_config(url: str) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    config.attributes["configure_logger"] = False
    return config


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    assert TEST_DATABASE_URL
    if TEST_DATABASE_URL == get_settings().database_url:
        pytest.exit("TEST_DATABASE_URL no puede ser la base de datos de la aplicación", 2)
    config = alembic_config(TEST_DATABASE_URL)
    # Reconstruir desde cero también prueba que downgrade y upgrade funcionan.
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE routes, users CASCADE"))
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def api(session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def dev_user(session_factory: sessionmaker[Session]) -> User:
    with session_factory() as session:
        return seed_dev_user(session)
