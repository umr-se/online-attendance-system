from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime, date
from pydantic import field_validator, ConfigDict

class UserBase(BaseModel):
    name: str
    email: str
    role: str

class UserCreate(UserBase):
    password: str
    qr_code: str

class UserOut(UserBase):
    id: int
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class AttendanceCreate(BaseModel):
    qr_code: str

class AttendanceOut(BaseModel):
    user_id: int
    user_name: str
    date: date
    clock_in: Optional[str]  # Change to string
    clock_out: Optional[str]  # Change to string
    class Config:
        from_attributes = True
        
class LeaveRequestCreate(BaseModel):
    date: date
    reason: str = None

class LeaveRequestOut(LeaveRequestCreate):
    id: int
    user_id: int
    user_name: str  # Now this will come directly from query
    
    class Config:
        from_attributes = True