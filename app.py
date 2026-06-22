from datetime import datetime, date
from sqlite3 import Error
from pathlib import Path
from urllib import response

from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from database.database import Database, initialize_database
from utils import get_db, set_flash_message, render_template, get_records
from fastapi import FastAPI, Form, Request, HTTPException, Depends, status, UploadFile, File
from fastapi.staticfiles import StaticFiles
from models import *
from auth import (get_password_hash, verify_password, create_access_token, get_current_user,
                  timedelta, ACCESS_TOKEN_EXPIRE_MINUTES, get_optional_user, decode_token,
                  get_admin_user, generate_unique_personal_id)
from os import path
from typing import List, Optional
from shutil import copyfileobj
from uuid import uuid4
from config import Config

app = FastAPI()

Config.UPLOAD_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


async def save_uploaded_photo(file: UploadFile, entity_type: str, entity_id: int, db: Database):
    if not file or not file.filename:
        return

    file_extension = path.splitext(file.filename)[1]
    unique_filename = f"{uuid4()}{file_extension}"
    file_path = Config.UPLOAD_DIR / unique_filename

    with open(file_path, "wb") as buffer:
        # noinspection PyTypeChecker
        copyfileobj(file.file, buffer)

    from PIL.Image import open as o
    file_size = path.getsize(Config.UPLOAD_DIR / unique_filename)
    width, height = o(Config.UPLOAD_DIR / unique_filename).size
    image_type = o(Config.UPLOAD_DIR / unique_filename).get_format_mimetype()

    # noinspection PyTypeChecker
    image = Image(
        file_path=unique_filename,
        original_name=file.filename,
        mime_type=image_type,
        file_size=file_size,
        width=width,
        height=height
    )
    db.add("images", image.model_dump())

    image_id = db.cursor.lastrowid

    db.add("images_links", {
        "image_id": image_id,
        "entity_type": entity_type,
        "entity_id": entity_id
    })


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
            db.close()

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
        trips = get_records(
            table="trips",
            where="user_id = ?",
            params=(request.state.user["id"],),
            order_by="created_at DESC"
        )
        context = {"trips": trips}
    return render_template(request, "index.html", context)


@app.get("/places", response_class=HTMLResponse, tags=["Public"])
async def places(
        request: Request,
        q: Optional[str] = "",
        db: Database = Depends(get_db)
):
    places = get_records(
        table="places",
        order_by="rating DESC",
        check_image_type="place"
    )
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
    place = get_records(
        table="places",
        where="id = ?",
        params=(place_id,),
        fetch_one=True,
        check_image_type="place"
    )

    if not place:
        raise HTTPException(
            status_code=404,
            detail="Место не найдено"
        )

    gallery_links = db.execute(
        "SELECT image_id FROM images_links WHERE entity_type = 'gallery' AND entity_id = ?",
        (place_id,)
    ).fetchall()
    gallery_images = [row["image_id"] for row in gallery_links]

    attractions = get_records(
        table="attractions",
        where="place_id = ?",
        params=(place_id,),
        check_image_type="attraction"
    )

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
    entity_type = entity_type.lower().rstrip('s')

    query = """
            SELECT i.file_path, i.mime_type
            FROM images i
                     JOIN images_links il ON i.id = il.image_id
            WHERE il.entity_type = ? \
              AND il.entity_id = ?
            ORDER BY il.created_at ASC \
            """
    images = db.execute(query, (entity_type, entity_id)).fetchall()

    if images and 0 <= index < len(images):
        img = images[index]
        file_path = Config.UPLOAD_DIR / img["file_path"]
        if file_path.exists():
            return FileResponse(
                file_path,
                media_type=img["mime_type"]
            )

    if entity_type in ["user", "avatar"]:
        default_avatar = Path("static/assets/default-avatar.png")
        if default_avatar.exists():
            return FileResponse(
                default_avatar,
                media_type="image/png"
            )

    raise HTTPException(
        status_code=404,
        detail="Изображение не найдено"
    )


@app.get("/media/id/{image_id}", tags=["Media"])
async def get_image_by_id(image_id: int, db: Database = Depends(get_db)):
    """
    Дополнительный роут: получение картинки напрямую по её уникальному ID из таблицы images.
    Полезно, когда бэкенд уже прислал список ID картинок в галерее.
    """
    img = db.select(
        table="images",
        columns="file_path, mime_type",
        where="id = ?",
        params=(image_id,)
    ).fetchone()

    if img:
        file_path = Config.UPLOAD_DIR / img["file_path"]
        if file_path.exists():
            return FileResponse(file_path, media_type=img["mime_type"])

    raise HTTPException(status_code=404, detail="Изображение по ID не найдено")


