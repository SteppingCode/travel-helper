from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import date
from typing import Optional
import sqlite3

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB_PATH = "travels.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_name TEXT NOT NULL,
                trip_date TEXT NOT NULL,
                destination TEXT NOT NULL,
                budget REAL
            )
        """)
        conn.commit()

init_db()


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