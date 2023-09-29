from fastapi import FastAPI, HTTPException, Depends
from models import Questionnaire
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.security.oauth2 import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
import httpx
import bcrypt
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv
from config import MONGODB_URL, DATABASE_NAME, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
from config import OPENAI_API_KEY
import os

load_dotenv()

app = FastAPI()

# Constants for OpenAI
OPENAI_URL = "https://api.openai.com/v2/engines/davinci-codex/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json",
    "User-Agent": "OpenAI-FastAPI-Integration",
}

# Database configurations
client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

# CORS setup for development
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secure session middleware setup
SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "some-random-secret-key")  # Get from environment variable
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=3600)

# OAuth setup
oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    redirect_uri=GOOGLE_REDIRECT_URI,
    client_kwargs={'scope': 'openid profile email'},
)

@app.get('/login')
async def login(request: Request):
    redirect_uri = "http://localhost:8000/login/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get('/login/callback')
async def callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user = await oauth.google.parse_id_token(request, token)
    request.session['user'] = dict(user)
    return RedirectResponse("/profile")

@app.route('/profile')
async def profile(request: Request):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401)
    return user

@app.post("/register/")
async def register(email: str, password: str):
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Store the hashed_pw in the database along with the user's email
    user_data = {"email": email, "password": hashed_pw}
    try:
        await db.users.insert_one(user_data)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    return {"message": "User registered successfully"}

@app.post("/login-email/")
async def login_email(email: str, password: str):
    user = await db.users.find_one({"email": email})

    if not user or not bcrypt.checkpw(password.encode('utf-8'), user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    return {"message": "Login successful"}

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/submit-response/")
async def submit_response(response: Questionnaire):
    if not response:
        raise HTTPException(status_code=400, detail="Invalid response")
    
    # Save to MongoDB 
    result = await db.responses.insert_one(response.dict())

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save response")

    return {"message": "Response saved successfully"}

@app.post("/get-college-rankings/")
async def get_college_rankings(response: Questionnaire):
    # Construct the prompt for OpenAI
    prompt_text = f"Given that a student prefers a {response.preference} university and wants to major in {response.major}, what are the top 10 college recommendations?"
    
    payload = {
        "prompt": prompt_text,
        "max_tokens": 150
    }
    
    async with httpx.AsyncClient() as client:
        api_response = await client.post(OPENAI_URL, headers=HEADERS, json=payload)
    
    response_data = api_response.json()
    # Ensure the response is as expected
    rankings = response_data.get("choices", [{}])[0].get("text", "").strip()
    if not rankings:
        raise HTTPException(status_code=500, detail="Failed to get rankings from OpenAI")
    
    return {"rankings": rankings}
