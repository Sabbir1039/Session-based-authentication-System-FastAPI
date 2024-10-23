from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import RedirectResponse
from user_app.schemas import (
    RegisterSchema,
    LoginSchema,
    UserUpdateSchema,
    PasswordResetRequestSchema,
    PasswordResetConfirmSchema
    )
from user_app.auth import get_password_hash, verify_password, generate_reset_token
from user_app.models import User
from sqlmodel import select, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from core_app.database import get_session as db_session
from core_app.config import templates, conf
from datetime import datetime, timedelta
import os
from fastapi_mail import FastMail, MessageSchema

router = APIRouter()

@router.get("/register")
async def register_page(request: Request):
    
    # checks if user already logged in
    user_session = request.session.get("user_id");
    if user_session:
        return RedirectResponse(url="/", status_code=303)
    
    return templates.TemplateResponse("user_app/register.html", {"request": request})

@router.post("/register")
async def register(request: Request,
                   user: RegisterSchema = Depends(RegisterSchema.as_form),
                   session: Session = Depends(db_session)
                   ):
    
    try:
        # Check if the email is already registered
        user_in_db = session.exec(select(User).where(User.email == user.email)).first()
        if user_in_db:
            return templates.TemplateResponse(
                "user_app/register.html",
                {
                    "request": request,
                    "error": "Email already registered"
                }
                )
        # Hash the user's password
        hashed_password = get_password_hash(user.password)

        # Create a new user instance and save to the database
        new_user = User(fullname= user.name, email=user.email, hashed_password=hashed_password)
        session.add(new_user)
        session.commit()
        
    except IntegrityError:
        session.rollback()  # Rollback the session in case of failure
        return templates.TemplateResponse(
            "user_app/register.html",
            {"request": request, "error": "Integrity Error - possible duplicate entry"}
        )
        
    except SQLAlchemyError as e:
        session.rollback()
        return templates.TemplateResponse(
            "user_app/register.html",
            {"request": request, "error": "Database Error"}
        )

    return RedirectResponse(url="/users/login?message=User registered successfully", status_code=303)


@router.get("/login")
async def login_page(request: Request):
    
    # checks if user already logged in
    user_session = request.session.get("user_id");
    if user_session:
        return RedirectResponse(url="/", status_code=303)
    
    message = request.query_params.get("message")
    return templates.TemplateResponse("user_app/login.html", { "request": request, "message": message })


@router.post("/login")
async def login(request: Request,
                response: Response,
                credentials: LoginSchema = Depends(LoginSchema.as_form),
                session: Session = Depends(db_session)):
    
    try:
        user_in_db = session.exec(select(User).where(User.email == credentials.email)).first()
        
        # Check if user exists and verify password
        if not user_in_db or not verify_password(credentials.password, user_in_db.hashed_password):
            return templates.TemplateResponse(
                "user_app/login.html",
                {
                    "request": request,
                    "error": "Invalid credentials"
                }
            )

        # Set the user_id in the session after successful login
        request.session["user_id"] = user_in_db.id

        return RedirectResponse(url="/", status_code=303)

    except SQLAlchemyError as e:
        return templates.TemplateResponse(
            "user_app/login.html",
            {
                "request": request,
                "error": "Database error occurred during login. Please try again later."
            }
        )


@router.get("/logout")
async def logout_page(request: Request):
    user_session = request.session.get("user_id")
    if not user_session:
        return RedirectResponse(url="/users/login?message=Login first!", status_code=303)
    return templates.TemplateResponse("user_app/logout.html", { "request": request })



@router.post("/logout")
async def logout(request: Request, response: Response):
    request.session.clear()
    return RedirectResponse(url="/users/login?message=User logged out successfully", status_code=303)



@router.get("/profile")
async def profile_page(request: Request, session: Session = Depends(db_session)):
    try:
        # Fetch user_id from session
        user_session = request.session.get("user_id")
        if not user_session:
            return RedirectResponse(url="/users/login?message=Login to visit profile page!", status_code=303)
        
        # Fetch user from database
        user_in_db = session.exec(select(User).where(User.id == user_session)).first()
        
        # Check if user exists in the database
        if not user_in_db:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare user data for template
        user = {
            "username": user_in_db.fullname,
            "email": user_in_db.email,
            "image": user_in_db.image or "images/profile_pics/default.jpg"  # Default image if none
        }
        
        # Render profile page with user data
        return templates.TemplateResponse("user_app/profile.html", {"request": request, "user": user})
    
    except HTTPException as http_err:
        raise http_err  # Re-raise any specific HTTP exceptions
    
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")




