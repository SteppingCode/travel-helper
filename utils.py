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


def get_entity_from_db(table_name: str) -> list | None:
    db = Database()
    entity = db.select(table_name)

    entity_list = []
    for e in entity:
        e_dict = dict(e)  # Convert sqlite3.Row to dict
        e_dict["has_image"] = check_image_exists(table_name[0:-1], e["id"])
        entity_list.append(e_dict)

    return entity_list