from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, ValidationInfo


class UserCreate(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    password: str
    password_confirm: str

    @field_validator('password_confirm')
    @classmethod
    def passwords_match(cls, v, info: ValidationInfo):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Пароли не совпадают')
        return v


class UserUpdate(BaseModel):
    id: int
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    password_confirm: Optional[str] = None

    @field_validator('password_confirm')
    @classmethod
    def passwords_match(cls, v, info: ValidationInfo):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Пароли не совпадают')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
