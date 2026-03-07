from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import crud, models
from app.db.db import get_db
from app.schemas.submission import SubmissionCreate, SubmissionOut, SubmissionApproval,StartTask,ExtendCreate,ExtendOut,DeadlineOut, DeadlineBase

router = APIRouter()

@router.post("/start-task",response_model=SubmissionOut)
def start_task(data:StartTask,db:Session=Depends(get_db)):

     # 1. Validate mentee
    mentee = crud.get_user_by_email(db, data.mentee_email)
    if not mentee or mentee.role != "mentee":
        raise HTTPException(status_code=403, detail="Invalid or missing mentee")
    
     # 2. Get task
    task = crud.get_task(db, track_id=data.track_id, task_no=data.task_no)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # 3. Start task
    submission =crud.start_task(db=db,mentee_id=mentee.id,task_id=task.id)
    if not submission:
        raise HTTPException(status_code=400, detail="Task already Started")
    return submission

@router.patch("/submit-task", response_model=SubmissionOut)
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
    submission = crud.submit_task(db,submission_id=data.submission_id,reference_link=data.reference_link)
    if not submission:
        raise HTTPException(status_code=400, detail="Task already submitted")

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
        status=data.status,
        mentor_id=mentor.id
    )
    return updated

@router.post("/extend-deadline", response_model= ExtendOut)
def extend_date(data:ExtendCreate,db:Session = Depends(get_db)):
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

    extended = crud.extend_date(submission_id= data.submission_id, mentor_id=mentor.id,reason = data.reason,extended_date=data.extended_date,db=db)   
    return extended

@router.get("/get_deadline", response_model = DeadlineOut)
def get_deadline(data:DeadlineBase,db: Session = Depends(get_db)):
    deadline = crud.get_deadline(db=db, task_id = data.task_id, mentee_id =  data.mentee_id)
    return deadline

'''
@router.post("/pause-task",response_model=PauseOut)
def pause_task(data:PauseCreate, db: Session = Depends(get_db)):
    # 1. Validate mentor
    mentor = crud.get_user_by_email(db, data.mentor_email)
    if not mentor or mentor.role != "mentor":
        raise HTTPException(status_code=403, detail="Invalid or missing mentor")

    # 2. Validate submission
    submission = db.query(models.Submission).filter_by(id=data.submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # 3. Confirm mentor is assigned to this mentee
    if not crud.is_mentor_of(db, mentor.id, submission.mentee_id):
        raise HTTPException(status_code=403, detail="Mentor not authorized for this mentee")

    # 4. Get task
    task = crud.get_task(db, track_id=data.track_id, task_no=data.task_no)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    pause = crud.pause_task(submission_id=data.submission_id,db=db,reason=data.reason)
    return pause
@router.patch("/resume-task",response_model = PauseOut)
def resume_task(data:ResumeCreate,db:Session=Depends(get_db)):
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

    # 4. Get task
    task = crud.get_task(db, track_id=data.track_id, task_no=data.task_no)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    pause = crud.resume_task(pause_id=data.id,db=db)
    if not pause:
        raise HTTPException(status_code=400, detail="Task not Paused")
    return pause
'''

