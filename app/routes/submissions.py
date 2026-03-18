from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.db import get_db
from app.db import crud, models
from app.schemas import submission
from app.schemas.submission import SubmissionOut
from app.db.crud import get_submissions_for_user
router = APIRouter()


@router.get("/", response_model=List[SubmissionOut])
def get_submissions(
    email: str = Query(...),
    track_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    submissions = get_submissions_for_user(db, email, track_id)

    # print("DEBUG: Type of returned object:", type(submissions[0]))
    return submissions