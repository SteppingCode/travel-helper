from fastapi import Response, Request
from sqlite3 import Row
from fastapi.templating import Jinja2Templates
from database.database import Database
import urllib.parse

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


def get_entity_from_db(table_name: str) -> list | None:
    db = Database()
    entity = db.select(table_name)

    entity_list = []
    for e in entity:
        e_dict = dict(e)  # Convert sqlite3.Row to dict
        e_dict["has_image"] = check_image_exists(table_name[0:-1], e["id"])
        entity_list.append(e_dict)

    return entity_list


def set_flash_message(response: Response, type: str, message: str) -> Response:
    """
    Добавляет cookie с уведомлением, которое прочитает JS на клиенте.
    Допустимые типы: 'success', 'error', 'warning', 'info'
    """
    # Кодируем сообщение, чтобы пробелы и русский язык безопасно передались через HTTP заголовки
    encoded_msg = urllib.parse.quote(f"{type}|{message}")

    response.set_cookie(
        key="toast_msg",
        value=encoded_msg,
        max_age=10,  # Cookie живет всего 10 секунд (хватит для редиректа)
        path="/",
        samesite="lax"
    )
    return response


def render_template(request: Request, name: str, context: dict = None):
    if context is None:
        context = {}

    context.update({"user": request.state.user})

    return templates.TemplateResponse(request, name, context)