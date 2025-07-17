from typing import Optional
from app.schemas.submission import SubmissionOut
from sqlalchemy.orm import Session,joinedload
from app.db import models
from datetime import datetime, date, timedelta
from sqlalchemy import func

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_task(db: Session, track_id: int, task_no: int):
    return db.query(models.Task).filter_by(track_id=track_id, task_no=task_no).first()

def submit_task(db: Session, mentee_id: int, task_id: int, reference_link: str, start_date: date):
    existing = db.query(models.Submission).filter_by(mentee_id=mentee_id, task_id=task_id).first()
    if existing:
        return None  # Already submitted

    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise Exception("Task not found")
    
    start_date = start_date
    submitted_at = date.today()
    deadline = start_date + timedelta(days=task.deadline_days)

    if deadline >= submitted_at:
        submission = models.Submission(
            mentee_id=mentee_id,
            task_id=task.id,
            task_name=task.title,     
            task_no=task.task_no,    
            reference_link=reference_link,
            submitted_at=date.today(),
            status="submitted",
            start_date=start_date,
        )

        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission
    else:
        return "late submission not allowed"

def approve_submission(db: Session, submission_id: int, mentor_feedback: str, status: str):
    sub = db.query(models.Submission).filter_by(id=submission_id).first()
    if not sub:
        return None

    sub.status = status
    sub.mentor_feedback = mentor_feedback
    if status == "approved":
        sub.approved_at = date.today()

    db.commit()
    db.refresh(sub)
    return sub

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
        .filter(models.Submission.status == "approved")
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

    query = db.query(models.Submission).filter(
        models.Submission.mentee_id == user.id
    )

    if track_id is not None:
        query = query.join(models.Task).filter(models.Task.track_id == track_id)

    submissions = query.all()

    return [
        SubmissionOut(
            id=sub.id,
            mentee_id=sub.mentee_id,
            task_id=sub.task_id,
            task_name=sub.task_name,
            task_no=sub.task_no,
            reference_link=sub.reference_link,
            status=sub.status,
            submitted_at=sub.submitted_at.date() if sub.submitted_at else None,
            approved_at=sub.approved_at.date() if sub.approved_at else None,
            mentor_feedback=sub.mentor_feedback,
            start_date=sub.start_date.date() if sub.start_date else None
        )
        for sub in submissions
    ]