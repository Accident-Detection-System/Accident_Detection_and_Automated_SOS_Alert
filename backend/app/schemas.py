from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

class HospitalRegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=6)
    location: Optional[str] = None
    phone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class UserRegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=6)
    phone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class CameraIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    location: Optional[str] = None

class SOSIn(BaseModel):
    lat: float
    lon: float

class GPSIn(BaseModel):
    lat: float
    lon: float
