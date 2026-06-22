import sqlite3
from datetime import datetime
from os import makedirs, path
from glob import glob


def conn_db(db_path: str | None = None) -> sqlite3.Connection:
    """Connect to an SQLite database file."""
    if db_path is None:
        base_dir = path.dirname(path.abspath(__file__))
        db_path = path.join(base_dir, "app.db")

    db_dir = path.dirname(db_path)
    if db_dir and not path.exists(db_dir):
        makedirs(db_dir, exist_ok=True)

    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def cursor_db(connection: sqlite3.Connection) -> sqlite3.Cursor:
    """Return a cursor for the given SQLite connection."""
    return connection.cursor()


class Database:
    """Lightweight SQLite database wrapper for basic CRUD operations."""
    def __init__(self, db_path: str | None = None):
        self.db = conn_db(db_path)
        self.cursor = cursor_db(self.db)


    def execute(self, sql: str, params: tuple | list | None = None, commit: bool = False):
        """Execute a SQL statement and optionally commit."""
        self.cursor.execute(sql, params or ())
        if commit:
            self.db.commit()
        return self.cursor


    def add(self, table: str, data: dict) -> int:
        """Insert a row into the specified table and return the last row id."""
        data.update({"created_at": datetime.now().isoformat()})
        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.cursor.execute(sql, tuple(data.values()))
        self.db.commit()
        return self.cursor.lastrowid # type: ignore


    def remove(self, table: str, where: str, params: tuple | list | None = None) -> int:
        """Delete rows matching the given WHERE clause."""
        sql = f"DELETE FROM {table} WHERE {where}"
        self.cursor.execute(sql, params or ())
        self.db.commit()
        return self.cursor.rowcount


    def update(self, table: str, data: dict, where: str, params: tuple | list | None = None) -> int:
        """Update rows in a table matching the WHERE clause."""
        set_clause = ", ".join(f"{column} = ?" for column in data.keys())
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        self.cursor.execute(sql, tuple(data.values()) + tuple(params or ()))
        self.db.commit()
        return self.cursor.rowcount


    def select(
            self,
            table: str,
            columns: str = "*",
            where: str | None = None,
            params: tuple | list | None = None,
            order_by: str | None = None,
            limit: int | None = None,
            fetch_one: bool = False,
    ):
        """Select rows from a table."""
        sql = f"SELECT {columns} FROM {table}"
        if where:
            sql += f" WHERE {where}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit:
            sql += f" LIMIT {limit}"

        self.cursor.execute(sql, params or ())
        return self.cursor.fetchone() if fetch_one else self.cursor.fetchall()


    def close(self):
        """Close the database connection."""
        self.db.close()


def initialize_database(db_path: str | None = None) -> None:
    """Create the database file and execute all SQL scripts in the sql folder."""
    connection = conn_db(db_path)
    try:
        base_dir = path.dirname(path.abspath(__file__))
        sql_path = path.join(base_dir, "sql", "*.sql")
        for sql_file in sorted(glob(sql_path)):
            with open(sql_file, "r", encoding="utf-8") as file:
                connection.executescript(file.read())
        connection.commit()
    finally:
        connection.close()