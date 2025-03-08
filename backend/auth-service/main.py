from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional, Dict
from shared.database import Database
from app.models.user import UserModel, UserService
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Auth Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-123")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

@app.on_event("startup")
async def startup_db_client():
    await Database.connect_db()

@app.on_event("shutdown")
async def shutdown_db_client():
    await Database.close_db()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/auth/register")
async def register_user(user: UserModel):
    try:
        logger.info(f"Attempting to register user: {user.email}")
        db = await Database.get_db()
        user_service = UserService(db)
        
        # Check if user already exists
        existing_user = await user_service.get_user_by_email(user.email)
        if existing_user:
            logger.info(f"User already exists: {user.email}")
            raise HTTPException(
                status_code=400,
                detail="User already registered"
            )
            
        current_time = datetime.utcnow()
        # Create user document with required fields
        user_dict = {
            "email": user.email,
            "password_hash": pwd_context.hash(user.password),
            "name": user.name,
            "created_at": current_time,  # Required by schema
            "updated_at": current_time
        }
        
        # Create the user
        user_id = await user_service.create_user_dict(user_dict)
        logger.info(f"Successfully registered user: {user.email}")
        
        return {"user_id": str(user_id)}
        
    except HTTPException as e:
        logger.error(f"Registration failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        logger.info(f"Attempting login for user: {form_data.username}")
        db = await Database.get_db()
        user_service = UserService(db)
        
        user = await user_service.get_user_by_email(form_data.username)
        logger.info(f"Found user document: {user}")
        
        if not user:
            logger.error(f"User not found: {form_data.username}")
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password"
            )
            
        stored_password = user.get("password_hash")
        if not stored_password:
            logger.error("No password hash found in user document")
            raise HTTPException(
                status_code=500,
                detail="Invalid user data"
            )
            
        if not pwd_context.verify(form_data.password, stored_password):
            logger.error("Invalid password")
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password"
            )
            
        access_token = create_access_token(
            data={"sub": str(user["_id"])},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        logger.info(f"Login successful for user: {form_data.username}")
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/me")
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
            
        db = await Database.get_db()
        user_service = UserService(db)
        user = await user_service.get_user_by_email(email)
        
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
            
        return {
            "email": user["email"],
            "name": user["name"]
        }
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 