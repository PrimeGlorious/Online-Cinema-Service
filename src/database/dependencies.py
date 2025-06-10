import os

if os.getenv("ENVIRONMENT", "developing") == "testing":
    from database.session_sqlite import get_sqlite_db as get_db
else:
    from database.session_postgresql import get_postgresql_db as get_db
