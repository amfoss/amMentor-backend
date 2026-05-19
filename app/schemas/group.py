from pydantic import BaseModel
from typing import Optional

class GroupCreate(BaseModel):
    title: str
    description: Optional[str] = None

class GroupOut(BaseModel):
    id: int
    title: str
    description: Optional[str]

    class Config:
        from_attributes = True