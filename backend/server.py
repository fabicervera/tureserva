from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone, date
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

# Free license settings
LICENCE_FREE = int(os.environ.get("LICENCE_FREE", "1"))
DAY_FREE = int(os.environ.get("DAY_FREE", "30"))

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Enhanced Models
class Location(BaseModel):
    country: str = "argentina"
    province: str
    city: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    user_type: str = "client"  # "employer" or "client"
    location: Location

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    user_type: str
    location: Location
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

class TimeRange(BaseModel):
    start_time: str  # HH:MM format
    end_time: str    # HH:MM format

class WorkingHours(BaseModel):
    day_of_week: int  # 0=Monday, 6=Sunday
    time_ranges: List[TimeRange] = []  # Multiple time ranges per day

class SpecificDateHours(BaseModel):
    date: str  # ISO date string (YYYY-MM-DD)
    time_ranges: List[TimeRange] = []  # Time ranges for this specific date

class Calendar(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employer_id: str
    calendar_name: str
    business_name: str
    description: str
    url_slug: str
    category: str = "general"  # For organizing calendars
    location: Location
    is_active: bool = True
    subscription_expires: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CalendarCreate(BaseModel):
    calendar_name: str
    business_name: str
    description: str
    url_slug: str
    category: str = "general"

class CalendarSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    calendar_id: str
    working_hours: List[WorkingHours] = []
    specific_date_hours: List[SpecificDateHours] = []  # Special hours for specific dates
    blocked_dates: List[str] = []  # ISO date strings
    blocked_saturdays: bool = False
    blocked_sundays: bool = False
    appointment_duration: int = 60  # minutes
    buffer_time: int = 0  # minutes between appointments

class CalendarSettingsCreate(BaseModel):
    working_hours: List[WorkingHours] = []
    specific_date_hours: List[SpecificDateHours] = []
    blocked_dates: List[str] = []
    blocked_saturdays: bool = False
    blocked_sundays: bool = False
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

class Friendship(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    employer_id: str
    status: str = "pending"  # "pending", "accepted", "blocked"
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    responded_at: Optional[datetime] = None

class FriendshipRequest(BaseModel):
    employer_id: str

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

def create_free_subscription(employer_id: str, calendar_id: str):
    """Create a free subscription for new employers"""
    if LICENCE_FREE:
        starts_at = datetime.now(timezone.utc)
        expires_at = starts_at + timedelta(days=DAY_FREE)
        
        return Subscription(
            calendar_id=calendar_id,
            plan_id="free-trial",
            employer_id=employer_id,
            status="active",
            starts_at=starts_at,
            expires_at=expires_at
        )
    return None

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
    user_dict["password"] = hashed_password
    user = User(**user_dict)
    
    # Store user with password in database
    user_dict_with_password = user.dict()
    user_dict_with_password["password"] = hashed_password
    await db.users.insert_one(prepare_for_mongo(user_dict_with_password))
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
    calendar_dict["location"] = current_user.location.dict()  # Inherit employer's location
    calendar = Calendar(**calendar_dict)
    
    await db.calendars.insert_one(prepare_for_mongo(calendar.dict()))
    
    # Create default settings
    settings = CalendarSettings(calendar_id=calendar.id)
    await db.calendar_settings.insert_one(prepare_for_mongo(settings.dict()))
    
    # Create free subscription if enabled
    if LICENCE_FREE:
        free_sub = create_free_subscription(current_user.id, calendar.id)
        if free_sub:
            await db.subscriptions.insert_one(prepare_for_mongo(free_sub.dict()))
            # Update calendar with subscription expiry
            calendar.subscription_expires = free_sub.expires_at
            await db.calendars.update_one(
                {"id": calendar.id},
                {"$set": {"subscription_expires": free_sub.expires_at.isoformat()}}
            )
    
    return calendar

@api_router.get("/calendars", response_model=List[Calendar])
async def get_calendars(
    current_user: User = Depends(get_current_user),
    search: Optional[str] = None,
    category: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None
):
    query = {}
    
    if current_user.user_type == "employer":
        query["employer_id"] = current_user.id
    else:
        # For clients, show only active calendars with valid subscriptions from their location
        query["is_active"] = True
        # Filter by location
        if not province and not city:
            # Default to user's location
            query["location.province"] = current_user.location.province
            if current_user.location.city:
                query["location.city"] = current_user.location.city
        else:
            if province:
                query["location.province"] = province
            if city:
                query["location.city"] = city
        
        # Only show calendars with active subscriptions
        current_time = datetime.now(timezone.utc).isoformat()
        query["subscription_expires"] = {"$gte": current_time}
    
    # Add search filters
    if search:
        search_regex = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"calendar_name": search_regex},
            {"business_name": search_regex},
            {"description": search_regex}
        ]
    
    if category:
        query["category"] = category
    
    calendars = await db.calendars.find(query).to_list(100)
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
    
    # Validate that blocked dates are not in the past
    today = date.today().isoformat()
    for blocked_date in settings_data.blocked_dates:
        if blocked_date < today:
            raise HTTPException(status_code=400, detail=f"Cannot block past date: {blocked_date}")
    
    # Validate specific date hours are not in the past
    for specific_date in settings_data.specific_date_hours:
        if specific_date.date < today:
            raise HTTPException(status_code=400, detail=f"Cannot set hours for past date: {specific_date.date}")
    
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
    
    # Remove MongoDB ObjectId and return clean data
    if '_id' in settings:
        del settings['_id']
    return settings

