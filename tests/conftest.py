"""Never let tests clear or alter the user's application database."""
import os
import tempfile

_database_dir = tempfile.TemporaryDirectory(prefix="arteria-tests-")
os.environ["ARTERIA_DB_PATH"] = os.path.join(_database_dir.name, "test.sqlite3")
