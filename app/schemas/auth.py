from pydantic import BaseModel, EmailStr, ConfigDict

class User(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str

    model_config = ConfigDict(from_attributes=True)

class UserOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User