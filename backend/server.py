from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    user_type: str = "client"  # "employer" or "client"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    user_type: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Token(BaseModel):
    access_token: str
    token_type: str

class SubscriptionPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    days: int
    price_ars: int
    description: str

class Calendar(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employer_id: str
    calendar_name: str
    business_name: str
    description: str
    url_slug: str
    is_active: bool = True
    subscription_expires: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CalendarCreate(BaseModel):
    calendar_name: str
    business_name: str
    description: str
    url_slug: str

class WorkingHours(BaseModel):
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: str  # HH:MM format
    end_time: str    # HH:MM format

class CalendarSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    calendar_id: str
    working_hours: List[WorkingHours] = []
    blocked_dates: List[str] = []  # ISO date strings
    blocked_weekends: bool = False
    blocked_days: List[int] = []  # Days of week to block (0-6)
    appointment_duration: int = 60  # minutes
    buffer_time: int = 0  # minutes between appointments

class CalendarSettingsCreate(BaseModel):
    working_hours: List[WorkingHours] = []
    blocked_dates: List[str] = []
    blocked_weekends: bool = False
    blocked_days: List[int] = []
    appointment_duration: int = 60
    buffer_time: int = 0

class Appointment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    calendar_id: str
    client_id: str
    client_name: str
    client_email: str
    appointment_date: str  # ISO date string
    appointment_time: str  # HH:MM format
    status: str = "confirmed"  # "confirmed", "cancelled", "completed"
    notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AppointmentCreate(BaseModel):
    appointment_date: str
    appointment_time: str
    notes: str = ""

class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    calendar_id: str
    plan_id: str
    employer_id: str
    status: str = "pending"  # "pending", "active", "expired", "cancelled"
    starts_at: datetime
    expires_at: datetime
    mercadopago_payment_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MercadoPagoSettings(BaseModel):
    access_token: str
    public_key: str

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise credentials_exception
    return User(**user)

def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, dict):
                data[key] = prepare_for_mongo(value)
            elif isinstance(value, list):
                data[key] = [prepare_for_mongo(item) if isinstance(item, dict) else item for item in value]
    return data

def parse_from_mongo(item):
    """Parse datetime strings back from MongoDB"""
    if isinstance(item, dict):
        for key, value in item.items():
            if isinstance(value, str) and key.endswith(('_at', 'expires', 'starts')):
                try:
                    item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    pass
    return item

# Initialize subscription plans
@app.on_event("startup")
async def startup_event():
    # Create default subscription plans
    default_plans = [
        {"name": "Plan 30 días", "days": 30, "price_ars": 30000, "description": "Acceso completo por 30 días"},
        {"name": "Plan 60 días", "days": 60, "price_ars": 50000, "description": "Acceso completo por 60 días"},
        {"name": "Plan 90 días", "days": 90, "price_ars": 70000, "description": "Acceso completo por 90 días"},
        {"name": "Plan 180 días", "days": 180, "price_ars": 120000, "description": "Acceso completo por 6 meses"}
    ]
    
    for plan_data in default_plans:
        existing = await db.subscription_plans.find_one({"name": plan_data["name"]})
        if not existing:
            plan = SubscriptionPlan(**plan_data)
            await db.subscription_plans.insert_one(prepare_for_mongo(plan.dict()))

# Auth routes
@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user_dict = user_data.dict()
    user = User(**user_dict)
    
    # Store user with password in database
    user_with_password = user.dict()
    user_with_password["password"] = hashed_password
    
    await db.users.insert_one(prepare_for_mongo(user_with_password))
    return user

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# Calendar routes
@api_router.post("/calendars", response_model=Calendar)
async def create_calendar(calendar_data: CalendarCreate, current_user: User = Depends(get_current_user)):
    if current_user.user_type != "employer":
        raise HTTPException(status_code=403, detail="Only employers can create calendars")
    
    # Check if URL slug is unique
    existing = await db.calendars.find_one({"url_slug": calendar_data.url_slug})
    if existing:
        raise HTTPException(status_code=400, detail="URL slug already exists")
    
    calendar_dict = calendar_data.dict()
    calendar_dict["employer_id"] = current_user.id
    calendar = Calendar(**calendar_dict)
    
    await db.calendars.insert_one(prepare_for_mongo(calendar.dict()))
    
    # Create default settings
    settings = CalendarSettings(calendar_id=calendar.id)
    await db.calendar_settings.insert_one(prepare_for_mongo(settings.dict()))
    
    return calendar

