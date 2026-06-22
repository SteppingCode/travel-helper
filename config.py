from os import getenv
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass


load_dotenv()


@dataclass
class Config:
    SECRET_KEY: str = getenv("SECRET_KEY")
    ALGORITHM: str = getenv("ALGORITHM")
    # noinspection PyTypeChecker
    ACCESS_TOKEN_EXPIRE_MINUTES: float = float(getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    UPLOAD_DIR = Path("uploads")