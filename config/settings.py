# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_URL = os.getenv("DB_URL", "mysql+pymysql://your_user:your_password@localhost:your_port/your_database")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
if not isinstance(SECRET_KEY, str):
    SECRET_KEY = str(SECRET_KEY)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Google Sheets Configuration
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SPREADSHEET_NAME", "spreadsheetbot")  # Use correct variable name