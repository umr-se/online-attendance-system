# Online Attendance System

A full-featured online attendance management system built using **FastAPI** and **SQLAlchemy** with user authentication, Google Sheets integration, WebSocket notifications, and role-based access control (admin/user).

---

## 🚀 Features

- JWT-based user authentication system
- Clock-in and clock-out attendance recording
- Leave request handling
- Google Sheets export (for admins)
- WebSocket-based real-time updates
- Default admin auto-creation at startup
- CORS enabled for frontend integration

---

## 🛠️ Tech Stack

- **FastAPI**
- **SQLAlchemy**
- **JWT (via python-jose)**
- **Google Sheets API**
- **SQLite/MySQL** (via SQLAlchemy)
- **WebSockets**
- **dotenv for env configs**

---

## ⚙️ Installation

1. **Clone the repository**

```bash
git clone https://github.com/umr-se/online-attendance-system.git
cd online-attendance-system
```

2. **Create and activate a virtual environment**

```bash
python -m venv venv
source venv/bin/activate
```

3. **Install the dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up your .env file**

```
GOOGLE_CREDENTIALS_FILE=credentials.json
SPREADSHEET_ID=your_spreadsheet_id
SPREADSHEET_NAME=attendance
```


5. **Run the FastAPI app**

```bash
uvicorn app.main:app --reload
```

## 📝 Google Sheets Setup

To enable exporting attendance data to Google Sheets:

1. **Go to** [Google Cloud Console](https://console.cloud.google.com/)
2. **Create a new project** (or use an existing one)
3. **Enable the following APIs**:
   - Google Sheets API
   - Google Drive API
4. **Create a service account**:
   - Navigate to **"APIs & Services" > "Credentials"**
   - Click **"Create Credentials" > "Service Account"**
   - Set a name and create the account
   - Under **"Key"**, generate a **JSON key** and download it as `credentials.json`
5. **Place the `credentials.json` file** in your project root
6. **Share the target Google Sheet** with the **service account email address**
   - It will look like: `your-service-account@your-project.iam.gserviceaccount.com`
   - Give **Editor** access
7. Add the following to your `.env` file:
   
![excel](https://github.com/user-attachments/assets/2e05ddf3-1f1a-4292-bf2d-a5f1834f40c5)
![database](https://github.com/user-attachments/assets/6aea7504-84b3-4997-a6ee-02680ec6f4c6)