# Friendship system
@api_router.post("/friendships/request")
async def request_friendship(request_data: FriendshipRequest, current_user: User = Depends(get_current_user)):
    if current_user.user_type != "client":
        raise HTTPException(status_code=403, detail="Only clients can request friendships")
    
    # Check if employer exists
    employer = await db.users.find_one({"id": request_data.employer_id, "user_type": "employer"})
    if not employer:
        raise HTTPException(status_code=404, detail="Employer not found")
    
    # Check if friendship already exists
    existing = await db.friendships.find_one({
        "client_id": current_user.id,
        "employer_id": request_data.employer_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Friendship request already exists")
    
    friendship = Friendship(
        client_id=current_user.id,
        employer_id=request_data.employer_id
    )
    
    await db.friendships.insert_one(prepare_for_mongo(friendship.dict()))
    return {"message": "Friendship request sent successfully"}

@api_router.get("/friendships/requests")
async def get_friendship_requests(current_user: User = Depends(get_current_user)):
    if current_user.user_type != "employer":
        raise HTTPException(status_code=403, detail="Only employers can view friendship requests")
    
    requests = await db.friendships.find({
        "employer_id": current_user.id,
        "status": "pending"
    }).to_list(100)
    
    # Get client info for each request
    result = []
    for req in requests:
        client = await db.users.find_one({"id": req["client_id"]})
        if client:
            result.append({
                "id": req["id"],
                "client": {
                    "id": client["id"],
                    "full_name": client["full_name"],
                    "email": client["email"],
                    "location": client["location"]
                },
                "requested_at": req["requested_at"]
            })
    
    return result

@api_router.post("/friendships/{friendship_id}/respond")
async def respond_to_friendship(friendship_id: str, accept: bool, current_user: User = Depends(get_current_user)):
    if current_user.user_type != "employer":
        raise HTTPException(status_code=403, detail="Only employers can respond to friendship requests")
    
    friendship = await db.friendships.find_one({
        "id": friendship_id,
        "employer_id": current_user.id,
        "status": "pending"
    })
    
    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship request not found")
    
    new_status = "accepted" if accept else "blocked"
    await db.friendships.update_one(
        {"id": friendship_id},
        {"$set": {
            "status": new_status,
            "responded_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": f"Friendship request {'accepted' if accept else 'rejected'}"}

# Appointments routes
@api_router.post("/calendars/{calendar_id}/appointments", response_model=Appointment)
async def create_appointment(calendar_id: str, appointment_data: AppointmentCreate, current_user: User = Depends(get_current_user)):
    calendar = await db.calendars.find_one({"id": calendar_id, "is_active": True})
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    
    # Check if friendship exists (client-employer relationship)
    if current_user.user_type == "client":
        friendship = await db.friendships.find_one({
            "client_id": current_user.id,
            "employer_id": calendar["employer_id"],
            "status": "accepted"
        })
        if not friendship:
            raise HTTPException(status_code=403, detail="You need to be accepted as a friend to book appointments")
    
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

@api_router.get("/calendars/{calendar_id}/available-slots")
async def get_available_slots(calendar_id: str, date: str):
    """Get available time slots for a specific date"""
    calendar = await db.calendars.find_one({"id": calendar_id, "is_active": True})
    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    
    settings = await db.calendar_settings.find_one({"calendar_id": calendar_id})
    if not settings:
        return []
    
    # Parse the date
    try:
        target_date = datetime.fromisoformat(date).date()
        day_of_week = target_date.weekday()  # 0=Monday, 6=Sunday
    except:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Check if date is blocked
    if date in settings.get("blocked_dates", []):
        return []
    
    # Check weekend blocks
    if day_of_week == 5 and settings.get("blocked_saturdays", False):  # Saturday
        return []
    if day_of_week == 6 and settings.get("blocked_sundays", False):   # Sunday
        return []
    
    # Get time ranges for this date
    time_ranges = []
    
    # First priority: specific date hours
    specific_hours = None
    for spec_date in settings.get("specific_date_hours", []):
        if spec_date["date"] == date:
            specific_hours = spec_date["time_ranges"]
            break
    
    if specific_hours:
        time_ranges = specific_hours
    else:
        # Second priority: regular weekly hours
        for working_hours in settings.get("working_hours", []):
            if working_hours["day_of_week"] == day_of_week:
                time_ranges = working_hours.get("time_ranges", [])
                break
    
    if not time_ranges:
        return []
    
    # Generate available slots
    available_slots = []
    appointment_duration = settings.get("appointment_duration", 60)
    buffer_time = settings.get("buffer_time", 0)
    
    for time_range in time_ranges:
        start_time = datetime.strptime(time_range["start_time"], "%H:%M").time()
        end_time = datetime.strptime(time_range["end_time"], "%H:%M").time()
        
        current_time = datetime.combine(target_date, start_time)
        end_datetime = datetime.combine(target_date, end_time)
        
        while current_time + timedelta(minutes=appointment_duration) <= end_datetime:
            slot_time = current_time.strftime("%H:%M")
            
            # Check if slot is already booked
            existing_appointment = await db.appointments.find_one({
                "calendar_id": calendar_id,
                "appointment_date": date,
                "appointment_time": slot_time,
                "status": {"$ne": "cancelled"}
            })
            
            if not existing_appointment:
                available_slots.append(slot_time)
            
            current_time += timedelta(minutes=appointment_duration + buffer_time)
    
    return sorted(available_slots)

# Location routes
@api_router.get("/locations")
async def get_locations():
    """Get available locations"""
    try:
        locations_path = Path(__file__).parent.parent / "frontend" / "src" / "data" / "locations.json"
        with open(locations_path, 'r', encoding='utf-8') as f:
            locations = json.load(f)
        return locations
    except FileNotFoundError:
        return {"argentina": {"name": "Argentina", "provinces": {}}}

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