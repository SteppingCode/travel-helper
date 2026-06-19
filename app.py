import sqlite3
from io import BytesIO
from pathlib import Path
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from starlette.responses import StreamingResponse
from database.database import Database, initialize_database
from utils import get_db, check_image_exists, get_entity_from_db, set_flash_message, render_template
from fastapi import FastAPI, Form, Request, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from models import *
from auth import get_password_hash, verify_password, create_access_token, get_current_user, timedelta, \
    ACCESS_TOKEN_EXPIRE_MINUTES, get_optional_user, decode_token
import os

app = FastAPI()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def startup_event():
    initialize_database()


@app.middleware("http")
async def add_user_to_request(request: Request, call_next):
    token = request.cookies.get("access_token")
    request.state.user = None

    if token:
        payload = decode_token(token)
        if payload:
            email = payload.get("sub")
            db = Database()
            user = db.select("users", where="email = ?", params=(email,), fetch_one=True)
            db.close()  # Обязательно закрываем

            if user:
                request.state.user = dict(user)

    response = await call_next(request)
    return response

@app.get("/", response_class=HTMLResponse, tags=["Public"])
async def read_root(request: Request,
                    db: Database = Depends(get_db),
                    user: dict | None = Depends(get_optional_user)):
    context = None
    if user:
        trips = db.select("trips", where="user_id = ?", params=(request.state.user["id"],))
        context = {"trips": trips}
    return render_template(request, "index.html", context)


@app.get("/places", response_class=HTMLResponse, tags=["Public"])
async def places(request: Request, q: Optional[str] = None, db: Database = Depends(get_db),
                 user: dict | None = Depends(get_optional_user)):
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

    return render_template(request, "places.html", {"places": filtered_places, "query": q})


@app.get("/place/{place_id}", tags=["Public"])
async def get_place(request: Request, place_id: int, db: Database = Depends(get_db),
                    user: dict | None = Depends(get_optional_user)):
    place = db.select("places", where="id = ?", params=(place_id,), fetch_one=True)
    place = dict(place)
    place["has_image"] = check_image_exists("place", place["id"])
    return render_template(request, "place_page.html", {"place": place})


@app.get("/get_image/{entity_type}/{entity_id}", tags=["Public"])
async def get_image(entity_type: str, entity_id: int, db: Database = Depends(get_db),
                    user: dict | None = Depends(get_optional_user)) -> StreamingResponse:
    """Getting entity's image"""
    result = check_image_exists(entity_type, entity_id)

    if not result:
        raise HTTPException(status_code=404)

    image_path = result["file_path"]
    mimetype = result["mime_type"]

    with open(os.path.join(UPLOAD_DIR, image_path), "rb") as image_file:
        data = image_file.read()

    return StreamingResponse(BytesIO(data), media_type=mimetype)

@app.get("/login", tags=["Public"])
async def login_redirect(request: Request):
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return set_flash_message(response, "warning", "Войдите в профиль для просмотра страницы")

@app.post("/login", tags=["Public"])
async def login(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        db: Database = Depends(get_db)
):
    referer = request.headers.get("referer", "/")
    user = db.select("users", where="email = ?", params=(email,), fetch_one=True)

    # ❌ ЕСЛИ ОШИБКА:
    if not user or not verify_password(password, user["hashed_password"]):
        response = RedirectResponse(url=referer, status_code=status.HTTP_303_SEE_OTHER)
        # Добавляем Toast с ошибкой
        return set_flash_message(response, "error", "Неверный email или пароль")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )

    # ✅ ЕСЛИ УСПЕХ:
    response = RedirectResponse(url=referer, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True, max_age=1800, samesite="lax"
    )
    # Добавляем Toast об успехе
    return set_flash_message(response, "success", f"С возвращением, {user['fullname']}!")


@app.get("/register", response_class=HTMLResponse, tags=["Public"])
async def register_page(
        request: Request,
        user: dict | None = Depends(get_optional_user)  # Keep the header working
):
    # If they are already logged in, no need to register
    if user:
        return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)

    # try:
    #     # CHECK EXISTING USER
    #     existing_user = False
    #     if existing_user:
    #         response = RedirectResponse(url="/register", status_code=status.HTTP_303_SEE_OTHER)
    #         return set_flash_message(response, "warning", "Пользователь с таким email уже существует")
    # else:
    #     response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    #     return set_flash_message(response, "success", "Успешная регистрация! Теперь вы можете войти.")
    # except sqlite3.Error as error:
    #     print(error)

    return render_template(request, "register.html")


@app.post("/register", tags=["Public"])
async def register(
        request: Request,
        fullname: str = Form(...),
        email: str = Form(...),
        phone: str = Form(...),
        country: str = Form(...),
        password: str = Form(...),
        db: Database = Depends(get_db)
):
    # Check if email already exists
    existing_user = db.select("users", where="email = ?", params=(email,), fetch_one=True)
    if existing_user:
        return render_template(request, "register.html", {"error": "Пользователь с таким email уже существует"})

    # Hash the password
    hashed_pw = get_password_hash(password)

    try:
        # Insert into database
        db.add("users", {
            "fullname": fullname,
            "email": email,
            "phone": phone,
            "country": country,
            "hashed_password": hashed_pw
        })
    except sqlite3.Error as err:
        print(f"Database Error: {err}")
        return render_template(request, "register.html", {"error": "Произошла ошибка при регистрации. Попробуйте позже."})

    # Registration successful! Redirect them to the homepage where they can use the dropdown to log in.
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/logout", tags=["Auth"])
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


@app.get("/mytrips", response_class=HTMLResponse, tags=["Auth"])
async def read_my_trips(
        request: Request,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)  # <-- This makes the route private
):
    # Now you can fetch trips specifically for the logged-in user!
    trips = db.select("trips", where="user_id = ?", params=(current_user["id"],))

    return render_template(request, "trips.html", {"trips": trips})


@app.get("/trip/{trip_id}", tags=["Auth"])
async def get_trip(request: Request, trip_id: int, db: Database = Depends(get_db),
                   current_user: dict = Depends(get_current_user)):
    trip = db.select("trips", where="id = ?", params=(trip_id,))
    return render_template(request, "trip_page.html", {"trip": trip})


@app.get("/create", response_class=HTMLResponse, tags=["Auth"])
async def create_page(request: Request, db: Database = Depends(get_db),
                      current_user: dict = Depends(get_current_user)):
    return render_template(request, "create_trip.html")


@app.post("/create_trip", tags=["Auth"])
async def create_trip(
        request: Request,
        trip_name: str = Form(...),
        trip_date: str = Form(...),
        destination: str = Form(...),
        budget: Optional[float] = Form(None),
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
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
async def profile_page(
        request: Request,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    return render_template(request, "profile.html")


@app.get("/budget", tags=["Auth"])
async def budget_page(request: Request, db: Database = Depends(get_db),
                      current_user: dict = Depends(get_current_user)):
    return render_template(request, "budget.html")


@app.get("/checklists", tags=["Auth"])
async def checklists(request: Request, db: Database = Depends(get_db),
                     current_user: dict = Depends(get_current_user)):
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
    return render_template(request, "checklists.html", {"checklists": checklists})


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
    return render_template(request, list_of_files[id], {"places": places, "trips": trips, "checklists": checklists})


@app.get("/reset", tags=["Auth"])
async def reset(request: Request, db: Database = Depends(get_db),
                current_user: dict = Depends(get_current_user)):
    pass


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('static/favicon.ico')
