import glob
import os.path
import sqlite3
from datetime import datetime
from os import makedirs, path

from models import *

"""
checklists
"""

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
        fetch_one: bool = False,
    ):
        """Select rows from a table."""
        sql = f"SELECT {columns} FROM {table}"
        if where:
            sql += f" WHERE {where}"
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
        for sql_file in sorted(glob.glob(sql_path)):
            with open(sql_file, "r", encoding="utf-8") as file:
                connection.executescript(file.read())
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    from PIL.Image import open
    db = Database()

    # trip1 = Trip(name="Отдых в Сочи", city="Сочи", country="Россия", date_from="2026-06-21", date_to="2020-09-21", user_id=1)
    # db.add("trips", trip1.model_dump())
    #
    # trip2 = Trip(name="Поездка в Японию", city="Токио", country="Япония", date_from="2026-12-31", date_to="2027-02-09", user_id=1)
    # db.add("trips", trip2.model_dump())
    #
    # trip3 = Trip(name="Поездка в Японию", city="Токио", country="Япония", date_from="2026-12-31", date_to="2027-02-09", user_id=2)
    # db.add("trips", trip3.model_dump())

    # place1 = Place(city="Санкт-Петербург", country="Россия", rating=5.0, description="Санкт-Петербу́рг — второй по численности населения город России. Город федерального значения. Административный центр Северо-Западного федерального округа. Основан 16 мая 1703 года царём Петром I. В 1714—1728 и 1732—1918 годах был столицей Российского государства.")
    # db.add("places", place1.model_dump())
    #
    # place2 = Place(city="Москва", country="Россия", rating=4.9, description="Москва́ — столица России, город федерального значения, административный центр Центрального федерального округа и центр Московской области, в состав которой не входит. Мегаполис; крупнейший по численности населения город России и её субъект — 13 274 285 человек, что делает Москву 22-й среди городов мира по численности населения. Центр Московской городской агломерации.")
    # db.add("places", place2.model_dump())
    #
    # images = ["sochi.jpg", "tokyo.jpg"]
    # for image in images:
    #     UPLOAD_DIR = "../uploads/"
    #     file_size = os.path.getsize(UPLOAD_DIR + image)
    #     width, height = open(UPLOAD_DIR + image).size
    #     image_type = open(UPLOAD_DIR + image).get_format_mimetype()
    #     image = Image(file_path=image, original_name=image, mime_type=image_type, file_size=file_size, width=width, height=height)
    #     db.add("images", image.model_dump())

    # db.add("images_links", {"image_id": 2, "entity_type": "trip", "entity_id": 3})
