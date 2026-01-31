from typing import Optional
from app.schemas.submission import SubmissionOut
from sqlalchemy.orm import Session,joinedload
from app.db import models
from datetime import datetime, date
from sqlalchemy import func

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_task(db: Session, track_id: int, task_no: int):
    return db.query(models.Task).filter_by(track_id=track_id, task_no=task_no).first()
#coded from herreference_link=data.reference_link, start_date=data.start_datee
def start_task(db: Session,mentee_id: int,task_id: int):
    start_date = date.today()
    #Validate Task
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise Exception("Task not found")
    # Alrdy exist
    exist = db.query(models.Submission).filter_by(task_id = task_id, mentee_id = mentee_id).first()
    if exist :
        return None  
    submission = models.Submission(
        mentee_id=mentee_id,
        task_id=task.id,
        task_name=task.title,     
        task_no=task.task_no,   
        reference_link="started", #remove it before push
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
        raise("Task not started")
    if submission.status == "submitted":
        raise("Task Already Submitted")
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


def approve_submission(db: Session, submission_id: int, mentor_feedback: str, status: str):
    sub = db.query(models.Submission).filter_by(id=submission_id).first()
    if not sub:
        return None
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

def pause_task(db: Session,submission_id: int,reason: str):
    pause = db.query(models.Pause).filter(models.Pause.id == submission_id)
    sub = db.query(models.Submission).filter_by(id=submission_id).first()
    if pause :
        raise("Tasked already paused")
    pause.reason=reason
    pause.pause_date = date.today()
    sub.status = "paused"
    db.add_all([sub, pause])
    db.commit()
    db.refresh(sub)
    db.refresh(pause)
    return sub
#coded till here
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
