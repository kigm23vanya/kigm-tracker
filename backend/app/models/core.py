from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, Enum):
    student = "student"
    curator = "curator"
    admin = "admin"
    teacher = "teacher"


class AchievementRarity(str, Enum):
    common = "common"
    rare = "rare"
    epic = "epic"
    legendary = "legendary"


class SubmissionState(str, Enum):
    new = "NEW"
    created = "CREATED"
    turned_in = "TURNED_IN"
    returned = "RETURNED"
    reclaimed = "RECLAIMED_BY_STUDENT"


class ParticipationStatus(str, Enum):
    none = "none"
    registered = "registered"
    participated = "participated"


class StudyGroup(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    course_number: Mapped[int] = mapped_column(Integer)

    users: Mapped[list[User]] = relationship(back_populates="group")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)

    courses: Mapped[list[GoogleCourse]] = relationship(back_populates="subject")
    teacher_subject_accesses: Mapped[list[TeacherSubjectAccess]] = relationship(back_populates="subject")
    event_subject_links: Mapped[list[EventSubjectLink]] = relationship(back_populates="subject")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_user_id: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), default=UserRole.student, nullable=False)
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    course_number: Mapped[int] = mapped_column(Integer, default=1)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    group: Mapped[StudyGroup | None] = relationship(back_populates="users")
    submissions: Mapped[list[Submission]] = relationship(back_populates="student")
    event_participation: Mapped[list[EventParticipation]] = relationship(back_populates="user")
    user_achievements: Mapped[list[UserAchievement]] = relationship(back_populates="user")
    comments: Mapped[list[AssignmentComment]] = relationship(back_populates="author")
    teacher_subject_accesses: Mapped[list[TeacherSubjectAccess]] = relationship(back_populates="teacher")


class GoogleCourse(Base):
    __tablename__ = "google_courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_course_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("subjects.id"), nullable=True)

    subject: Mapped[Subject | None] = relationship(back_populates="courses")
    assignments: Mapped[list[Assignment]] = relationship(back_populates="course")


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_coursework_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("google_courses.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    max_points: Mapped[float | None] = mapped_column(Float, nullable=True)
    state: Mapped[str] = mapped_column(String(32), default="PUBLISHED")

    course: Mapped[GoogleCourse] = relationship(back_populates="assignments")
    submissions: Mapped[list[Submission]] = relationship(back_populates="assignment")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_submission_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    submission_state: Mapped[SubmissionState] = mapped_column(SqlEnum(SubmissionState), default=SubmissionState.new)
    draft_grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    assigned_grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    assignment: Mapped[Assignment] = relationship(back_populates="submissions")
    student: Mapped[User] = relationship(back_populates="submissions")
    comments: Mapped[list[AssignmentComment]] = relationship(back_populates="submission")

    __table_args__ = (UniqueConstraint("assignment_id", "student_id", name="uq_submission_per_assignment_student"),)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organizer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    activity_points: Mapped[int] = mapped_column(Integer, default=0)

    participation: Mapped[list[EventParticipation]] = relationship(back_populates="event")
    subject_links: Mapped[list[EventSubjectLink]] = relationship(back_populates="event")


class TeacherSubjectAccess(Base):
    __tablename__ = "teacher_subject_access"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)

    teacher: Mapped[User] = relationship(back_populates="teacher_subject_accesses")
    subject: Mapped[Subject] = relationship(back_populates="teacher_subject_accesses")

    __table_args__ = (UniqueConstraint("teacher_id", "subject_id", name="uq_teacher_subject_access"),)


class EventSubjectLink(Base):
    __tablename__ = "event_subject_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)

    event: Mapped[Event] = relationship(back_populates="subject_links")
    subject: Mapped[Subject] = relationship(back_populates="event_subject_links")

    __table_args__ = (UniqueConstraint("event_id", name="uq_event_subject_link"),)


class EventParticipation(Base):
    __tablename__ = "event_participation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    participation_status: Mapped[ParticipationStatus] = mapped_column(
        SqlEnum(ParticipationStatus),
        default=ParticipationStatus.registered,
    )
    result: Mapped[str | None] = mapped_column(String(255), nullable=True)
    points_awarded: Mapped[int] = mapped_column(Integer, default=0)

    event: Mapped[Event] = relationship(back_populates="participation")
    user: Mapped[User] = relationship(back_populates="event_participation")

    __table_args__ = (UniqueConstraint("event_id", "user_id", name="uq_event_user"),)


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    rarity: Mapped[AchievementRarity] = mapped_column(SqlEnum(AchievementRarity), default=AchievementRarity.common)

    user_achievements: Mapped[list[UserAchievement]] = relationship(back_populates="achievement")


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id"))
    awarded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped[User] = relationship(back_populates="user_achievements")
    achievement: Mapped[Achievement] = relationship(back_populates="user_achievements")

    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)


class AssignmentComment(Base):
    __tablename__ = "assignment_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    comment_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    submission: Mapped[Submission] = relationship(back_populates="comments")
    author: Mapped[User] = relationship(back_populates="comments")
