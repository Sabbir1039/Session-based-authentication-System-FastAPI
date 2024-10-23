import os
import secrets
from fastapi.templating import Jinja2Templates

# Configure template directories    
templates = Jinja2Templates(directory=os.path.join(os.getcwd(), "templates"))

SECRET_KEY = secrets.token_hex(32)
