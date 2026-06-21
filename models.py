from pydantic import BaseModel
from typing import Optional


class Trip(BaseModel):
    name: str
    city: str
    country: str
    date_from: str
    date_to: str
    user_id: int
    budget: Optional[float] = None


class User(BaseModel):
    fullname: str
    email: str
    phone: str
    city: Optional[str] = None
    country: str
    hashed_password: str
    is_admin: bool = False
    email_notifications: bool = False
    budget: Optional[float] = None


class Place(BaseModel):
    city: str
    country: str
    rating: Optional[float] = None
    description: str
    subtitle: Optional[str] = None


class Attraction(BaseModel):
    place_id: int
    heading: str
    description: str


class Tag(BaseModel):
    text: str
    entity_type: str
    entity_id: int


class Image(BaseModel):
    file_path: str
    original_name: str
    mime_type: str
    file_size: int
    width: int
    height: int


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class AddItemRequest(BaseModel):
    type: str  # 'place', 'task', 'member', 'tag'
    value: str
