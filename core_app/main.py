from fastapi import FastAPI, Request, Depends
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from core_app.database import create_db_and_tables, get_session
from core_app.config import templates
from core_app.config import SECRET_KEY
from user_app.views import router as user_router
from user_app.models import User


app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    
# Add SessionMiddleware to the app
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="session_id",
    max_age=3600
)

# Mount routers
app.include_router(user_router, prefix="/users", tags=["Users"])

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Home route (main app)
@app.get("/")
async def home_page(request: Request, session: Session = Depends(get_session)):
    user_id = request.session.get("user_id")
    user = session.exec(select(User).where(User.id == user_id)).first()
    if user:
        user = user.fullname
    return templates.TemplateResponse(
        "core_app/home.html", 
        {"request": request, "user": user}
    )
