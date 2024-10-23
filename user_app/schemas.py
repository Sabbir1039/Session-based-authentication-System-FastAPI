from pydantic import BaseModel, EmailStr
from fastapi import Form, UploadFile
from typing import Optional

class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    password: str

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        email: EmailStr = Form(...),
        password: str = Form(...),
    ):
        return cls(name=name, email=email, password=password)

class LoginSchema(BaseModel):
    email: EmailStr
    password: str
    
    @classmethod
    def as_form(
        cls,
        email: EmailStr = Form(...),
        password: str = Form(...),
    ):
        return cls(email=email, password=password)
    
class UserUpdateSchema(BaseModel):
    fullname: str
    email: EmailStr
    image: Optional[UploadFile] = None  # For uploading a new image

    @classmethod
    def as_form(
        cls,
        fullname: str = Form(...),
        email: EmailStr = Form(...),
        image: Optional[UploadFile] = Form(None),  # Make image optional
    ):
        return cls(fullname=fullname, email=email, image=image)