from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.db import get_db
from app.db import models
from app.schemas.group import GroupCreate, GroupOut

from app.crud.auth import decode_token, oauth2_scheme, get_user_by_id

router = APIRouter()

@router.post("/create", response_model=GroupOut)
def create_new_group(group_data: GroupCreate, token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    token_data = decode_token(token)
    
    if "error" in token_data:
        if token_data["error"] == "token expired":
            raise HTTPException(status_code=401, detail="Session expired.")
        else:
            raise HTTPException(status_code=401, detail="Invalid token.")
        
    user_id = int(token_data["user_id"])

    user = get_user_by_id(db,user_id)

    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can create groups.")

    group = models.Group(title=group_data.title, description=group_data.description)

    db.add(group)
    db.commit()
    db.refresh(group)

    return group