"""Compartir ubicación (SCRUM-25) contra Postgres: migración 0010 y cascada."""

from sqlalchemy import inspect


def test_migration_creates_the_table(engine):
    inspector = inspect(engine)

    assert "location_shares" in inspector.get_table_names()
    uniques = {
        tuple(u["column_names"]) for u in inspector.get_unique_constraints("location_shares")
    }
    assert ("token_hash",) in uniques
    assert inspector.get_foreign_keys("location_shares")[0]["options"].get("ondelete") == "CASCADE"
