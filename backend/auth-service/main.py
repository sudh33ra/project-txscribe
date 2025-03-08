from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional, Dict
from shared.database import Database
from app.models.user import UserModel, UserService

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
SECRET_KEY = "your-secret-key"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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
async def register(
    email: str = Body(...),
    password: str = Body(...),
    name: str = Body(...),
) -> Dict:
    """
    Register a new user
    """
    try:
        db = await Database.get_db()
        user_service = UserService(db)
        
        # Check if user already exists
        existing_user = await user_service.get_user_by_email(email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash the password
        password_hash = pwd_context.hash(password)
        
        # Create new user with timestamps
        current_time = datetime.utcnow()
        user = UserModel(
            email=email,
            password_hash=password_hash,
            name=name,
            created_at=current_time,
            updated_at=current_time
        )
        
        user_id = await user_service.create_user(user)
        return {"user_id": str(user_id), "message": "User registered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        db = await Database.get_db()
        user_service = UserService(db)
        
        user = await user_service.get_user_by_email(form_data.username)
        if not user:
            raise HTTPException(status_code=400, detail="Incorrect email or password")
            
        if not pwd_context.verify(form_data.password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Incorrect email or password")
            
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"]},
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
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