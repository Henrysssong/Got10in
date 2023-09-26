from pydantic import BaseModel

class Questionnaire(BaseModel):
    major: str
    preference: str  # 'public' or 'private'