@api_router.get("/calendars", response_model=List[Calendar])
async def get_user_calendars(current_user: User = Depends(get_current_user)):
    if current_user.user_type == "employer":
        calendars = await db.calendars.find({"employer_id": current_user.id}).to_list(100)
    else:
        calendars = await db.calendars.find({"is_active": True}).to_list(100)
    
    return [Calendar(**parse_from_mongo(cal)) for cal in calendars]

@api_router.get("/calendars/{url_slug}", response_model=Calendar)
async def get_calendar_by_slug(url_slug: str):
    calendar = await db.calendars.find_one({"url_slug": url_slug, "is_active": True})
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    return Calendar(**parse_from_mongo(calendar))

# Calendar settings routes
@api_router.put("/calendars/{calendar_id}/settings")
async def update_calendar_settings(calendar_id: str, settings_data: CalendarSettingsCreate, current_user: User = Depends(get_current_user)):
    calendar = await db.calendars.find_one({"id": calendar_id, "employer_id": current_user.id})
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found or not authorized")
    
    settings_dict = settings_data.dict()
    settings_dict["calendar_id"] = calendar_id
    
    await db.calendar_settings.update_one(
        {"calendar_id": calendar_id},
        {"$set": prepare_for_mongo(settings_dict)},
        upsert=True
    )
    return {"message": "Settings updated successfully"}

@api_router.get("/calendars/{calendar_id}/settings")
async def get_calendar_settings(calendar_id: str):
    settings = await db.calendar_settings.find_one({"calendar_id": calendar_id})
    if not settings:
        # Return default settings
        default_settings = CalendarSettings(calendar_id=calendar_id)
        return default_settings.dict()
    return settings

# Appointments routes
@api_router.post("/calendars/{calendar_id}/appointments", response_model=Appointment)
async def create_appointment(calendar_id: str, appointment_data: AppointmentCreate, current_user: User = Depends(get_current_user)):
    calendar = await db.calendars.find_one({"id": calendar_id, "is_active": True})
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    
    # Check if slot is available
    existing = await db.appointments.find_one({
        "calendar_id": calendar_id,
        "appointment_date": appointment_data.appointment_date,
        "appointment_time": appointment_data.appointment_time,
        "status": {"$ne": "cancelled"}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Time slot not available")
    
    appointment_dict = appointment_data.dict()
    appointment_dict.update({
        "calendar_id": calendar_id,
        "client_id": current_user.id,
        "client_name": current_user.full_name,
        "client_email": current_user.email
    })
    
    appointment = Appointment(**appointment_dict)
    await db.appointments.insert_one(prepare_for_mongo(appointment.dict()))
    return appointment

@api_router.get("/calendars/{calendar_id}/appointments", response_model=List[Appointment])
async def get_calendar_appointments(calendar_id: str, current_user: User = Depends(get_current_user)):
    # Check authorization
    calendar = await db.calendars.find_one({"id": calendar_id})
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    
    # Employers can see all appointments, clients only their own
    if current_user.user_type == "employer" and calendar["employer_id"] == current_user.id:
        appointments = await db.appointments.find({"calendar_id": calendar_id}).to_list(1000)
    else:
        appointments = await db.appointments.find({
            "calendar_id": calendar_id,
            "client_id": current_user.id
        }).to_list(1000)
    
    return [Appointment(**parse_from_mongo(apt)) for apt in appointments]

# Subscription plans routes
@api_router.get("/subscription-plans", response_model=List[SubscriptionPlan])
async def get_subscription_plans():
    plans = await db.subscription_plans.find().to_list(100)
    return [SubscriptionPlan(**plan) for plan in plans]

# MercadoPago settings routes
@api_router.post("/mercadopago/settings")
async def save_mercadopago_settings(settings: MercadoPagoSettings, current_user: User = Depends(get_current_user)):
    if current_user.user_type != "employer":
        raise HTTPException(status_code=403, detail="Only employers can configure MercadoPago")
    
    await db.mercadopago_settings.update_one(
        {"employer_id": current_user.id},
        {"$set": {"employer_id": current_user.id, **settings.dict()}},
        upsert=True
    )
    return {"message": "MercadoPago settings saved successfully"}

@api_router.get("/mercadopago/settings")
async def get_mercadopago_settings(current_user: User = Depends(get_current_user)):
    if current_user.user_type != "employer":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    settings = await db.mercadopago_settings.find_one({"employer_id": current_user.id})
    if not settings:
        return {"access_token": "", "public_key": ""}
    
    return {"access_token": "***", "public_key": settings.get("public_key", "")}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()