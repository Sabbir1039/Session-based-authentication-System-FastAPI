import os
import secrets
from fastapi.templating import Jinja2Templates
from pydantic_settings import BaseSettings
from fastapi_mail import ConnectionConfig


class Settings(BaseSettings):
    # Email settings
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    
    class Config:
        env_file = "core_app/.env"  # Use environment variables from a .env file

settings = Settings()

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
)


# Configure template directories    
templates = Jinja2Templates(directory=os.path.join(os.getcwd(), "templates"))

SECRET_KEY = secrets.token_hex(32)