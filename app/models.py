from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Time
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import date

# models.py
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))  # Add length
    email = Column(String(100), unique=True, index=True)  # Add length
    password = Column(String(255))  # Add length
    qr_code = Column(String(50))  # Add length
    role = Column(String(20))  # Add length
    
    attendances = relationship("Attendance", back_populates="user")
    leave_requests = relationship("LeaveRequest", back_populates="user")


# models.py
class Attendance(Base):
    __tablename__ = "attendances"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, default=date.today())
    clock_in = Column(Time, nullable=True)
    clock_out = Column(Time, nullable=True)
    user_name = Column(String(100))   # Add length here if exists
    
    user = relationship("User", back_populates="attendances")

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user_name = Column(String(100))  # Add this field to store the name
    date = Column(Date, nullable=False)
    reason = Column(String(255), nullable=True)
    
    user = relationship("User", back_populates="leave_requests")