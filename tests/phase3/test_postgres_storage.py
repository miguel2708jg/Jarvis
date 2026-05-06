"""PostgreSQL storage selection and SQL behavior."""


def test_storage_factory_uses_sqlite_without_database_url(monkeypatch):
    from backend.storage import factory

    monkeypatch.setattr(factory.settings, "database_url", None, raising=False)

    class FakeSQLiteStore:
        def __init__(self, table_name, schema):
            self.table_name = table_name
            self.schema = schema

    class FakePostgresStore:
        def __init__(self, table_name, schema):
            raise AssertionError("Postgres should not be selected")

    monkeypatch.setattr(factory, "SQLiteStore", FakeSQLiteStore)
    monkeypatch.setattr(factory, "PostgresStore", FakePostgresStore)

    store = factory.create_store("samples", "CREATE TABLE samples (id TEXT PRIMARY KEY)")

    assert isinstance(store, FakeSQLiteStore)
    assert store.table_name == "samples"


def test_storage_factory_uses_postgres_with_database_url(monkeypatch):
    from backend.storage import factory

    monkeypatch.setattr(
        factory.settings,
        "database_url",
        "postgresql://user:pass@example.test/db?sslmode=require",
        raising=False,
    )

    class FakeSQLiteStore:
        def __init__(self, table_name, schema):
            raise AssertionError("SQLite should not be selected")

    class FakePostgresStore:
        def __init__(self, table_name, schema):
            self.table_name = table_name
            self.schema = schema

    monkeypatch.setattr(factory, "SQLiteStore", FakeSQLiteStore)
    monkeypatch.setattr(factory, "PostgresStore", FakePostgresStore)

    store = factory.create_store("samples", "CREATE TABLE samples (id TEXT PRIMARY KEY)")

    assert isinstance(store, FakePostgresStore)
    assert store.table_name == "samples"


def test_postgres_store_upsert_and_placeholder_conversion():
    from backend.storage.postgres_store import PostgresStore

    class FakeCursor:
        rowcount = 1

        def fetchone(self):
            return {"id": "sample-1", "value": "stored"}

        def fetchall(self):
            return [{"id": "sample-1", "value": "stored"}]

    class FakeConnection:
        def __init__(self):
            self.calls = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, sql, params=None):
            self.calls.append((sql, params))
            return FakeCursor()

    connection = FakeConnection()
    store = PostgresStore(
        "samples",
        "CREATE TABLE IF NOT EXISTS samples (id TEXT PRIMARY KEY, value TEXT NOT NULL)",
        database_url="postgresql://example/db",
        connect=lambda _url: connection,
    )

    store.set("sample-1", {"id": "sample-1", "value": "stored"})
    store.get("sample-1")
    store.all()
    store.query("value = ? ORDER BY id", ("stored",))
    assert store.delete("sample-1") is True

    sql_statements = [sql for sql, _params in connection.calls]
    assert any("ON CONFLICT (id) DO UPDATE SET value = EXCLUDED.value" in sql for sql in sql_statements)
    assert any("WHERE value = %s ORDER BY id" in sql for sql in sql_statements)
    assert not any("?" in sql for sql in sql_statements)
