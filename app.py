from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, date
from typing import Optional
import sqlite3

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB_PATH = "travels.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_name TEXT NOT NULL,
                trip_date TEXT NOT NULL,
                destination TEXT NOT NULL,
                budget REAL,
                trip_image TEXT
                     )
                     """)
        conn.execute("""
CREATE TABLE IF NOT EXISTS places (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL,
                place_name TEXT NOT NULL,
                FOREIGN KEY (trip_id) REFERENCES trips (id) ON DELETE CASCADE
                         )
                     """)
        conn.execute("""
CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL,
                task_name TEXT NOT NULL,
                is_completed INTEGER DEFAULT 0,
                FOREIGN KEY (trip_id) REFERENCES trips (id) ON DELETE CASCADE
                         )
                     """)
        conn.execute("""
CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL,
                member_name TEXT NOT NULL,
                FOREIGN KEY (trip_id) REFERENCES trips (id) ON DELETE CASCADE
                         )
                     """)


init_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return RedirectResponse(url="/details", status_code=303)


@app.get("/create", response_class=HTMLResponse)
def create_page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/create_route")
def create_route(
        request: Request,
        trip_name: str = Form(...),
        trip_date: date = Form(...),
        destination: str = Form(...),
        budget: Optional[float] = Form(None),
        image_base64: Optional[str] = Form(None)
):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO trips (trip_name, trip_date, destination, budget, trip_image) VALUES (?, ?, ?, ?, ?)",
            (trip_name, str(trip_date), destination, budget, image_base64 if image_base64 else None)
        )
        conn.commit()

    return RedirectResponse(url="/details", status_code=303)


@app.get("/details", response_class=HTMLResponse)
def details(request: Request):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trips ORDER BY id DESC")
        trips = [dict(row) for row in cursor.fetchall()]

    nearest_trip = None
    today = date.today()
    min_days_left = float('inf')

    for trip in trips:
        if trip.get("trip_date"):
            try:
                date_str = trip["trip_date"].split()[0]
                t_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                if t_date >= today:
                    days_left = (t_date - today).days
                    if days_left < min_days_left:
                        min_days_left = days_left
                        nearest_trip = trip
                        nearest_trip["days_left"] = days_left
                        nearest_trip["formatted_date"] = t_date.strftime("%d.%m.%Y")
            except Exception:
                continue

    if not nearest_trip and trips:
        nearest_trip = trips[0]
        try:
            t_date = datetime.strptime(nearest_trip["trip_date"].split()[0], "%Y-%m-%d").date()
            nearest_trip["formatted_date"] = t_date.strftime("%d.%m.%Y")
        except Exception:
            nearest_trip["formatted_date"] = nearest_trip["trip_date"]
        nearest_trip["days_left"] = None

    if nearest_trip:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            nearest_trip["places_count"] = \
            cursor.execute("SELECT COUNT(*) FROM places WHERE trip_id = ?", (nearest_trip["id"],)).fetchone()[0]
            nearest_trip["tasks_count"] = \
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE trip_id = ?", (nearest_trip["id"],)).fetchone()[0]
            nearest_trip["members_count"] = \
            cursor.execute("SELECT COUNT(*) FROM members WHERE trip_id = ?", (nearest_trip["id"],)).fetchone()[0] + 1

    return templates.TemplateResponse(
        request=request,
        name="details.html",
        context={"trips": trips, "nearest_trip": nearest_trip}
    )

@app.get("/api/trip/{trip_id}/data")
def get_trip_data(trip_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        places = [dict(r) for r in cursor.execute("SELECT * FROM places WHERE trip_id = ?", (trip_id,)).fetchall()]
        tasks = [dict(r) for r in cursor.execute("SELECT * FROM tasks WHERE trip_id = ?", (trip_id,)).fetchall()]
        members = [dict(r) for r in cursor.execute("SELECT * FROM members WHERE trip_id = ?", (trip_id,)).fetchall()]

        return {"places": places, "tasks": tasks, "members": members}


@app.post("/api/trip/{trip_id}/add_item")
async def add_item(trip_id: int, request: Request):
    data = await request.json()
    item_type = data.get("type")
    value = data.get("value")

    if not value or not item_type:
        raise HTTPException(status_code=400, detail="Invalid data")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if item_type == "place":
            cursor.execute("INSERT INTO places (trip_id, place_name) VALUES (?, ?)", (trip_id, value))
        elif item_type == "task":
            cursor.execute("INSERT INTO tasks (trip_id, task_name) VALUES (?, 0)", (trip_id, value))
        elif item_type == "member":
            cursor.execute("INSERT INTO members (trip_id, member_name) VALUES (?, ?)", (trip_id, value))
        conn.commit()
        return {"status": "success"}


@app.delete("/api/trip/delete_item/{item_type}/{item_id}")
def delete_item(item_type: str, item_id: int):
    if item_type not in ["place", "task", "member"]:
        raise HTTPException(status_code=400, detail="Invalid item type")

    table_map = {"place": "places", "task": "tasks", "member": "members"}
    table_name = table_map[item_type]

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"DELETE FROM {table_name} WHERE id = ?", (item_id,))
        conn.commit()
        return {"status": "success"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)