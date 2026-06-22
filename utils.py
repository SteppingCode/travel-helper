from fastapi import Response, Request
from sqlite3 import Row
from fastapi.templating import Jinja2Templates
from database.database import Database
from urllib import parse


templates = Jinja2Templates(directory="templates")


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


def get_records(
        table: str,
        where: str | None = None,
        params: tuple | list | None = None,
        order_by: str | None = None,
        limit: int | None = None,
        fetch_one: bool = False,
        check_image_type: str | None = None  # Укажите тип ('place', 'user' и т.д.), если нужно проверить картинку
) -> dict | list[dict] | None:
    """
    Универсальная функция для получения любых данных из БД.
    Возвращает словарь (если fetch_one=True), список словарей или None.
    """
    db = Database()
    try:
        result = db.select(
            table=table,
            where=where,
            params=params,
            order_by=order_by,
            limit=limit,
            fetch_one=fetch_one
        )

        if not result:
            return None if fetch_one else []

        def process_row(row: Row) -> dict:
            data = dict(row)
            if check_image_type:
                image_exists = check_image_exists(check_image_type, data["id"])
                data["has_image"] = True if image_exists else False
            return data

        if fetch_one:
            return process_row(result)

        return [process_row(row) for row in result]

    finally:
        db.close()


def set_flash_message(response: Response, type: str, message: str) -> Response:
    """
    Добавляет cookie с уведомлением, которое прочитает JS на клиенте.
    Допустимые типы: 'success', 'error', 'warning', 'info'
    """
    # Кодируем сообщение, чтобы пробелы и русский язык безопасно передались через HTTP заголовки
    encoded_msg = parse.quote(f"{type}|{message}")

    response.set_cookie(
        key="toast_msg",
        value=encoded_msg,
        max_age=10,
        path="/",
        samesite="lax"
    )
    return response


def render_template(request: Request, name: str, context: dict = None):
    if context is None:
        context = {}

    context.update({"user": request.state.user})

    return templates.TemplateResponse(request, name, context)