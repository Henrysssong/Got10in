import os

MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017") 
DATABASE_NAME = "gottening_db"
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = "http://localhost:8000/login/callback"
