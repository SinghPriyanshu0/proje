from fastapi import FastAPI, Form, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Text,Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, Column, Integer, String, Date, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.types import DECIMAL
from sqlalchemy import Enum as SQLAlchemyEnum
from passlib.context import CryptContext
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from typing import List
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError
from datetime import date


app = FastAPI()


SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:Oct%402024%23@localhost:3306/hotel_management"


engine = create_engine(SQLALCHEMY_DATABASE_URL)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define SQLAlchemy model for the contact_info table
class ContactInfo(Base):
    __tablename__ = "contact_info"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    email = Column(String(100), unique=True, index=True)
    message = Column(Text)



# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic model for data validation (this model will be used for request/response)
class ContactCreate(BaseModel):
    name: str
    email: str
    message: str

    class Config:
        orm_mode = True  # Tells Pydantic to treat SQLAlchemy models like dictionaries
class RoomBoucher(Base):
    __tablename__ = "room_boucher"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, nullable=False)
    guest_name = Column(String(100), nullable=False)
    booking_date = Column(Date, nullable=False)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    total_amount = Column(Integer, nullable=False)
    room_type = Column(String(50), nullable=False)
    status = Column(SQLAlchemyEnum("Booked", "Checked-in", "Completed", "Cancelled", name="status_enum"), default="Booked")
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", onupdate="CURRENT_TIMESTAMP")

# Create the tables in the database
Base.metadata.create_all(bind=engine)

# Pydantic model for data validation
class RoomBoucherCreate(BaseModel):
    room_id: int
    guest_name: str
    booking_date: str
    check_in_date: str
    check_out_date: str
    total_amount: int
    room_type: str
    status: str

    class Config:
        orm_mode = True

    # Custom JSON encoder to convert datetime.date to string
        json_encoders = {
            date: lambda v: v.isoformat()  # This will convert datetime.date to 'YYYY-MM-DD' string format
        }

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI app
app = FastAPI()

