from fastapi import FastAPI, HTTPException, Depends
from models import Questionnaire
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.security.oauth2 import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from fastapi.routing import APIRoute as Route
from starlette.routing import Mount, Router, Route as StarletteRoute
from starlette.routing import request_response
import httpx
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv
from config import MONGODB_URL, DATABASE_NAME, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI

load_dotenv()

app = FastAPI()

# Database configurations
client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

# CORS setup
origins = [
    "http://localhost:3000",   # React's default port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key="some-random-secret-key", max_age=3600)

oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    refresh_token_url=None,
    redirect_uri=GOOGLE_REDIRECT_URI,
    client_kwargs={'scope': 'openid profile email'},
)

@app.get('/login')
async def login(request: Request):
    redirect_uri = "http://localhost:8000/login/callback"  # Manually constructing the URL
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get('/login/callback')
async def callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user = await oauth.google.parse_id_token(request, token)
    request.session['user'] = dict(user)
    return RedirectResponse("/profile")  # Manually constructing the URL

@app.route('/profile')
async def profile(request: Request):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401)
    return user

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/submit-response/")
async def submit_response(response: Questionnaire):
    if not response:
        raise HTTPException(status_code=400, detail="Invalid response")
    
    # Save to MongoDB 
    result = await db.responses.insert_one(response.model_dump())

    if not result:
        raise HTTPException(status_code=500, detail="Failed to save response")

    return {"message": "Response saved successfully"}

@app.post("/get-college-rankings/")
async def get_college_rankings(response: Questionnaire):
    # Use the OpenAI API to get the rankings based on the user's preferences
    url = "https://api.openai.com/v2/engines/davinci-codex/completions"
    YOUR_OPENAI_API_KEY = "Your OpenAI Key Here"
    headers = {
        "Authorization": f"Bearer {YOUR_OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "OpenAI-FastAPI-Integration",
    }
    
    prompt_text = f"Given that a student prefers a {response.preference} university and wants to major in {response.major}, what are the top 10 college recommendations?"
    
    payload = {
        "prompt": prompt_text,
        "max_tokens": 150  # adjust as needed
    }
    
    async with httpx.AsyncClient() as client:
        api_response = await client.post(url, headers=headers, json=payload)
    
    response_data = api_response.json()
    return {"rankings": response_data["choices"][0]["text"].strip()}