@app.get("/login", tags=["Public"])
async def login_redirect(
        request: Request
):
    response = RedirectResponse(
        url="/",
        status_code=status.HTTP_303_SEE_OTHER
    )
    return set_flash_message(response, "warning", "Войдите в профиль для просмотра страницы")


@app.post("/login", tags=["Public"])
async def login(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        db: Database = Depends(get_db)
):
    referer = request.headers.get("referer", "/")
    user = get_records(
        table="users",
        where="email = ?",
        params=(email,),
        fetch_one=True
    )

    if not user or not verify_password(password, user["hashed_password"]):
        response = RedirectResponse(
            url=referer,
            status_code=status.HTTP_303_SEE_OTHER
        )
        return set_flash_message(response, "error", "Неверный email или пароль")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=access_token_expires
    )

    response = RedirectResponse(
        url=referer,
        status_code=status.HTTP_303_SEE_OTHER
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,
        samesite="lax"
    )
    return set_flash_message(response, "success", f"С возвращением, {user['fullname']}!")


@app.get("/register", response_class=HTMLResponse, tags=["Public"])
async def register_page(
        request: Request,
        user: dict | None = Depends(get_optional_user)
):
    if user:
        return RedirectResponse(
            url="/profile",
            status_code=status.HTTP_303_SEE_OTHER
        )

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
    existing_user = get_records(
        table="users",
        where="email = ?",
        params=(email,),
        fetch_one=True
    )

    if existing_user:
        response = RedirectResponse(
            url="/register",
            status_code=status.HTTP_303_SEE_OTHER
        )
        return set_flash_message(response, "warning", "Пользователь с таким email уже существует")

    hashed_pw = get_password_hash(password)
    personal_id = generate_unique_personal_id(db)

    try:
        user = User(
            fullname=fullname,
            email=email,
            phone=phone,
            country=country,
            hashed_password=hashed_pw,
            personal_id=personal_id
        )
        db.add("users", user.model_dump())

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": email},
            expires_delta=access_token_expires
        )

        response = RedirectResponse(
            url="/profile",
            status_code=status.HTTP_303_SEE_OTHER
        )
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=1800,
            samesite="lax"
        )
        return set_flash_message(response, "success", "Успешная регистрация! Добро пожаловать.")

    except Error as err:
        print(f"Database Error: {err}")
        return render_template(request, "register.html",
                               {"error": "Произошла ошибка при регистрации. Попробуйте позже."})


@app.get("/logout", tags=["Auth"])
async def logout():
    response = RedirectResponse(
        url="/",
        status_code=status.HTTP_303_SEE_OTHER
    )
    response.delete_cookie("access_token")
    return response


