import os

# MongoDB configurations
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://<username>:<password>@cluster.mongodb.net/<dbname>?retryWrites=true&w=majority")
DATABASE_NAME = os.getenv("DATABASE_NAME", "your_default_db_name")

# OAuth2.0 configurations for Google
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "your_google_client_id")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "your_google_client_secret")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/login/callback")

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "Your_OpenAI_Key_Here")