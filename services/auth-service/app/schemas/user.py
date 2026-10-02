from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID

class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=30,
        pattern="^[a-zA-Z0-9_-]+$"  #only alphanumeric characters
    )
    email: EmailStr
    password: str = Field(
        min_length=8, 
        max_length=128
    )
    
    @field_validator('username')
    def validate_username(cls, v):
        if not v.isascii():
            raise ValueError('Username must be ASCII characters only')
        return v
    
    @field_validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in '@$!%*?&' for c in v):
            raise ValueError('Password must contain at least one special character (@$!%*?&)')
        return v

    model_config = {
        "json_schema_extra" : {
            "examples": [
                {
                    "username": "cranky",
                    "email": "example@example.com",
                    "password": "ThisIsATest123!"
                }
            ]
        }
    }

class LoginForm(BaseModel):
    email: EmailStr
    password: str
    
class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr

    model_config = {
        "from_attributes": True
    }

class Token(BaseModel):
    access_token: str
    token_type: str

LoginForm.model_rebuild()