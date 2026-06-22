"""PostgreSQL storage selection and SQL behavior."""


def test_storage_factory_uses_sqlite_without_database_url(monkeypatch):
    from backend.storage import factory

    monkeypatch.setattr(factory.settings, "database_url", None, raising=False)
    monkeypatch.setattr(factory.settings, "allow_sqlite_fallback", True, raising=False)

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


def test_storage_factory_requires_database_url_without_explicit_sqlite_fallback(monkeypatch):
    from backend.storage import factory

    monkeypatch.setattr(factory.settings, "database_url", None, raising=False)
    monkeypatch.setattr(factory.settings, "allow_sqlite_fallback", False, raising=False)

    try:
        factory.create_store("samples", "CREATE TABLE samples (id TEXT PRIMARY KEY)")
    except RuntimeError as exc:
        assert "DATABASE_URL is required" in str(exc)
    else:
        raise AssertionError("Expected missing DATABASE_URL to fail without explicit SQLite fallback")


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


def test_postgres_store_reconnects_once_after_connection_error():
    import psycopg

    from backend.storage.postgres_store import PostgresStore

    class FakeCursor:
        def fetchone(self):
            return {"id": "sample-1", "value": "stored"}

    class BrokenConnection:
        closed = False

        def __init__(self):
            self.close_called = False

        def execute(self, sql, params=None):
            raise psycopg.OperationalError("SSL SYSCALL error")

        def close(self):
            self.close_called = True
            self.closed = True

    class WorkingConnection:
        closed = False

        def __init__(self):
            self.calls = []

        def execute(self, sql, params=None):
            self.calls.append((sql, params))
            return FakeCursor()

        def commit(self):
            pass

    broken = BrokenConnection()
    working = WorkingConnection()
    connections = [broken, working]

    store = PostgresStore(
        "samples",
        "CREATE TABLE IF NOT EXISTS samples (id TEXT PRIMARY KEY, value TEXT NOT NULL)",
        database_url="postgresql://example/db",
        connect=lambda _url: connections.pop(0),
    )

    assert store.get("sample-1") == {"id": "sample-1", "value": "stored"}
    assert broken.close_called is True
    assert any("SELECT * FROM samples WHERE id = %s" in sql for sql, _params in working.calls)
