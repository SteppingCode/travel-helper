import sqlite3
from io import BytesIO
from pathlib import Path
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from starlette.responses import StreamingResponse
from database.database import Database, initialize_database
from utils import get_db, check_image_exists, get_entity_from_db
from fastapi import FastAPI, Form, Request, UploadFile, File, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models import *
import os

app = FastAPI()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def startup_event():
    initialize_database()


@app.get("/", response_class=HTMLResponse, tags=["Public"])
async def read_root(request: Request):
    trips = get_entity_from_db("trips")
    return templates.TemplateResponse(request=request, name="index.html", context={"trips": trips})


@app.get("/places", response_class=HTMLResponse, tags=["Public"])
async def places(request: Request, q: Optional[str] = None, db: Database = Depends(get_db)):
    places = get_entity_from_db("places")
    filtered_places = places
    if q and q.strip():  # Защита от пустой строки
        q_lower = q.lower().strip()
        filtered_places = [
            place for place in places
            if (q_lower in place.get("city", "").lower() or
                q_lower in place.get("country", "").lower() or
                q_lower in place.get("descriptions", "").lower() or
                q_lower in str(place.get("tags", "")).lower())
        ]

    return templates.TemplateResponse(
        request=request,
        name="places.html",
        context={"places": filtered_places, "query": q or ""}
    )


@app.get("/place/{place_id}", tags=["Public"])
async def get_place(request: Request, place_id: int, db: Database = Depends(get_db)):
    place = db.select("places", where="id = ?", params=(place_id,), fetch_one=True)
    place = dict(place)
    place["has_image"] = check_image_exists("place", place["id"])
    return templates.TemplateResponse(request=request, name="place_page.html", context={"place": place})


@app.get("/get_image/{entity_type}/{entity_id}")
async def get_image(entity_type: str, entity_id: int, db: Database = Depends(get_db)) -> StreamingResponse:
    """Getting entity's image"""
    result = check_image_exists(entity_type, entity_id)

    if not result:
        raise HTTPException(status_code=404)

    image_path = result["file_path"]
    mimetype = result["mime_type"]

    with open(os.path.join(UPLOAD_DIR, image_path), "rb") as image_file:
        data = image_file.read()

    return StreamingResponse(BytesIO(data), media_type=mimetype)


@app.get("/mytrips", response_class=HTMLResponse, tags=["Auth"])
async def read_my_trips(request: Request):
    trips = get_entity_from_db("trips")
    return templates.TemplateResponse(request=request, name="trips.html", context={"trips": trips})


@app.get("/trip/{trip_id}", tags=["Auth"])
async def get_trip(request: Request, trip_id: int, db: Database = Depends(get_db)):
    trip = db.select("trips", where="id = ?", params=(trip_id,))
    return templates.TemplateResponse(request=request, name="trip_page.html", context={"trip": trip})


@app.get("/create", response_class=HTMLResponse, tags=["Public"])
async def create_page(request: Request):
    return templates.TemplateResponse(request=request, name="create_trip.html")


@app.post("/create_trip", tags=["Auth"])
async def create_trip(
        request: Request,
        trip_name: str = Form(...),
        trip_date: str = Form(...),
        destination: str = Form(...),
        budget: Optional[float] = Form(None),
        db: Database = Depends(get_db)
):
    """
    СОЗДАНИЕ ПУТЕШЕСТВИЯ
    """
    try:
        trip = Trip(name=trip_name, city=destination, country="TEST", date_from=trip_date.isoformat(),
                    date_to="2999-01-01", user_id=1)
        db.add("trips", trip.model_dump())
    except sqlite3.Error as err:
        print(err)
    return RedirectResponse(url="/details", status_code=303)



@app.get("/profile", tags=["Auth"])
async def profile_page(request: Request, db: Database = Depends(get_db)):
    user = db.select("users")
    return templates.TemplateResponse(request=request, name="profile.html", context={"user": user})


@app.get("/budget", tags=["Auth"])
async def budget_page(request: Request, db: Database = Depends(get_db)):
    return templates.TemplateResponse(request=request, name="budget.html")


