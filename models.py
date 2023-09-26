from pydantic import validator, BaseModel

class Questionnaire(BaseModel):
    major: str
    preference: str  # 'public' or 'private'
    
    @validator('preference', pre=True)
    def check_preference(cls, preference):
        if preference not in ['public', 'private']:
            raise ValueError('Preference must be either "public" or "private"')
        return preference
