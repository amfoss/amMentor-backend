from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import crud, models
from app.db.db import get_db
from app.schemas.submission import SubmissionCreate, SubmissionOut, SubmissionApproval

router = APIRouter()

@router.post("/submit-task", response_model=SubmissionOut)
def submit_task(data: SubmissionCreate, db: Session = Depends(get_db)):
    # 1. Validate mentee
    mentee = crud.get_user_by_email(db, data.mentee_email)
    if not mentee or mentee.role != "mentee":
        raise HTTPException(status_code=403, detail="Invalid or missing mentee")

    # 2. Get task
    task = crud.get_task(db, track_id=data.track_id, task_no=data.task_no)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 3. Submit
    submission = crud.submit_task(db, mentee_id=mentee.id, task_id=task.id, reference_link=data.reference_link, start_date=data.start_date)
    if not submission:
        raise HTTPException(status_code=400, detail="Task already submitted")
    if submission == "late submission not allowed":
        raise HTTPException(status_code=400, detail="You cannot submit this task as the deadline has passed")
    return submission

@router.patch("/approve-task", response_model=SubmissionOut)
def approve_task(data: SubmissionApproval, db: Session = Depends(get_db)):
    # 1. Validate mentor
    mentor = crud.get_user_by_email(db, data.mentor_email)
    if not mentor or mentor.role != "mentor":
        raise HTTPException(status_code=403, detail="Invalid or missing mentor")

    # 2. Validate submission
    sub = db.query(models.Submission).filter_by(id=data.submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    # 3. Confirm mentor is assigned to this mentee
    if not crud.is_mentor_of(db, mentor.id, sub.mentee_id):
        raise HTTPException(status_code=403, detail="Mentor not authorized for this mentee")

    # 4. Approve or pause
    updated = crud.approve_submission(
        db,
        submission_id=sub.id,
        mentor_feedback=data.mentor_feedback,
        status=data.status
    )
    return updated