import bcrypt, jwt

from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, status, Request, Depends
from utils import get_db
from database.database import Database
from jwt.exceptions import PyJWTError
from config import Config
from secrets import choice
from string import ascii_uppercase, digits


SECRET_KEY = Config.SECRET_KEY
ALGORITHM = Config.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = Config.ACCESS_TOKEN_EXPIRE_MINUTES


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Переводим строки в байты
    password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    # Сравниваем
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)

def get_password_hash(password: str) -> str:
    # Генерируем соль и хешируем
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    # Возвращаем строку для сохранения в БД
    return hashed_password.decode('utf-8')


def generate_unique_personal_id(db: Database, length=8) -> str:
    """Генерирует уникальный буквенно-цифровой ID и проверяет его отсутствие в БД."""
    while True:
        # Генерируем случайную строку (например, "A1B2C3D4")
        code = ''.join(choice(ascii_uppercase + digits) for _ in range(length))

        existing = db.select("users", where="personal_id = ?", params=(code,), fetch_one=True)

        if not existing:
            return code


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        # Убираем префикс Bearer, если он есть
        if token.startswith("Bearer "):
            token = token.replace("Bearer ", "")
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except PyJWTError:
        return None


# --- Dependency to protect routes ---
def get_current_user(request: Request, db: Database = Depends(get_db)):
    token = request.cookies.get("access_token")

    if not token:
        # If no token, redirect to login page instead of throwing JSON error
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})

    try:
        # Strip "Bearer " prefix if we appended it
        token = token.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    except JWTError:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})

    user = db.select("users", where="email = ?", params=(email,), fetch_one=True)
    if user is None:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})

    return dict(user)


def get_optional_user(request: Request, db: Database = Depends(get_db)):
    """Returns the current user dict if logged in, otherwise None."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        token = token.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None

    user = db.select("users", where="email = ?", params=(email,), fetch_one=True)
    return dict(user) if user else None


# Зависимость проверки на администратора
def get_admin_user(request: Request, current_user: dict = Depends(get_current_user)):
    # В SQLite BOOLEAN хранится как 0 или 1, поэтому get("is_admin") вернет 1 (True) для админов
    if not current_user.get("is_admin"):
        # Если это не админ, выбрасываем ошибку 403
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Требуются права администратора."
        )
    return current_user