@router.get("/profile/update")
async def update_profile_page(
    request: Request,
    session: Session = Depends(db_session),
):
    try:
        # Get the user ID from the session
        user_id = request.session.get("user_id")
        if not user_id:
            return RedirectResponse(url="/users/login?message=Login to visit profile update page!", status_code=303)
        
        # Fetch the user from the database
        user_in_db = session.exec(select(User).where(User.id == user_id)).first()
        
        # If user not found, redirect to homepage
        if not user_in_db:
            return RedirectResponse(url="/", status_code=303)
        
        # Prepare user data for the template
        user = {
            "fullname": user_in_db.fullname,
            "email": user_in_db.email,
        }

        # Render the profile update template with user data
        return templates.TemplateResponse("user_app/profile_update.html", {"request": request, "user": user})

    except HTTPException as http_err:
        raise http_err
    
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    


@router.post("/profile/update")
async def update_profile(
    request: Request,
    user_update: UserUpdateSchema = Depends(UserUpdateSchema.as_form),
    session: Session = Depends(db_session),
):
    try:
        user_id = request.session.get("user_id")
        if not user_id:
            return RedirectResponse(url="/", status_code=303)
        
        user_in_db = session.exec(select(User).where(User.id == user_id)).first()
        if not user_in_db:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user details
        user_in_db.fullname = user_update.fullname
        user_in_db.email = user_update.email
        
        # Handle image upload
        if user_update.image and user_update.image.filename:
            # Ensure the image directory exists
            image_dir = "static/images/profile_pics"
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Get the current timestamp
            original_filename = user_update.image.filename.rsplit(".", 1)[0]  # Extract original filename
            file_extension = user_update.image.filename.split(".")[-1]  # Extract file extension

            # Construct new filename
            new_filename = f"profile_{timestamp}_{original_filename}.{file_extension}"
            image_path = f"images/profile_pics/{new_filename}"
            
            # Save the image to the server
            with open(f"static/{image_path}", "wb") as image_file:
                content = await user_update.image.read()
                image_file.write(content)
            
            # Update the user image path in the database
            user_in_db.image = image_path

        session.add(user_in_db)
        session.commit()

        return RedirectResponse(url="/users/profile", status_code=303)
    
    except HTTPException as http_err:
        raise http_err
    
    except OSError as os_err:
        print(f"File system error occurred: {os_err}")
        raise HTTPException(status_code=500, detail="An error occurred while saving the image.")
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during profile update.")


# password reset
# Send password reset email
@router.post("/password-reset/request")
async def password_reset_request(
    request: PasswordResetRequestSchema,
    session: Session = Depends(db_session)
    ):
    
    email = request.email
    user_in_db = session.exec(select(User).where(User.email == email)).first()
    if not user_in_db:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate a token and store it with an expiry time
    reset_token = generate_reset_token()
    token_expiry = datetime.utcnow() + timedelta(minutes=30)  # Token valid for 30 minutes

    user_in_db.reset_token = reset_token
    user_in_db.token_expiry = token_expiry
    
    session.commit()

    # Send email with reset link (token in query parameters)
    reset_url = f"http://localhost:8000/password-reset/confirm?token={reset_token}"
    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body=f"Click the following link to reset your password: {reset_url}",
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)

    return {"msg": "Password reset email sent"}

# Verify the token and allow password reset
@router.post("/password-reset/confirm")
async def password_reset_confirm(
    credentials: PasswordResetConfirmSchema,
    session: Session = Depends(db_session)
    ):
    
    # Find the user with the matching token
    user_in_db = session.exec(select(User).where(User.reset_token == credentials.token)).first()
    
    if not user_in_db or datetime.utcnow() > user_in_db.token_expiry:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    # Update password
    user_in_db.hashed_password = get_password_hash(credentials.new_password)
    
    # Clear reset token
    user_in_db.reset_token = None
    user_in_db.token_expiry = None
    
    session.commit()

    return {"msg": "Password successfully reset"}