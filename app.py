import sqlite3
from io import BytesIO
from pathlib import Path
from uvicorn import run
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from starlette.responses import StreamingResponse
from database.database import Database, initialize_database
from utils import get_db
from fastapi import FastAPI, Form, Request, UploadFile, File, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import date, datetime
from models import *

app = FastAPI()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def startup_event():
    initialize_database()


# @app.post("/upload_trip/")
# async def upload_trip(preview: UploadFile = File(...), db: Database = Depends(get_db)):
#     """Upload image and store as BLOB"""
#     if not preview.content_type.startswith("image/"):
#         raise HTTPException(400, detail="Only image files allowed")
#
#     contents = await preview.read()
#
#
#     return RedirectResponse(url="/", status_code=302)

# ===EXAMPLE===
@app.post("/upload")
async def upload_file(image: UploadFile = File(...)):
    print("UPLOAD FILE")
    file_path = UPLOAD_DIR / image.filename

    # Save the file
    with open(file_path, "wb") as f:
        contents = await image.read()
        f.write(contents)

    return {"filename": image.filename}


# TODO: Вынести вспомогательные функции в отдельный модуль
@app.get("/{entity_type}/{image_id}")
async def get_image(entity_type: str, image_id: int, db: Database = Depends(get_db)) -> StreamingResponse:
    """Getting entity's image"""
    result = db.execute(
        sql=f"select * from images i inner join images_links il on i.id = il.image_id where il.entity_type = {entity_type} and il.image_id = {image_id}").fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Image not found")

    image_path = result["file_path"]
    mimetype = result["mime_type"]

    with open(image_path, "rb") as image_file:
        data = image_file.read()

    return StreamingResponse(BytesIO(data), media_type=mimetype)


@app.get("/", response_class=HTMLResponse, tags=["Public"])
async def read_root(request: Request, db: Database = Depends(get_db)):
    trips = db.select("trips")
    return templates.TemplateResponse(request=request, name="index.html", context={"trips": trips})


@app.get("/mytrips", response_class=HTMLResponse, tags=["Auth"])
async def read_my_trips(request: Request, db: Database = Depends(get_db)):
    trips = db.select("trips")
    return templates.TemplateResponse(request=request, name="trips.html", context={"trips": trips})


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('static/favicon.ico')


@app.get("/create", response_class=HTMLResponse, tags=["Public"])
async def create_page(request: Request):
    return templates.TemplateResponse(request=request, name="create_trip.html")


@app.post("/create_route", tags=["Auth"])
async def create_route(
        request: Request,
        trip_name: str = Form(...),
        trip_date: date = Form(...),
        destination: str = Form(...),
        budget: Optional[float] = Form(None),
        db: Database = Depends(get_db)
):
    """
    СОЗДАНИЕ ПУТЕШЕСТВИЯ
    """
    try:
        time_created = datetime.now()
        db.add("trips", {"name": trip_name, "city": destination, "country": "TEST", "date_from": trip_date,
                         "date_to": "2999-01-01", "created_at": time_created, "user_id": 1})

    except sqlite3.Error as err:
        print(err)
    return RedirectResponse(url="/details", status_code=303)


@app.get("/details", response_class=HTMLResponse, tags=["Auth"])
async def details(request: Request, db: Database = Depends(get_db)):
    trips = db.select("trips")

    return templates.TemplateResponse(
        request=request,
        name="details.html",
        context={"trips": trips}
    )


@app.get("/places", response_class=HTMLResponse, tags=["Public"])
async def places(request: Request, q: Optional[str] = None, db: Database = Depends(get_db)):
    # TODO: Починить страницу
    places = db.select("places")
    filtered_places = places

    if q and q.strip():  # Защита от пустой строки
        q_lower = q.lower().strip()
        filtered_places = [
            place for place in places
            if (q_lower in place.get("name", "").lower() or
                q_lower in place.get("country", "").lower() or
                q_lower in place.get("description", "").lower() or
                any(q_lower in tag.lower() for tag in place.get("tags", [])))
        ]

    return templates.TemplateResponse(request=request, name="places.html",
                                      context={"places": filtered_places, "query": q or ""})


@app.get("/trip/{trip_id}", tags=["Auth"])
async def get_trip(request: Request, trip_id: int, db: Database = Depends(get_db)):
    pass


@app.get("/budget", tags=["Auth"])
async def budget_page(request: Request, db: Database = Depends(get_db)):
    return templates.TemplateResponse(request=request, name="budget.html")


if __name__ == '__main__':
    run(app, host="0.0.0.0", port=8000, reload=True)
