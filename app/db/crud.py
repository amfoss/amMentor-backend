from typing import Optional
from app.schemas.submission import SubmissionOut, DeadlineOut
from sqlalchemy.orm import Session,joinedload
from app.db import models
from datetime import datetime, date, timedelta
from sqlalchemy import func

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_task(db: Session, track_id: int, task_no: int):
    return db.query(models.Task).filter_by(track_id=track_id, task_no=task_no).first()

def start_task(db: Session,mentee_id: int,task_id: int):
    start_date = datetime.today()
    #Validate Task
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise Exception("Task not found")
    # Already exist
    exist = db.query(models.Submission).filter_by(task_id = task_id, mentee_id = mentee_id).first()
    if exist :
        return None  
    submission = models.Submission(
        mentee_id=mentee_id,
        task_id=task.id,
        task_name=task.title,     
        task_no=task.task_no,
        submitted_at = None,   
        reference_link="None",
        status="started".lower(),
       start_date=start_date,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission

def submit_task(db: Session, submission_id: int,reference_link:str):
    submission = db.query(models.Submission).filter_by(id = submission_id).first()
    if not submission:
        raise Exception("Submission Not Found")
    if submission.status == "submitted":
        raise Exception("Task Already Submitted")
    task = db.query(models.Task).filter(models.Task.id == submission.task_id).first()
    if not task:
        raise Exception("Task not found")
    submission.submitted_at=date.today(),
    submission.status="submitted".lower(),
    submission.reference_link=reference_link,
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def approve_submission(db: Session, submission_id: int, mentor_feedback: str, status: str,mentor_id: int):
    sub = db.query(models.Submission).filter_by(id=submission_id).first()
    if not sub:
        return None
    if sub.status != "submitted":
        raise Exception("Task not Submitted or rejected")
    normalized_status = status.strip().lower()
    sub.status = normalized_status
    sub.mentor_feedback = mentor_feedback
    sub.evaluated_by_mentor_id = mentor_id
    
    if normalized_status == "approved":
       sub.approved_at = date.today()
    else:
        sub.approved_at = None

    db.commit()
    return (
        db.query(models.Submission)
        .options(joinedload(models.Submission.evaluated_by_mentor))
        .filter(models.Submission.id == submission_id)
        .first()
    )


def extend_date(db:Session,extended_date:datetime,submission_id:int,reason:str,mentor_id :int):
    submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not submission:
        raise Exception("Submission Not Found")
    exist = db.query(models.Extend).filter(models.Extend.submission_id == submission_id).first()
    deadline = get_deadline(db= db, mentee_id= submission.mentee_id, task_id=submission.task_id)
    # for formating the date without timezone in it
    extended_date = extended_date.replace(tzinfo=None)

    if(deadline.deadline > extended_date):
        raise Exception("Deadline is Less Than Original deadline")
    if exist:
        # if the date is preponed it does not count as extending the deadline so not adding to the count
        if(exist.extended_date < extended_date):
            exist.extended_count = exist.extended_count+1
        exist.extended_date = extended_date
        db.add(exist)
        db.commit()
        db.refresh(exist)
        return exist
    extended = models.Extend(
        extended_date = extended_date,
        submission_id = submission_id,
        reason = reason,
        extended_by_mentor_id = mentor_id,
        extended_count = 1
    )
    db.add(extended)
    db.commit()
    db.refresh(extended)
    return extended

def get_deadline(db: Session,task_id: int, mentee_id: int):
    #Validate Submission
    submission = db.query(models.Submission).filter_by(task_id = task_id, mentee_id = mentee_id).first()
    if not submission:
        raise Exception("Submission Not Found")    
    if submission.status == "approved":
        raise Exception("Task Already approved")
     #Validate Task
    task = db.query(models.Task).filter(models.Task.id == submission.task_id).first()
    if not task:
        raise Exception("Task not found")
    start_date = submission.start_date
    duration = timedelta(days = task.deadline_days)
    extended = db.query(models.Extend).filter(models.Extend.submission_id == submission.id).first()

    if extended :
        deadline = extended.extended_date
    else : 
        deadline = start_date + duration
    
    extended_days = (deadline - (start_date + duration)).days

    return DeadlineOut(
                mentee_id=mentee_id,
                task_id=task_id,
                deadline=deadline,
                extended_days=extended_days
            )



'''
def pause_task(db: Session,submission_id: int,reason: str):
    exist = db.query(models.Pause).filter(models.Pause.submission_id == submission_id).first()
    sub = db.query(models.Submission).filter_by(id=submission_id).first()
    if exist :
        raise Exception("Tasked already paused")
    pause = models.Pause(
        submission_id = submission_id,
        pause_date = date.today(),
        reason = reason
    )
    sub.status = "paused"
    db.add_all([sub, pause])
    db.commit()
    db.refresh(pause)
    return pause

def resume_task(db:Session,pause_id:int ):
    pause = db.query(models.Pause).filter(models.Pause.id == pause_id).first()
    if not pause :
        return None
    pause.resume_date = date.today()
    db.add(pause)
    db.commit()
    db.refresh(pause)
    return pause
'''


def is_mentor_of(db: Session, mentor_id: int, mentee_id: int):
    return db.query(models.MentorMenteeMap).filter_by(mentor_id=mentor_id, mentee_id=mentee_id).first() is not None

def get_leaderboard_data(db: Session, track_id: int):

    return (
        db.query(
            models.User.name,
            func.sum(models.Task.points).label("total_points"),
            func.count(models.Submission.id).label("tasks_completed")
        )
        .join(models.Submission, models.Submission.mentee_id == models.User.id)
        .join(models.Task, models.Submission.task_id == models.Task.id)
        .filter(func.lower(models.Submission.status) == "approved")
        .filter(models.Task.track_id == track_id)
        .group_by(models.User.id)
        .order_by(func.sum(models.Task.points).desc())
        .all()
    )
def get_otp_by_email(db, email):
    return db.query(models.OTP).filter(models.OTP.email == email).first()

def create_or_update_otp(db, email, otp, expires_at):
    entry = get_otp_by_email(db, email)
    if entry:
        entry.otp = otp
        entry.expires_at = expires_at
    else:
        entry = models.OTP(email=email, otp=otp, expires_at=expires_at)
        db.add(entry)
    db.commit()


def get_submissions_for_user(db: Session, email: str, track_id: Optional[int] = None) -> list[SubmissionOut]:
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return []

    submissions = (
        db.query(models.Submission)
        .options(joinedload(models.Submission.evaluated_by_mentor))
        .filter(models.Submission.mentee_id == user.id)
        .all()
    )
    return submissions
