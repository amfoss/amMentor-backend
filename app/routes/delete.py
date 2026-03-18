from fastapi import APIRouter, Depends, HTTPException
from app.db.db import get_db
from sqlalchemy.orm import Session
from app.db import crud, models
from datetime import datetime

router = APIRouter()

@router.delete("/{user_id}")
def delete_user(
    user_id : int,
    db: Session = Depends(get_db)
):
    # Validate User
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=403, detail="Invalid or missing user")
    
    user.deleted_at = datetime.utcnow()
    db.commit()

    return {"message" : "User deletion successful"}