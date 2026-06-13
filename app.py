import io

from pathlib import Path
from uvicorn import run
from fastapi import Depends, FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database.database import Database, initialize_database
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import date
from typing import Optional
import sqlite3

app = FastAPI()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()


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


@app.get("/{entity_type}/{image_id}")
async def get_image(entity_type: str, image_id: int, db: Database = Depends(get_db)):
    """Getting entity's image"""
    result = db.execute(
        sql=f"select * from images i inner join image_links il on i.id = il.image_id where il.entity_type = {entity_type} and il.image_id = {image_id}",
        params=("fetchone",))

# TODO: Ask ChatGPT How to make that when I add for example some post with image automatically adds a row in image_link and images tables?

    if not result:
        raise HTTPException(status_code=404, detail="Image not found")

    image_path = result["file_path"]
    mimetype = result["mime_type"]

    with open(image_path, "rb") as image_file:
        data = image_file.read()

    return StreamingResponse(io.BytesIO(data), media_type=mimetype)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Database = Depends(get_db)):
    trips = db.select("trips")
    return templates.TemplateResponse(request=request, name="index.html", context={"trips": trips})


@app.get("/mytrips", response_class=HTMLResponse)
async def read_my_trips(request: Request, db: Database = Depends(get_db)):
    trips = db.select("trips")
    return templates.TemplateResponse(request=request, name="mytrips.html", context={"trips": trips})


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('static/favicon.ico')


if __name__ == '__main__':
    run(app, host="0.0.0.0", port=8000, reload=True)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return RedirectResponse(url="/details", status_code=303)


@app.get("/create", response_class=HTMLResponse)
async def create_page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/create_route")
async def create_route(
        request: Request,
        trip_name: str = Form(...),
        trip_date: date = Form(...),
        destination: str = Form(...),
        budget: Optional[float] = Form(None)
):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO trips (trip_name, trip_date, destination, budget) VALUES (?, ?, ?, ?)",
            (trip_name, str(trip_date), destination, budget)
        )
        conn.commit()

    return RedirectResponse(url="/details", status_code=303)


@app.get("/details", response_class=HTMLResponse)
async def details(request: Request):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trips ORDER BY id DESC")
        trips = cursor.fetchall()

    return templates.TemplateResponse(
        request=request,
        name="details.html",
        context={"trips": trips}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)