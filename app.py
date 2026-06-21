from datetime import datetime
from sqlite3 import Error
from pathlib import Path
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from database.database import Database, initialize_database
from utils import get_db, get_entity_from_db, set_flash_message, render_template
from fastapi import FastAPI, Form, Request, HTTPException, Depends, status, UploadFile, File
from fastapi.staticfiles import StaticFiles
from models import *
from auth import get_password_hash, verify_password, create_access_token, get_current_user, timedelta, \
    ACCESS_TOKEN_EXPIRE_MINUTES, get_optional_user, decode_token, get_admin_user
from os import path
from typing import List, Optional
import shutil
import uuid

app = FastAPI()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


async def save_uploaded_photo(file: UploadFile, entity_type: str, entity_id: int, db: Database):
    if not file or not file.filename:
        return

    # Генерируем уникальное имя файла
    file_extension = path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    # Сохраняем физически на диск
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # В реальном коде здесь можно вытащить размеры через PIL,
    # пока ставим заглушки, как в вашей модели Image
    db.execute(
        """INSERT INTO images (file_path, original_name, mime_type, file_size, width, height, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (unique_filename, file.filename, file.content_type, 0, 0, 0, datetime.now()),
        commit=True
    )

    # Получаем id последней картинки
    image_id = db.cursor.lastrowid

    # Связываем картинку полиморфно через таблицу картинок
    db.execute(
        "INSERT INTO images_links (image_id, entity_type, entity_id, created_at) VALUES (?, ?, ?, ?)",
        (image_id, entity_type, entity_id, datetime.now()),
        commit=True
    )


@app.on_event("startup")
def startup_event():
    initialize_database()


@app.middleware("http")
async def add_user_to_request(
        request: Request,
        call_next
):
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
async def read_root(
        request: Request,
        db: Database = Depends(get_db),
        user: dict | None = Depends(get_optional_user)
):
    context = None
    if user:
        trips = get_entity_from_db("trips", request.state.user["id"])
        context = {"trips": trips}
    return render_template(request, "index.html", context)


@app.get("/places", response_class=HTMLResponse, tags=["Public"])
async def places(
        request: Request,
        q: Optional[str] = "",
        db: Database = Depends(get_db)
):
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
async def get_place(
        request: Request,
        place_id: int,
        db: Database = Depends(get_db)
):
    # 1. Получаем основную информацию о месте
    place = db.select("places", where="id = ?", params=(place_id,), fetch_one=True)
    if not place:
        raise HTTPException(status_code=404, detail="Место не найдено")

    # 2. Получаем ID изображений для галереи
    gallery_links = db.execute(
        "SELECT image_id FROM images_links WHERE entity_type = 'gallery' AND entity_id = ?",
        (place_id,)
    ).fetchall()
    gallery_images = [row["image_id"] for row in gallery_links]

    # 3. Получаем достопримечательности
    attractions = db.select("attractions", where="place_id = ?", params=(place_id,))

    return render_template(request, "place_page.html", {
        "place": place,
        "gallery_images": gallery_images,
        "attractions": attractions
    })


@app.get("/media/{entity_type}/{entity_id}", tags=["Media"])
async def get_universal_image(
        entity_type: str,
        entity_id: int,
        index: int = 0,  # Позволяет выбирать 1-ю, 2-ю или 3-ю картинку для галерей
        db: Database = Depends(get_db)
):
    """
    Универсальный роут для получения ОДНОГО изображения сущности.
    Примеры путей:
      - /media/place/5         (главное фото места №5)
      - /media/user/12         (аватар пользователя №12)
      - /media/gallery/5?index=1  (вторая фотография из галереи места №5)
    """
    # Приводим к нижнему регистру и убираем "s" на конце, если случайно передали во множественном числе
    entity_type = entity_type.lower().rstrip('s')

    # Ищем все изображения, привязанные к этому объекту, сортируя по дате добавления
    query = """
            SELECT i.file_path, i.mime_type
            FROM images i
                     JOIN images_links il ON i.id = il.image_id
            WHERE il.entity_type = ? \
              AND il.entity_id = ?
            ORDER BY il.created_at ASC \
            """
    images = db.execute(query, (entity_type, entity_id)).fetchall()

    # Если изображения найдены и запрашиваемый индекс корректен
    if images and 0 <= index < len(images):
        img = images[index]
        file_path = UPLOAD_DIR / img["file_path"]
        if file_path.exists():
            return FileResponse(file_path, media_type=img["mime_type"])

    # --- УМНЫЕ ЗАГЛУШКИ (FALLBACKS) ---
    # Если картинка в базе или на диске отсутствует, отдаем дефолтные изображения из static
    if entity_type in ["user", "avatar"]:
        default_avatar = Path("static/assets/default-avatar.png")
        if default_avatar.exists():
            return FileResponse(default_avatar, media_type="image/png")

    # Заглушка по умолчанию для мест, поездок и достопримечательностей
    default_placeholder = Path("static/images/placeholder.jpg")
    if default_placeholder.exists():
        return FileResponse(default_placeholder, media_type="image/jpeg")

    # Если даже заглушек нет в папке static, отдаем 404
    raise HTTPException(status_code=404, detail="Изображение не найдено")


@app.get("/media/id/{image_id}", tags=["Media"])
async def get_image_by_id(image_id: int, db: Database = Depends(get_db)):
    """
    Дополнительный роут: получение картинки напрямую по её уникальному ID из таблицы images.
    Полезно, когда бэкенд уже прислал список ID картинок в галерее.
    """
    img = db.execute("SELECT file_path, mime_type FROM images WHERE id = ?", (image_id,)).fetchone()
    if img:
        file_path = UPLOAD_DIR / img["file_path"]
        if file_path.exists():
            return FileResponse(file_path, media_type=img["mime_type"])

    raise HTTPException(status_code=404, detail="Изображение по ID не найдено")

@app.get("/login", tags=["Public"])
async def login_redirect(
        request: Request
):
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

    if not user or not verify_password(password, user["hashed_password"]):
        response = RedirectResponse(url=referer, status_code=status.HTTP_303_SEE_OTHER)
        return set_flash_message(response, "error", "Неверный email или пароль")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )

    response = RedirectResponse(url=referer, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token", value=f"Bearer {access_token}", httponly=True, max_age=1800, samesite="lax"
    )
    return set_flash_message(response, "success", f"С возвращением, {user['fullname']}!")


@app.get("/register", response_class=HTMLResponse, tags=["Public"])
async def register_page(
        request: Request,
        user: dict | None = Depends(get_optional_user)
):
    if user:
        return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)

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
        response = RedirectResponse(url="/register", status_code=status.HTTP_303_SEE_OTHER)
        return set_flash_message(response, "warning", "Пользователь с таким email уже существует")

    # Hash the password
    hashed_pw = get_password_hash(password)

    try:
        user = User(fullname=fullname, email=email, phone=phone, country=country, hashed_password=hashed_pw)
        db.add("users", user.model_dump())
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        return set_flash_message(response, "success", "Успешная регистрация! Теперь вы можете войти.")
    except Error as err:
        print(f"Database Error: {err}")
        return render_template(request, "register.html", {"error": "Произошла ошибка при регистрации. Попробуйте позже."})


@app.get("/logout", tags=["Auth"])
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


@app.get("/mytrips", response_class=HTMLResponse, tags=["Auth"])
async def read_my_trips(
        request: Request,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    trips = get_entity_from_db("trips", request.state.user["id"])
    return render_template(request, "trips.html", {"trips": trips})


@app.get("/create", response_class=HTMLResponse, tags=["Auth"])
async def create_page(
        request: Request,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
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
    try:
        trip = Trip(name=trip_name, city=destination, country="TEST", date_from=trip_date.isoformat(),
                    date_to="2999-01-01", user_id=1)
        db.add("trips", trip.model_dump())
    except Error as err:
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
async def budget_page(
        request: Request,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    return render_template(request, "budget.html")


@app.get("/checklists", tags=["Auth"])
async def checklists(
        request: Request,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
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


@app.get("/reset", tags=["Auth"])
async def reset(
        request: Request,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    pass


@app.get("/admin/places/new", tags=["Admin"])
async def admin_create_page(
        request: Request,
        db: Database = Depends(get_db),
        admin_user: dict = Depends(get_admin_user)
):
    return render_template(request, "create_place.html")


@app.post("/admin/places/create", tags=["Admin"])
async def admin_create_place(
        request: Request,
        city: str = Form(...),
        country: str = Form(...),
        description: str = Form(...),
        subtitle: Optional[str] = Form(None),
        rating: Optional[float] = Form(None),
        hero_image: UploadFile = File(...),
        gallery_images: List[UploadFile] = File(None),
        db: Database = Depends(get_db),
        admin_user: dict = Depends(get_admin_user)
):
    # 1. Сохраняем "Место" в таблицу places
    db.execute(
        """INSERT INTO places (city, country, rating, description, subtitle, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (city, country, rating, description, subtitle, datetime.now()),
        commit=True
    )
    place_id = db.cursor.lastrowid

    # 2. Сохраняем обложку (hero_image) с типом связки 'place'
    await save_uploaded_photo(hero_image, "place", place_id, db)

    # 3. Сохраняем массив картинок галереи (до 3-х) с типом связки 'gallery'
    if gallery_images:
        for g_file in gallery_images:
            if g_file.filename:  # Проверка, что файл прикреплен
                await save_uploaded_photo(g_file, "gallery", place_id, db)

    # 4. Обрабатываем достопримечательности динамически из form_data
    form_data = await request.form()

    for i in range(1, 4):
        heading = form_data.get(f"attr_heading_{i}")
        attr_desc = form_data.get(f"attr_description_{i}")
        attr_file = form_data.get(f"attr_image_{i}")  # Это UploadFile

        # Если админ заполнил хотя бы заголовок достопримечательности
        if heading and heading.strip():
            db.execute(
                "INSERT INTO attractions (place_id, heading, description, created_at) VALUES (?, ?, ?, ?)",
                (place_id, heading, attr_desc or "", datetime.now()),
                commit=True
            )
            attraction_id = db.cursor.lastrowid

            # Если к достопримечательности прикреплено фото — привязываем его
            if attr_file and attr_file.filename:
                await save_uploaded_photo(attr_file, "attraction", attraction_id, db)

    response = RedirectResponse(url="/places", status_code=status.HTTP_303_SEE_OTHER)
    return set_flash_message(response, "success", "Новое место и достопримечательности успешно добавлены!")


@app.post("/admin/places/delete/{place_id}", tags=["Admin"])
async def delete_place(
    place_id: int,
    db: Database = Depends(get_db),
    admin_user: dict = Depends(get_admin_user)
):
    db.remove("places", where="id = ?", params=(place_id,))
    return RedirectResponse(url="/places", status_code=status.HTTP_303_SEE_OTHER)


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('static/favicon.ico')