@app.get("/mytrips", response_class=HTMLResponse, tags=["Auth"])
async def read_my_trips(
        request: Request,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    ru_months = ["", "янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
    trips_raw = get_records(
        table="trips",
        where="user_id = ?",
        params=(current_user["id"],),
        order_by="date_from ASC",
        check_image_type="trip"
    )

    today = datetime.now().date()
    trips = []
    nearest_trip = None
    min_days_left = float('inf')

    # noinspection PyTypeChecker
    for t in trips_raw:
        try:
            d_from = datetime.fromisoformat(t["date_from"].split("T")[0]).date()
            d_to = datetime.fromisoformat(t["date_to"].split("T")[0]).date()

            t["formatted_date"] = \
                (f"{d_from.day} {ru_months[d_from.month]} - "
                 f"{d_to.day} {ru_months[d_to.month]} {d_to.year}")
            days_left = (d_from - today).days

            if days_left > 0:
                t["status"] = "Запланировано"
                t["days_left"] = days_left

                # Ищем самую ближайшую запланированную поездку
                if days_left < min_days_left:
                    min_days_left = days_left
                    nearest_trip = t
            elif d_from <= today <= d_to:
                t["status"] = "В процессе"
                t["days_left"] = 0
                if nearest_trip is None or nearest_trip["status"] != "В процессе":
                    nearest_trip = t
            else:
                t["status"] = "Завершено"
                t["days_left"] = None
        except Exception as e:
            t["formatted_date"] = "Даты не указаны"
            t["status"] = "Неизвестно"
            t["days_left"] = None

        try:
            t["places_count"] = db.execute("SELECT COUNT(*) FROM trip_places WHERE trip_id = ?",
                                           (t["id"],)).fetchone()[0]
        except:
            t["places_count"] = 0

        try:
            t["tasks_count"] = db.execute("SELECT COUNT(*) FROM checklists WHERE trip_id = ? AND user_id = ?",
                                          (t["id"], request.state.user['id'])).fetchone()[0]
        except:
            t["tasks_count"] = 0

        try:
            t["members_count"] = \
                db.execute("SELECT COUNT(*) FROM trip_members WHERE trip_id = ?",
                           (t["id"],)).fetchone()[0] + 1
        except:
            t["members_count"] = 1

        trips.append(t)

    # Если запланированных нет, берем последнюю завершенную как "ближайшую" (история)
    if not nearest_trip and trips:
        nearest_trip = trips[-1]

    return render_template(request, "trips.html",
                           {
                               "trips": trips,
                               "nearest_trip": nearest_trip
                           })


# app.py
@app.get("/trip/{trip_id}", response_class=HTMLResponse, tags=["Auth"])
async def trip_page(
        request: Request,
        trip_id: int,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    trip = get_records(
        table="trips",
        where="id = ? AND user_id = ?",
        params=(trip_id, current_user["id"]),
        fetch_one=True,
        check_image_type="trip"
    )
    if not trip:
        raise HTTPException(status_code=404, detail="Путешествие не найдено или нет доступа")

    return render_template(request, "trip_details.html", {"trip": trip})


@app.post("/trip/add_db_place/{place_id}", tags=["Auth"])
async def link_place_to_trip(
        request: Request,
        place_id: int,
        trip_id: int = Form(...),
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    trip = get_records(
        table="trips",
        where="id = ? AND user_id = ?",
        params=(trip_id, current_user["id"]),
        fetch_one=True
    )
    if not trip:
        return set_flash_message(RedirectResponse(
            url=f"/place/{place_id}",
            status_code=303), "error", "Ошибка доступа"
        )

    # Добавляем связь
    db.add("trip_places", {"trip_id": trip_id, "place_id": place_id})
    response = RedirectResponse(
        url=f"/trip/{trip_id}",
        status_code=303
    )
    return set_flash_message(response, "success", "Место успешно добавлено в маршрут!")


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
        trip_from: date = Form(...),
        trip_to: date = Form(...),
        country_destination: str = Form(...),
        city_destination: str = Form(...),
        budget: Optional[float] = Form(None),
        preview: UploadFile = File(None),
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    try:
        trip = Trip(
            name=trip_name,
            city=city_destination,
            country=country_destination,
            date_from=trip_from.isoformat(),
            date_to=trip_to.isoformat(),
            user_id=request.state.user['id'],
            budget=budget
        )
        db.add("trips", trip.model_dump())
        if preview:
            trip_id = db.cursor.lastrowid
            await save_uploaded_photo(preview, "trip", trip_id, db)
    except Error as err:
        print(err)
    return RedirectResponse(
        url="/mytrips",
        status_code=303
    )


@app.get("/budget", response_class=HTMLResponse)
async def budget_page(
        request: Request,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]

    # 1. Получаем общий бюджет самого пользователя
    user_row = db.select("users", "budget", where="id = ?", params=(user_id,), fetch_one=True)
    total_budget = user_row["budget"] if user_row and user_row["budget"] else 0.0

    # 2. Получаем все поездки пользователя
    user_trips = db.select("trips", where="user_id = ?", params=(user_id,))

    # 3. Расчет статистических показателей
    trip_budgets = [t["budget"] for t in user_trips if t["budget"] is not None]

    planned_budget = sum(trip_budgets)
    avg_budget = planned_budget / len(trip_budgets) if trip_budgets else 0.0

    # Потрачено — сумма бюджетов завершенных (completed = 1) поездок
    spent_budget = sum([t["budget"] for t in user_trips if t["budget"] is not None and t["completed"] == 1])

    trips_data = []
    for t in user_trips:
        trip_budget = t["budget"] or 0.0
        print(trip_budget)
        # Вычисляем, какую долю общих средств занимает эта поездка
        percent = (trip_budget / total_budget * 100) if total_budget > 0 else 0
        print(percent)
        print(min(100, round(percent)))

        trips_data.append({
            "name": t["name"],
            "budget": f"{trip_budget:,.0f}".replace(",", " "),
            "percent": min(100, round(percent))
        })

    # Форматируем вывод чисел (например: 150000 -> 150 000)
    context = {
        "request": request,
        "user": current_user,
        "total_budget": f"{total_budget:,.0f}".replace(",", " "),
        "avg_budget": f"{avg_budget:,.0f}".replace(",", " "),
        "planned_budget": f"{planned_budget:,.0f}".replace(",", " "),
        "spent_budget": f"{spent_budget:,.0f}".replace(",", " "),
        "trips": trips_data
    }

    # Возвращаем отрендеренный шаблон (используя Jinja2)
    return render_template(request, "budget.html", context)


@app.get("/profile", tags=["Auth"])
async def profile_page(
        request: Request,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    return render_template(request, "profile.html")


# --- ПРОФИЛЬ ---
@app.post("/profile", tags=["Auth"])
async def update_profile(
        request: Request,
        email: str = Form(...),
        phone: str = Form(...),
        city: Optional[str] = Form(None),
        budget: Optional[float] = Form(None),
        email_alerts: Optional[str] = Form(None),
        avatar: UploadFile = File(None),
        remove_avatar: str = Form("0"),
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    is_email = 1 if email_alerts == 'on' else 0

    db.update("users", {
        "email": email,
        "phone": phone,
        "city": city,
        "budget": budget,
        "email_notifications": is_email,
    }, where="id = ?", params=(current_user["id"],))

    user_avatar_id = db.execute(
        "SELECT i.id FROM images i INNER JOIN images_links il ON il.image_id = i.id WHERE il.entity_type = 'user' AND il.entity_id = ?",
        (request.state.user["id"],)).fetchone()

    if user_avatar_id and remove_avatar == "1":
        db.remove("images", "id = ?", (user_avatar_id['id'],))
        db.update("users", {"has_avatar": 0}, "id = ?", (request.state.user["id"],))
    elif user_avatar_id and avatar and avatar.filename:
        db.remove("images", "id = ?", (user_avatar_id['id'],))
        await save_uploaded_photo(avatar, "user", request.state.user["id"], db)
    elif avatar and avatar.filename:
        await save_uploaded_photo(avatar, "user", request.state.user["id"], db)
        db.update("users", {"has_avatar": 1}, "id = ?", (request.state.user["id"],))

    response = RedirectResponse(
        url="/profile",
        status_code=status.HTTP_303_SEE_OTHER
    )
    return set_flash_message(response, "success", "Профиль успешно сохранен!")


@app.get("/checklists", tags=["Auth"])
async def checklists_page(
        request: Request,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    trips = get_records(
        table="trips",
        where="user_id = ?",
        params=(request.state.user["id"],),
        order_by="date_from ASC",
    )

    trips_data = []

    # noinspection PyTypeChecker
    for trip in trips:
        trip_id = trip["id"]
        existing = db.select("checklists", where="user_id = ? AND trip_id = ?",
                             params=(request.state.user["id"], trip_id))

        checklists = {}
        for row in existing:
            cat = row["category"]

            if cat not in checklists:
                checklists[cat] = []

            checklists[cat].append({
                "id": row["id"],
                "text": row["item_text"],
                "done": bool(row["is_done"]),
                "user_data": row["user_data"]
            })

        trips_data.append({
            "trip": dict(trip),
            "checklists": checklists
        })

    return render_template(request, "checklists.html", {"trips_data": trips_data})


@app.post("/checklists", tags=["Auth"])
async def save_checklists(
        request: Request,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    form_data = await request.form()

    # Получаем все ID чек-листов пользователя
    items = db.select("checklists", columns="id", where="user_id = ?", params=(current_user["id"],))

    # Обновляем каждый (если чекбокс нажат, он вернет 'on', иначе None)
    # noinspection PyTypeChecker
    for item in items:
        item_id = item["id"]
        is_done = 1 if form_data.get(f"item_{item_id}_done") == "on" else 0
        user_data = form_data.get(f"item_{item_id}_data", "")

        db.execute(
            "UPDATE checklists SET is_done = ?, user_data = ? WHERE id = ? AND user_id = ?",
            (is_done, user_data, item_id, current_user["id"]), commit=True
        )

    return RedirectResponse(
        url="/checklists",
        status_code=status.HTTP_303_SEE_OTHER
    )


@app.get("/reset", tags=["Auth"])
async def reset_checklists(
        request: Request,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    db.remove("checklists", where="user_id = ?", params=(current_user["id"],))
    return RedirectResponse(
        url="/checklists",
        status_code=status.HTTP_303_SEE_OTHER
    )


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
    place = Place(
        city=city,
        country=country,
        rating=rating,
        description=description,
        subtitle=subtitle
    )
    db.add("places", place.model_dump())
    place_id = db.cursor.lastrowid

    await save_uploaded_photo(hero_image, "place", place_id, db)

    if gallery_images:
        for g_file in gallery_images:
            if g_file.filename:
                await save_uploaded_photo(g_file, "gallery", place_id, db)

    form_data = await request.form()

    for i in range(1, 4):
        # noinspection PyTypeChecker
        heading: str = form_data.get(f"attr_heading_{i}")
        attr_desc = form_data.get(f"attr_description_{i}")
        attr_file = form_data.get(f"attr_image_{i}")  # Это UploadFile

        # Если админ заполнил хотя бы заголовок достопримечательности
        if heading and heading.strip():
            attraction = Attraction(place_id=place_id, heading=heading, description=description)
            db.add("attractions", attraction.model_dump())
            attraction_id = db.cursor.lastrowid

            # Если к достопримечательности прикреплено фото — привязываем его
            if attr_file and attr_file.filename:
                # noinspection PyTypeChecker
                await save_uploaded_photo(attr_file, "attraction", attraction_id, db)

    response = RedirectResponse(
        url="/places",
        status_code=status.HTTP_303_SEE_OTHER
    )
    return set_flash_message(response, "success", "Новое место и достопримечательности успешно добавлены!")


@app.post("/admin/places/delete/{place_id}", tags=["Admin"])
async def delete_place(
        place_id: int,
        db: Database = Depends(get_db),
        admin_user: dict = Depends(get_admin_user)
):
    db.remove("places", where="id = ?", params=(place_id,))
    return RedirectResponse(
        url="/places",
        status_code=status.HTTP_303_SEE_OTHER
    )


@app.get("/api/user/trips", tags=["Auth"])
async def api_get_user_trips(
        request: Request,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    return get_records(
        table="trips",
        where="user_id = ?",
        params=(request.state.user["id"],)
    )


@app.get("/api/trip/{trip_id}/data", tags=["Auth"])
async def api_get_trip_data(
        request: Request,
        trip_id: int,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    places_query = """
                   SELECT tp.id, COALESCE(p.city, tp.custom_name) as place_name
                   FROM trip_places tp
                            LEFT JOIN places p ON tp.place_id = p.id
                   WHERE tp.trip_id = ? \
                   """
    places = [dict(row) for row in db.execute(places_query, (trip_id,)).fetchall()]

    # Чек-листы, участники и теги
    tasks = db.select("checklists", where="trip_id = ? AND user_id = ?", params=(trip_id, request.state.user['id']))
    members = db.select("trip_members", columns="id, member_name", where="trip_id = ?", params=(trip_id,))
    tags = db.select("trip_tags", columns="id, tag_name", where="trip_id = ?", params=(trip_id,))

    # print(places, tasks, members, tags)

    return {
        "places": [dict(t) for t in places],
        "tasks": [dict(t) for t in tasks],
        "members": [dict(m) for m in members],
        "tags": [dict(t) for t in tags]
    }


@app.post("/api/trip/{trip_id}/add_item", tags=["Auth"])
async def api_add_trip_item(
        request: Request,
        trip_id: int,
        item: AddItemRequest,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    trip = get_records(
        table="trips",
        where="id = ? AND user_id = ?",
        params=(trip_id, request.state.user["id"]),
        fetch_one=True
    )

    if not trip:
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещен"
        )

    table_map = {
        "place": ("trip_places", {"trip_id": trip_id, "custom_name": item.value}),
        "task": ("checklists", {"user_id": request.state.user['id'], "trip_id": trip_id, "category": item.value, "item_text": item.value}),
        "member": ("trip_members", {"trip_id": trip_id, "member_name": item.value}),
        "tag": ("trip_tags", {"trip_id": trip_id, "tag_name": item.value}),
    }

    if item.type not in table_map:
        raise HTTPException(
            status_code=400,
            detail="Неверный тип"
        )

    table, data = table_map[item.type]

    # Не более 10 участников (1 организатор + 9 добавленных)
    if item.type == "member":
        count = db.execute("SELECT COUNT(*) FROM trip_members WHERE trip_id = ?", (trip_id,)).fetchone()[0]
        if count >= 9:
            raise HTTPException(
                status_code=400,
                detail="Достигнут лимит: максимум 10 участников"
            )

    db.add(table, data)
    return {
        "status": "ok"
    }


@app.delete("/api/trip/delete_item/{item_type}/{item_id}", tags=["Auth"])
async def api_delete_trip_item(
        request: Request,
        item_type: str,
        item_id: int,
        db: Database = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    table_map = {"place": "trip_places", "task": "checklists", "member": "trip_members", "tag": "trip_tags"}
    if item_type in table_map:
        db.remove(table_map[item_type], where="id = ?", params=(item_id,))
    return {"status": "ok"}


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('static/favicon.ico')