@app.get("/checklists", tags=["Auth"])
async def checklists(request: Request, db: Database = Depends(get_db)):
    checklists = {
        'Документы и бронирования': [
            {'text': 'Проверить паспорт и визу', 'done': False, 'user_data': ''},
            {'text': 'Купить авиабилеты', 'done': False, 'user_data': ''},
            {'text': 'Забронировать отель', 'done': False, 'user_data': ''},
            {'text': 'Зарегистрироваться на рейс онлайн', 'done': False, 'user_data': ''},
            {'text': 'Распечатать посадочные талоны', 'done': False, 'user_data': ''},
            {'text': 'Проверить ограничения по багажу', 'done': False, 'user_data': ''}
        ],
        'Аптечка и здоровье': [
            {'text': 'Аптечка первой помощи', 'done': False, 'user_data': ''},
            {'text': 'Лекарства по рецепту', 'done': False, 'user_data': ''},
            {'text': 'Обезболивающие', 'done': False, 'user_data': ''},
            {'text': 'Средства от аллергии', 'done': False, 'user_data': ''}
        ],
        'Защита и гигиена': [
            {'text': 'Солнцезащитный крем', 'done': False, 'user_data': ''},
            {'text': 'Репелленты от насекомых', 'done': False, 'user_data': ''},
            {'text': 'Одежда по погоде', 'done': False, 'user_data': ''},
            {'text': 'Удобная обувь', 'done': False, 'user_data': ''},
            {'text': 'Туалетные принадлежности', 'done': False, 'user_data': ''}
        ],
        'Техника и зарядка': [
            {'text': 'Зарядные устройства', 'done': False, 'user_data': ''},
            {'text': 'Адаптеры для розеток', 'done': False, 'user_data': ''},
            {'text': 'Фотоаппарат или камера', 'done': False, 'user_data': ''}
        ],
        'Важные документы (с собой)': [
            {'text': 'Паспорт', 'done': False, 'user_data': ''},
            {'text': 'Виза или разрешение на въезд', 'done': False, 'user_data': ''},
            {'text': 'Копии документов', 'done': False, 'user_data': ''},
            {'text': 'Страховой полис', 'done': False, 'user_data': ''},
            {'text': 'Водительские права', 'done': False, 'user_data': ''},
            {'text': 'Бронь отеля', 'done': False, 'user_data': ''}
        ],
        'Перед выходом из дома': [
            {'text': 'Выключить электроприборы', 'done': False, 'user_data': ''},
            {'text': 'Закрыть окна и двери', 'done': False, 'user_data': ''},
            {'text': 'Полить растения', 'done': False, 'user_data': ''},
            {'text': 'Организовать уход за питомцами', 'done': False, 'user_data': ''},
            {'text': 'Перенаправить почту', 'done': False, 'user_data': ''},
            {'text': 'Проверить замки', 'done': False, 'user_data': ''}
        ]
    }
    return templates.TemplateResponse(request=request, name="checklists.html", context={"checklists": checklists})


@app.get("/test/{id}")
async def test(request: Request, id: int = 0, db: Database = Depends(get_db)):
    dir = "templates"
    list_of_files = os.listdir(dir)
    places = db.select("places")
    trips = db.select("trips")
    user = db.select("users", where="id = 1")
    checklists = {
        'Документы и бронирования': [
            {'text': 'Проверить паспорт и визу', 'done': False, 'user_data': ''},
            {'text': 'Купить авиабилеты', 'done': False, 'user_data': ''},
            {'text': 'Забронировать отель', 'done': False, 'user_data': ''},
            {'text': 'Зарегистрироваться на рейс онлайн', 'done': False, 'user_data': ''},
            {'text': 'Распечатать посадочные талоны', 'done': False, 'user_data': ''},
            {'text': 'Проверить ограничения по багажу', 'done': False, 'user_data': ''}
        ],
        'Аптечка и здоровье': [
            {'text': 'Аптечка первой помощи', 'done': False, 'user_data': ''},
            {'text': 'Лекарства по рецепту', 'done': False, 'user_data': ''},
            {'text': 'Обезболивающие', 'done': False, 'user_data': ''},
            {'text': 'Средства от аллергии', 'done': False, 'user_data': ''}
        ],
        'Защита и гигиена': [
            {'text': 'Солнцезащитный крем', 'done': False, 'user_data': ''},
            {'text': 'Репелленты от насекомых', 'done': False, 'user_data': ''},
            {'text': 'Одежда по погоде', 'done': False, 'user_data': ''},
            {'text': 'Удобная обувь', 'done': False, 'user_data': ''},
            {'text': 'Туалетные принадлежности', 'done': False, 'user_data': ''}
        ],
        'Техника и зарядка': [
            {'text': 'Зарядные устройства', 'done': False, 'user_data': ''},
            {'text': 'Адаптеры для розеток', 'done': False, 'user_data': ''},
            {'text': 'Фотоаппарат или камера', 'done': False, 'user_data': ''}
        ],
        'Важные документы (с собой)': [
            {'text': 'Паспорт', 'done': False, 'user_data': ''},
            {'text': 'Виза или разрешение на въезд', 'done': False, 'user_data': ''},
            {'text': 'Копии документов', 'done': False, 'user_data': ''},
            {'text': 'Страховой полис', 'done': False, 'user_data': ''},
            {'text': 'Водительские права', 'done': False, 'user_data': ''},
            {'text': 'Бронь отеля', 'done': False, 'user_data': ''}
        ],
        'Перед выходом из дома': [
            {'text': 'Выключить электроприборы', 'done': False, 'user_data': ''},
            {'text': 'Закрыть окна и двери', 'done': False, 'user_data': ''},
            {'text': 'Полить растения', 'done': False, 'user_data': ''},
            {'text': 'Организовать уход за питомцами', 'done': False, 'user_data': ''},
            {'text': 'Перенаправить почту', 'done': False, 'user_data': ''},
            {'text': 'Проверить замки', 'done': False, 'user_data': ''}
        ]
    }
    print(list_of_files[id])

    return templates.TemplateResponse(request=request, name=list_of_files[id],
                                      context={"places": places, "trips": trips, "checklists": checklists,
                                               "user": user})


@app.get("/reset", tags=["Auth"])
async def reset(request: Request, db: Database = Depends(get_db)):
    pass


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('static/favicon.ico')