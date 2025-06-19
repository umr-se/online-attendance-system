from datetime import date, datetime, timezone
from fastapi import FastAPI, Depends, Form, HTTPException, Query, status
from jose import JWTError
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app import models, schemas, crud, google_sheets, auth
from app.database import Base, engine, SessionLocal
from app.database import Base, engine, get_db
from app.auth import create_access_token, decode_token
from fastapi.middleware.cors import CORSMiddleware
from app import models, schemas, crud, google_sheets, auth
from app.auth import get_password_hash
from app.models import User
from dotenv import load_dotenv
import os
from fastapi import WebSocket, WebSocketDisconnect
from typing import List

Base.metadata.create_all(bind=engine)
load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

@app.on_event("startup")
def on_startup():
    # Disable foreign key checks
    with engine.connect() as connection:
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    
    # Re-enable foreign key checks
    with engine.connect() as connection:
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    
    # Create new tables
    Base.metadata.create_all(bind=engine)
    
    create_default_admin()
    verify_google_credentials()
    
@app.get('/' ,tags = ['Home'])
async def root():
    return{"Welcome!!"}
    
    
def verify_google_credentials():    
    from app import google_sheets
    print("\n--- Environment Variables ---")
    print(f"GOOGLE_CREDENTIALS_FILE: {os.getenv('GOOGLE_CREDENTIALS_FILE')}")
    print(f"SPREADSHEET_ID: {os.getenv('SPREADSHEET_ID')}")
    print(f"SPREADSHEET_NAME: {os.getenv('SPREADSHEET_NAME')}")
    print("-----------------------------\n")

def create_default_admin():
    db = SessionLocal()
    try:
        admin_email = "admin@example.com"
        existing_admin = crud.get_user_by_email(db, admin_email)
        if not existing_admin:
            admin = User(
                name="Admin",
                email=admin_email,
                password=auth.get_password_hash("pass123"),
                qr_code="1111",
                role="admin"
            )
            db.add(admin)
            db.commit()
            print("Default admin created.")
    except Exception as e:
        print(f"Error creating admin: {str(e)}")
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        token_data = decode_token(token)
        if not token_data or not token_data.email:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = crud.get_user_by_email(db, token_data.email)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:  # Add this import at the top: from jose import JWTError
        raise HTTPException(status_code=401, detail="Invalid token")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()


def get_leave_requests(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    all: bool = False
):
    """
    Get leave requests
    - Regular users: only their own requests
    - Admins: all requests if 'all=true' parameter provided
    """
    if user.role == "admin" and all:
        return crud.get_leave_requests(db)
    return crud.get_leave_requests(db, user.id)

# Add WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        
@app.post("/register", response_model=schemas.UserOut, tags=['User'])
def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Create user with default values
    user_data = schemas.UserCreate(
        name=name,
        email=email,
        password=password,
        role="user",       # Default role
        qr_code="0000"     # Default QR code
    )
    
    db_user = crud.get_user_by_email(db, email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    return crud.create_user(db, user_data)

@app.post("/token", response_model=schemas.Token ,tags = ['User'])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/attendance/clock-in", response_model=schemas.AttendanceOut, tags=['Attendance'])
def clock_in(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    today = date.today()
    
    # Check if attendance already exists
    attendance = db.query(models.Attendance).filter(
        models.Attendance.user_id == user.id,
        models.Attendance.date == today
    ).first()
    
    if attendance:
        if attendance.clock_in:
            raise HTTPException(status_code=400, detail="Already clocked in today")
    else:
        # Create new attendance record
        attendance = models.Attendance(
            user_id=user.id,
            user_name=user.name,
            date=today
        )
        db.add(attendance)
    
    # Set clock-in time and format as string
    now = datetime.now().time()
    attendance.clock_in = now
    db.commit()
    db.refresh(attendance)
    
    # Format response with time as strings
    return {
        "user_id": attendance.user_id,
        "user_name": attendance.user_name,
        "date": attendance.date,
        "clock_in": attendance.clock_in.strftime("%H:%M:%S") if attendance.clock_in else None,
        "clock_out": attendance.clock_out.strftime("%H:%M:%S") if attendance.clock_out else None
    }

@app.post("/attendance/clock-out", response_model=schemas.AttendanceOut, tags=['Attendance'])
def clock_out(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    today = date.today()
    attendance = db.query(models.Attendance).filter(
        models.Attendance.user_id == user.id,
        models.Attendance.date == today
    ).first()
    
    if not attendance:
        raise HTTPException(status_code=400, detail="You haven't clocked in today")
    if attendance.clock_out:
        raise HTTPException(status_code=400, detail="Already clocked out today")
    
    # Set clock-out time and format as string
    now = datetime.now().time()
    attendance.clock_out = now
    db.commit()
    db.refresh(attendance)
    
    # Format response with time as strings
    return {
        "user_id": attendance.user_id,
        "user_name": attendance.user_name,
        "date": attendance.date,
        "clock_in": attendance.clock_in.strftime("%H:%M:%S") if attendance.clock_in else None,
        "clock_out": attendance.clock_out.strftime("%H:%M:%S") if attendance.clock_out else None
    }

@app.post("/create-leave", response_model=schemas.LeaveRequestOut, tags=['Leave Requests'])
def create_leave_request(
    date: date = Form(...),
    reason: str = Form(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    # Create leave request WITH USER NAME
    db_leave_request = models.LeaveRequest(
        user_id=user.id,
        user_name=user.name,  # Store name directly
        date=date,
        reason=reason
    )
    db.add(db_leave_request)
    db.commit()
    db.refresh(db_leave_request)
    return db_leave_request

@app.get("/Get-leave-lists", response_model=List[schemas.LeaveRequestOut], tags=['Leave Requests'])
def get_leave_requests(
    all: bool = Query(False, description="Return all requests (admin only)"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if user.role == "admin" and all:
        leave_requests = db.query(models.LeaveRequest).all()
    else:
        leave_requests = db.query(models.LeaveRequest).filter(
            models.LeaveRequest.user_id == user.id
        ).all()
    
    return leave_requests

@app.post("/admin/export", tags=['Admin'])
async def export_attendance(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    today = date.today()
    
    # Get all users
    users = db.query(models.User).all()
    user_ids = [user.id for user in users]
    
    # Get today's attendance records
    attendances = db.query(models.Attendance).filter(
        models.Attendance.date == today,
        models.Attendance.user_id.in_(user_ids)
    ).all()
    attendance_map = {att.user_id: att for att in attendances}
    
    # Get today's leave requests
    leaves_today = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.date == today,
        models.LeaveRequest.user_id.in_(user_ids)
    ).all()
    leave_user_ids = {leave.user_id for leave in leaves_today}
    
    export_data = []
    for user in users:
        att = attendance_map.get(user.id)
        is_on_leave = user.id in leave_user_ids
        
        clock_in = ""
        clock_out = ""
        if not is_on_leave and att:
            # Already formatted as strings in the response
            clock_in = att.clock_in if att.clock_in else ""
            clock_out = att.clock_out if att.clock_out else ""
        
        export_data.append([
            user.name,
            user.role,
            today.strftime("%Y-%m-%d"),
            clock_in,
            clock_out,
            "On Leave" if is_on_leave else ""
        ])
    
    success = google_sheets.export_to_sheet(
        export_data,
        spreadsheet_id=os.getenv("SPREADSHEET_ID"),
        sheet_name="attendance"
    )
    
    if success:
        await manager.broadcast("attendance_updated")
        return {"status": "Exported to Google Sheets"}
    raise HTTPException(500, "Export failed")