import os
import json
import gspread
from typing import Optional
from app.schemas.submission import SubmissionOut
from sqlalchemy.orm import Session
from app.db import models
from datetime import datetime, date, timedelta
from sqlalchemy import func
from app.db.db import SessionLocal

def _get_gspread_client():
    creds_json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not creds_json_str:
        raise ValueError("GOOGLE_CREDENTIALS_JSON environment variable is not set.")
    
    creds_info = json.loads(creds_json_str)
    client = gspread.service_account_from_dict(creds_info)
    return client

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_task(db: Session, track_id: int, task_no: int):
    return db.query(models.Task).filter_by(track_id=track_id, task_no=task_no).first()

def submit_task(db: Session, mentee_id: int, task_id: int, reference_link: str, start_date: date, commit_hash: str):
    existing = db.query(models.Submission).filter_by(mentee_id=mentee_id, task_id=task_id).first()
    if existing:
        return None
    
    mentee = db.query(models.User).filter(models.User.id == mentee_id).first()
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise Exception("Task not found")
    
    start_date = datetime.combine(start_date, datetime.min.time()) 
    deadline = start_date + timedelta(days=task.deadline_days)
    submitted_at = datetime.now()

    if deadline >= submitted_at:
        submitted_late = False
    elif deadline + timedelta(hours=12) >= submitted_at:
        submitted_late = True
    else:
        return "late submission not allowed"

    submission = models.Submission(
        mentee_id=mentee_id,
        task_id=task.id,
        task_name=task.title,     
        task_no=task.task_no,    
        reference_link=reference_link,
        submitted_at=date.today(),
        status="submitted",
        start_date=start_date,
        submitted_late=submitted_late,
        commit_hash=commit_hash
    )

    client = _get_gspread_client()
    sheet_name = "Copy of Praveshan 2025 Master DB"
    
    if task.track_id == 1:
        worksheet_name = "S1 Submissions"
    elif task.track_id == 2:
        worksheet_name = "S2 Submissions"
    else:
        worksheet_name = None

    if worksheet_name:
        sheet = client.open(sheet_name).worksheet(worksheet_name)
        cell = sheet.find(mentee.name)
        if not cell:
            row = len(sheet.col_values(1)) + 1
            sheet.update_cell(row, 1, mentee.name)
            sheet.update_cell(row, task.task_no + 2, commit_hash)
        else:
            row = cell.row
            sheet.update_cell(row, task.task_no + 2, commit_hash)

    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    return submission

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
    
def get_sheet_data():
    client = _get_gspread_client()
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise ValueError("GOOGLE_SHEET_ID environment variable not set.")

    worksheet = client.open_by_key(sheet_id).worksheet("Form Responses")
    expected_headers = ["Name", "Email Address"]
    data = worksheet.get_all_records(expected_headers=expected_headers)
    return data

def sync_users_from_sheet():
    db: Session = SessionLocal()
    try:
        rows = get_sheet_data() 
        inserted_count = 0
        for row in rows:
            email = row.get("Email Address", "").strip()
            name = row.get("Name", "").strip()
            if not email or not name:
                continue
            if get_user_by_email(db, email):
                continue 
            user = models.User(name=name, email=email, role="mentee")
            db.add(user)
            inserted_count += 1

        db.commit()
    finally:
        db.close()