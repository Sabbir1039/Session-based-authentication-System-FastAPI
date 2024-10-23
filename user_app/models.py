from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fullname: str = Field(index=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    hashed_password: str
    image: Optional[str] = Field(default="images/profile_pics/profile.jpg") # will store image path

    # New fields for password reset token and expiry
    reset_token: Optional[str] = None
    token_expiry: Optional[datetime] = None