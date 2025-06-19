from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
from app import models, schemas
from app.auth import get_password_hash, verify_password
from sqlalchemy.orm import Session, joinedload

def get_user_by_qr(db: Session, qr_code: str):
    return db.query(models.User).filter(models.User.qr_code == qr_code).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        name=user.name,
        email=user.email,
        password=hashed_password,
        qr_code=user.qr_code,
        role=user.role 
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
    
    # Use hashed password comparison instead of role check
    if not verify_password(password, user.password):
        return None
    return user

def clock_in(db: Session, user: models.User):
    today = date.today()
    attendance = db.query(models.Attendance).filter_by(user_id=user.id, date=today).first()
    if not attendance:
        attendance = models.Attendance(user_id=user.id, user_role=user.role, date=today, clock_in=datetime.now())
        db.add(attendance)
    else:
        attendance.clock_in = datetime.now()
        attendance.user_role = user.role 
    db.commit()
    db.refresh(attendance)
    return attendance

def clock_out(db: Session, user: models.User):
    today = date.today()
    attendance = db.query(models.Attendance).filter_by(user_id=user.id, date=today).first()
    if attendance:
        attendance.clock_out = datetime.now()
        attendance.user_role = user.role 
        db.commit()
        db.refresh(attendance)
        return attendance
    return None

def get_today_attendance(db: Session):
    today = date.today()
    return (
        db.query(models.Attendance)
        .options(joinedload(models.Attendance.user))
        .filter(models.Attendance.date == today)
        .all()
    )
    
def create_leave_request(db: Session, user_id: int, leave_request: schemas.LeaveRequestCreate):
    # Get the user object to access the name
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check for existing leave
    existing_leave = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.user_id == user_id,
        models.LeaveRequest.date == leave_request.date
    ).first()
    
    if existing_leave:
        raise HTTPException(400, "Leave already exists for this date")
    
    # Create the leave request without setting user_name
    db_leave_request = models.LeaveRequest(
        user_id=user_id,
        date=leave_request.date,
        reason=leave_request.reason
    )
    
    db.add(db_leave_request)
    db.commit()
    db.refresh(db_leave_request)
    
    # Return the leave request with user name (will be accessible via relationship)
    return db_leave_request

def get_leave_requests(db: Session, user_id: int = None):
    # Eager load user relationship with only the name
    query = db.query(
        models.LeaveRequest,
        models.User.name.label('user_name')
    ).join(models.User)
    
    if user_id:
        query = query.filter(models.LeaveRequest.user_id == user_id)
    
    # Return results with user_name
    results = query.all()
    return [leave_request for (leave_request, user_name) in results]


# In crud.py
def get_leave_requests(db: Session, user_id: int = None):
    if user_id:
        return db.query(models.LeaveRequest).filter(models.LeaveRequest.user_id == user_id).all()
    else:
        return db.query(models.LeaveRequest, models.User.name)\
                .join(models.User, models.LeaveRequest.user_id == models.User.id)\
                .all()  


# In crud.py
def is_user_on_leave(db: Session, user_id: int, date: date):
    # Check if user has an approved leave request for this date
    return db.query(models.LeaveRequest).filter(
        models.LeaveRequest.user_id == user_id,
        models.LeaveRequest.date == date,
        models.LeaveRequest.status == "approved"
    ).first() is not None
    
    
def get_users_by_role(db: Session, role: str = None, exclude_role: str = None):
    query = db.query(models.User)
    if role:
        query = query.filter(models.User.role == role)
    if exclude_role:
        query = query.filter(models.User.role != exclude_role)
    return query.all()    