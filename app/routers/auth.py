from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserResponse, Token, LogoutResponse
from app.auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_user,
    oauth2_scheme,
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        201: {"description": "User successfully registered"},
        400: {"description": "Username or email already registered"},
        422: {"description": "Validation error"}
    }
)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    - **username**: Must be unique
    - **email**: Must be a valid email address and unique
    - **password**: User's password (will be hashed)
    """
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user_data.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post(
    "/login",
    response_model=Token,
    summary="Login and get access token",
    responses={
        200: {"description": "Successfully authenticated"},
        401: {"description": "Incorrect username or password"},
        400: {"description": "User account is inactive"}
    }
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and receive JWT access token.
    
    Uses OAuth2 password flow. Returns a Bearer token that should be included
    in the Authorization header for protected endpoints.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout current user",
    responses={
        200: {"description": "Successfully logged out"},
        401: {"description": "Invalid or missing authentication token"}
    }
)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout the current authenticated user.
    
    Note: Token invalidation is handled client-side. The server does not
    maintain a blacklist of tokens.
    """
    return {"message": "Successfully logged out"}