@app.post("/submit_room_boucher", response_model=RoomBoucherCreate)
async def submit_room_boucher(
    room_id: int = Form(...),
    guest_name: str = Form(...),
    booking_date: str = Form(...),
    check_in_date: str = Form(...),
    check_out_date: str = Form(...),
    total_amount: int = Form(...),
    room_type: str = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    # Convert string dates to datetime.date objects
    try:
        booking_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
        check_in_date = datetime.strptime(check_in_date, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(check_out_date, "%Y-%m-%d").date()
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD.")
    
    # Check if the room exists in the room table
    room = db.query(Room).filter(Room.id == room_id).first()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found. Please try another room.")

    if room.status != "Available":
        raise HTTPException(status_code=400, detail="The selected room is not available. Please try another room.")

    # Create a new RoomBoucher record
    new_room_boucher = RoomBoucher(
        room_id=room_id,
        guest_name=guest_name,
        booking_date=booking_date,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        total_amount=total_amount,
        room_type=room_type,
        status=status,
    )

    db.add(new_room_boucher)
    db.commit()
    db.refresh(new_room_boucher)

    # Update the room status to "Occupied"
    room.status = "Occupied"
    db.commit()

    # Convert the datetime.date objects to strings before returning the response
    return {
        "room_id": new_room_boucher.room_id,
        "guest_name": new_room_boucher.guest_name,
        "booking_date": new_room_boucher.booking_date.isoformat(),
        "check_in_date": new_room_boucher.check_in_date.isoformat(),
        "check_out_date": new_room_boucher.check_out_date.isoformat(),
        "total_amount": new_room_boucher.total_amount,
        "room_type": new_room_boucher.room_type,
        "status": new_room_boucher.status,
    }

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# POST endpoint to handle the form submission and store it in the database
@app.post("/submit_contact", response_model=ContactCreate)
async def submit_contact(name: str = Form(...),email: str = Form(...), message: str = Form(...), db: Session = Depends(get_db)):
    # Check if the contact already exists by email (optional)
    db_contact = db.query(ContactInfo).filter(ContactInfo.email == email).first()
    if db_contact:
        raise HTTPException(status_code=400, detail="Contact with this email already exists")

    # Create a new contact record
    new_contact = ContactInfo(name=name, email=email, message=message)

    # Add and commit the new contact
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)

    # Return success response with the stored contact data
    return new_contact


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(15), nullable=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")
# Initialize the password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Route to register a new user using form data
@app.post("/user-register")
async def create_user(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(None),  # Optional field
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if the email is already registered
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password
    hashed_password = hash_password(password)

    # Create a new user record
    new_user = User(
        name=name,
        email=email,
        phone=phone,
        password_hash=hashed_password
    )

    # Add to the session and commit
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully", "user_id": new_user.id}


app.mount("/static", StaticFiles(directory="frontend"), name="static")
# Route to login a user using form data

    
class UserLoginResponse(BaseModel):
    success: bool
    message: str

@app.post("/user-login", response_model=UserLoginResponse)
async def login_user(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    print(f"Attempting login for email: {email}")  # Debugging log

    # Retrieve user from the database by email
    db_user = db.query(User).filter(User.email == email).first()

    if not db_user:
        print(f"User not found: {email}")  # Debugging log
        return JSONResponse(status_code=404, content={"success": False, "message": "User not found"})

    # Verify the password with the stored hash
    if not verify_password(password, db_user.password_hash):
        print(f"Invalid password for user: {email}")  # Debugging log
        return JSONResponse(status_code=401, content={"success": False, "message": "Invalid credentials"})

    # Return success message if credentials are valid
    print(f"Login successful for user: {email}")  # Debugging log
    return JSONResponse(status_code=200, content={"success": True, "message": "Login successful"})


#Admin page designed by me 

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
class Admin(Base):
    __tablename__ = "admin"

    username= Column(Integer, primary_key=True, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")

    
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to verify the password


# Route for admin login
@app.post("/adminlogin")
async def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Retrieve user from the database by email
    db_user = db.query(Admin).filter(Admin.username == username).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify the password with the stored hash
    if not verify_password(password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return RedirectResponse(url="http://127.0.0.1:8000/static/html/inside_admin.html", status_code=303)

# Working for Inside_admin page page




# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fetch all rows from the `contact_info` table
@app.get("/contact_info/")
def fetch_contacts(db=Depends(get_db)):
    contacts = db.query(ContactInfo).order_by(ContactInfo.id).all()
    return contacts

@app.get("/payment_info/")
def fetch_payments(db: Session = Depends(get_db)):
    payments = db.query(Payment).order_by(Payment.id).all()
    # Format the payments into a more suitable structure for the frontend
    formatted_payments = [
        {
            "room_id": payment.room_id, 
            "amount_paid": payment.amount,  
            "payment_method": payment.method, 
            "payment_date": payment.timestamp.isoformat()  
        }
        for payment in payments
    ]
    return formatted_payments
class Room(Base):
    __tablename__ = "room"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    room_number = Column(String(10), unique=True, nullable=False)
    room_type = Column(String(50), nullable=False)
    price_per_night = Column(DECIMAL(10, 2), nullable=False)
    status = Column(Enum("Available", "Occupied", "Maintenance"), default="Available")
    created_at = Column(TIMESTAMP, server_default=func.now())

@app.get("/getrooms/")
def fetch_rooms(db=Depends(get_db)):
    rooms = db.query(Room).order_by(Room.id).all()
    return rooms

@app.get("/getusers/")
def fetch_users(db=Depends(get_db)):
    users = db.query(User).order_by(User.id).all()
    return users
class PaymentMethod(PyEnum):
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    CASH = "Cash"
    ONLINE = "Online"

# Now in your SQLAlchemy model, you can use this enum as follows
from sqlalchemy import Column, Integer, Enum as SqlEnum
# Payment model to interact with the payment table
class Payment(Base):
    __tablename__ = 'payment'

    id = Column(Integer, primary_key=True, index=True)
    room_boucher_id = Column(Integer, ForeignKey('room_boucher.id', ondelete="CASCADE"))
    amount_paid = Column(Float)  # Correctly using Column(Float)
    payment_date = Column(TIMESTAMP, default=datetime.utcnow)
    payment_method = Column(Enum(PaymentMethod))  # Enum for payment method

# Pydantic model for the payment input validation
class PaymentCreate(BaseModel):
    room_boucher_id: int
    amount_paid: float
    payment_method: PaymentMethod

    class Config:
        orm_mode = True

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API route for submitting payment
@app.post("/submit_payment", response_model=PaymentCreate)
async def submit_payment(
    room_boucher_id: int = Form(...),
    amount_paid: float = Form(...),
    payment_method: str = Form(...),
    db: Session = Depends(get_db)
):
    # Step 1: Check if the room_boucher exists
    room_boucher = db.query(RoomBoucher).filter(RoomBoucher.id == room_boucher_id).first()
    if not room_boucher:
        raise HTTPException(status_code=404, detail="Room Boucher not found")

    # Step 2: Insert payment details into the payment table
    new_payment = Payment(
        room_boucher_id=room_boucher_id,
        amount_paid=amount_paid,
        payment_method=payment_method
    )

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    # Step 3: Get the associated room using the foreign key in room_boucher
    room = db.query(Room).filter(Room.id == room_boucher.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Step 4: Update the room's status to "Available" if it was "Occupied"
    if room.status.value == "Occupied":
        room.status= "Available"
        db.commit()  # Save the changes to the room status

    return new_payment


class RoomStatus(PyEnum):
    AVAILABLE = "Available"
    OCCUPIED = "Occupied"
    MAINTENANCE = "Maintenance"


# Room Status Update Request Model
class RoomStatusUpdate(BaseModel):
    status: RoomStatus

    class Config:
        orm_mode = True

# Update Room Status Endpoint using PATCH
@app.patch("/rooms/{room_id}/status", response_model=RoomStatusUpdate)
async def update_room_status(
    room_id: int,
    status_update: RoomStatusUpdate,
    db: Session = Depends(get_db)
):
    # Fetch the room by its ID
    room = db.query(Room).filter(Room.id == int(room_id)).first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Validate status
    if status_update.status not in RoomStatus:
        raise HTTPException(status_code=400, detail="Invalid status value")
    
    # Update the room's status
    room.status = status_update.status.value 
    db.commit()
    db.refresh(room)
    
    return room  # Return updated room status




