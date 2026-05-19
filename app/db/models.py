from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    is_member = Column(Boolean, nullable=False)
    is_admin = Column(Boolean, nullable=False)
    is_faculty = Column(Boolean, nullable=False)

    deleted_at = Column(DateTime, nullable=True, default=None, index=True)
    
class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    deadline_days = Column(Integer, nullable=True)

    assign_everyone = Column(Boolean, nullable=False)

    individual_task = Column(Boolean, nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    __table_args__ = (UniqueConstraint("group_id", "title", name="unique_group_task"),
                        CheckConstraint(
                            "(individual_task = TRUE AND user_id IS NOT NULL) OR (individual_task = FALSE AND user_id IS NULL)",
                            name="check_individual_task_has_user"
                        ),
                    ) 

    group = relationship("Group", back_populates="tasks")
    user = relationship("User", back_populates="tasks")

Group.tasks = relationship("Task", back_populates="group", cascade="all, delete-orphan")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    submitee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    reference_link = Column(Text, nullable=False)
    explainantion = Column(Text, nullable=True)
    status = Column(String, default="submitted")  # submitted / approved / ongoing / extended / rejected
    submitted_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    mentor_feedback = Column(Text, nullable=True)
    evaluated_by_mentor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    submitee = relationship("User", foreign_keys=[submitee_id], lazy="joined")
    evaluated_by_mentor = relationship("User", foreign_keys=[evaluated_by_mentor_id],lazy="joined")

    task = relationship("Task")
    @property
    def evaluated_by_mentor_name(self):
        return self.evaluated_by_mentor.name if self.evaluated_by_mentor else None

    @property
    def evaluated_by_mentor_email(self):
        return self.evaluated_by_mentor.email if self.evaluated_by_mentor else None

class UserGroupMap(Base):
    __tablename__ = "user_group_map"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # admin / member / mentor

    __table_args__ = (UniqueConstraint("user_id", "group_id", name="unique_user_group"),)

class OTP(Base):
    __tablename__ = "otp"

    email = Column(String, primary_key=True, index=True)
    otp = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)