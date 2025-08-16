from typing import Optional
from app.schemas.submission import SubmissionOut
from sqlalchemy.orm import Session,joinedload
from app.db import models
from datetime import date, timedelta
from sqlalchemy import func
from app.db.db import SessionLocal
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = "credentials.json"

def mentor_mentee_map(db:Session):
    mentors=(
        db.query(models.User).filter(models.User.role == "mentor").all()
    )
    mentees=(
        db.query(models.User).filter(models.User.role == "mentee").all()
    )

    for mentor in mentors:
        for mentee in mentees:
            if not db.query(models.MentorMenteeMap).filter_by(mentor_id=mentor.id, mentee_id=mentee.id).first():
                map_entry = models.MentorMenteeMap(mentor_id=mentor.id, mentee_id=mentee.id)
                db.add(map_entry)
    db.commit()
    db.refresh(map_entry)
    return "Mentor Mentee Mapping completed successfully"

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_task(db: Session, track_id: int, task_no: int):
    return db.query(models.Task).filter_by(track_id=track_id, task_no=task_no).first()

def submit_task(db: Session, mentee_id: int, task_id: int, start_date: date, commit_hash: str):
    existing = db.query(models.Submission).filter_by(mentee_id=mentee_id, task_id=task_id).first()
    if existing:
        return None  # Already submitted
    
    mentee = db.query(models.User).filter(models.User.id == mentee_id).first()

    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise Exception("Task not found")
    
    # convert start_date into a datetime object
    start_date = start_date
    deadline = start_date + timedelta(days=task.deadline_days)
    submitted_at = date.today()

    # Check if the submission is late
    if deadline >= submitted_at:
        submission = models.Submission(
            mentee_id=mentee_id,
            task_id=task.id,
            task_name=task.title,     
            task_no=task.task_no,    
            submitted_at=date.today(),
            status="submitted",
            start_date=start_date,
            commit_hash = commit_hash
        )

        credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(credentials)
        if(task.track_id == 1):
            sheet = client.open("Copy of Praveshan 2025 Master DB").worksheet("S1 Submissions") # Change sheet name
            cell = sheet.find(mentee.name)
            print(sheet)
            if not cell:
                name_column = sheet.col_values(1)
                row = len(name_column) + 1
                sheet.update_cell(row, 1, mentee.name)
                sheet.update_cell(row, task.task_no+2, commit_hash)
            else:
                row = cell.row
                sheet.update_cell(row, task.task_no+2, commit_hash)
        elif(task.track_id == 2):
            sheet = client.open("Copy of Praveshan 2025 Master DB").worksheet("S2 Submissions") # Change sheet name
            cell = sheet.find(mentee.name)
            if not cell:
                name_column = sheet.col_values(1)
                row = len(name_column) + 1
                sheet.update_cell(row, 1, mentee.name)
                sheet.update_cell(row, task.task_no+2, commit_hash)
            else:
                row = cell.row
                sheet.update_cell(row, task.task_no+2, commit_hash)
        
        

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
            status=sub.status,
            submitted_at=sub.submitted_at.date() if sub.submitted_at else None,
            approved_at=sub.approved_at.date() if sub.approved_at else None,
            mentor_feedback=sub.mentor_feedback,
            start_date=sub.start_date.date() if sub.start_date else None
        )
        for sub in submissions
    ]
    
def get_sheet_data():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    client = gspread.authorize(creds)
    worksheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID")).worksheet("Copy of P1-Mapping") # Change sheet name
    expected_headers = ["Name", "Email Address","Faction name"]
    data = worksheet.get_all_records(expected_headers=expected_headers)
    return data

def sync_users_from_sheet():
    db: Session = SessionLocal()
    try:
        rows = get_sheet_data() 
        print(f"Loaded {len(rows)} rows from sheet.")
        inserted_count = 0
        for row in rows:
            Faction_name = row.get("Faction name", "")
            email = row.get("Email Address", "").strip()
            name = row.get("Name", "").strip()
            if not email or not name:
                continue
            if get_user_by_email(db, email):
                continue 
            if Faction_name=="S2+":
                track = 2
            else:
                track=1
            user = models.User(name=name, email=email, role="mentee",group_name=Faction_name ,track=track)
            db.add(user)
            inserted_count += 1
            db.commit()
        print(f"Inserted {inserted_count} new users.")
    except Exception as e:
        print(f"Error syncing users: {e}")
    finally:
        db.close()

