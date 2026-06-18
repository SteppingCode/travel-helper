from io import BytesIO
from fastapi import HTTPException, Depends, Response
from starlette.responses import StreamingResponse
from sqlite3 import Row
from database.database import Database


def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()


def check_image_exists(entity_type: str, entity_id: int) -> Row | None:
    db = Database()
    result = db.execute(
        f"select * from images inner join images_links on images.id = images_links.image_id where entity_type = ? and entity_id = ?",
        (entity_type, entity_id)).fetchone()

    if not result:
        return None

    return result


def get_trips_from_db() -> list | None:
    db = Database()
    trips = db.select("trips")

    trips_list = []
    for trip in trips:
        trip_dict = dict(trip)  # Convert sqlite3.Row to dict
        trip_dict["has_image"] = check_image_exists("trip", trip["id"])
        trips_list.append(trip_dict)

    return trips_list