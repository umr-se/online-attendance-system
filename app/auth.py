from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.schemas import TokenData
import logging

# Set up logging
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Ensure SECRET_KEY is bytes
    secret_bytes = SECRET_KEY.encode('utf-8') if isinstance(SECRET_KEY, str) else SECRET_KEY
    
    try:
        return jwt.encode(to_encode, secret_bytes, algorithm=ALGORITHM)
    except Exception as e:
        logger.error(f"Error creating access token: {str(e)}")
        raise RuntimeError("Failed to create access token")

def decode_token(token: str):
    try:
        # Ensure SECRET_KEY is bytes
        secret_bytes = SECRET_KEY.encode('utf-8') if isinstance(SECRET_KEY, str) else SECRET_KEY
        
        payload = jwt.decode(token, secret_bytes, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return TokenData(email=email)
    except JWTError as e:
        logger.error(f"JWT Error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        return None