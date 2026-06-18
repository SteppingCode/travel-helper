from io import BytesIO
from fastapi import HTTPException, Depends, Response
from starlette.responses import StreamingResponse
from database.database import Database


def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()


