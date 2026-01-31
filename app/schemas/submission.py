from pydantic import BaseModel
from typing import Optional
from datetime import date,datetime

class SubmissionBase(BaseModel):
    track_id: int
    task_no: int
    reference_link: str
    start_date: date
class SubmissionCreate(SubmissionBase):
    mentee_email: str
    submission_id : int

class SubmissionOut(BaseModel):
    id: int
    mentee_id: int
    task_id: int
    task_no: int
    task_name: str 
    reference_link: str
    status: str
    submitted_at: datetime
    approved_at: Optional[date] = None
    mentor_feedback: Optional[str] = None   
    start_date: datetime
    evaluated_by_mentor_id : Optional[int] = None
    evaluated_by_mentor_name : Optional[str] = None
    evaluated_by_mentor_email: Optional[str] = None
    class Config:
        orm_mode = True

class SubmissionApproval(BaseModel):
    submission_id: int
    mentor_email: str
    status: str  # approved, paused, rejected
    mentor_feedback: Optional[str] = None

class StartTask(BaseModel):
    track_id: int
    task_no: int
    mentee_email: str