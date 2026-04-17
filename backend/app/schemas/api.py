from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field

from app.models.core import AchievementRarity, ParticipationStatus, SubmissionState, UserRole


class LeaderboardScope(str, Enum):
    group = "group"
    course = "course"
    college = "college"


class AuthGoogleRequest(BaseModel):
    google_user_id: str | None = None
    email: EmailStr
    full_name: str
    avatar_url: str | None = None


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    id: int
    google_user_id: str | None
    full_name: str
    email: EmailStr
    role: UserRole
    group_id: int | None
    course_number: int
    avatar_url: str | None

    model_config = {"from_attributes": True}


class AuthLoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class AchievementOut(BaseModel):
    id: int
    code: str
    title: str
    description: str
    rarity: AchievementRarity

    model_config = {"from_attributes": True}


class UserAchievementOut(BaseModel):
    id: int
    achievement: AchievementOut
    awarded_at: datetime
    reason: str | None

    model_config = {"from_attributes": True}


class SubjectGradeOut(BaseModel):
    subject_name: str
    final_grade: float | None
    average_grade: float | None
    completed_assignments: int


class EventOut(BaseModel):
    id: int
    title: str
    description: str | None
    starts_at: datetime
    location: str | None
    organizer: str | None
    activity_points: int
    subject_id: int | None = None
    subject_name: str | None = None

    model_config = {"from_attributes": True}


class EventCreate(BaseModel):
    title: str
    description: str | None = None
    starts_at: datetime
    location: str | None = None
    organizer: str | None = None
    activity_points: int = 0
    subject_id: int | None = None


class EventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    starts_at: datetime | None = None
    location: str | None = None
    organizer: str | None = None
    activity_points: int | None = None
    subject_id: int | None = None


class EventParticipationOut(BaseModel):
    id: int
    event_id: int
    event_title: str
    date: datetime
    participation_status: ParticipationStatus
    result: str | None
    points_awarded: int


class ExperienceOut(BaseModel):
    experience: int
    level: int | None
    progress_percent: float
    current_level_xp: int
    next_level_xp: int | None
    infinite: bool = False


class TeacherProfileOut(BaseModel):
    curator_group: str | None
    work_experience_years: int
    organized_events: list[EventOut]


class EventParticipationCreate(BaseModel):
    participation_status: ParticipationStatus = ParticipationStatus.registered


class EventParticipationUpdate(BaseModel):
    participation_status: ParticipationStatus | None = None
    result: str | None = None
    points_awarded: int | None = None


class AssignmentCardOut(BaseModel):
    id: int
    course_title: str
    assignment_title: str
    assignment_description: str | None
    due_date: datetime | None
    max_points: float | None
    submission_state: SubmissionState | None
    draft_grade: float | None
    assigned_grade: float | None
    comment: str | None = None


class SubmissionOut(BaseModel):
    id: int
    google_submission_id: str
    assignment_id: int
    student_id: int
    submission_state: SubmissionState
    draft_grade: float | None
    assigned_grade: float | None
    last_synced_at: datetime

    model_config = {"from_attributes": True}


class SubmissionGradeUpdate(BaseModel):
    draft_grade: float | None = None
    assigned_grade: float | None = None


class UserAchievementAssignRequest(BaseModel):
    achievement_code: str = Field(min_length=1, max_length=120)
    reason: str | None = Field(default=None, max_length=255)


class AssignmentCommentOut(BaseModel):
    id: int
    submission_id: int
    author_id: int
    comment_text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignmentCommentCreate(BaseModel):
    comment_text: str = Field(min_length=1, max_length=5000)


class ProfileOut(BaseModel):
    user: UserOut
    title: str
    phone: str | None
    total_achievements: int
    activity_points: int
    experience: ExperienceOut
    teacher_profile: TeacherProfileOut | None = None


class LeaderboardEntryOut(BaseModel):
    position: int
    user_id: int
    full_name: str
    score: float


class SyncResultOut(BaseModel):
    synced_courses: int
    synced_assignments: int
    synced_submissions: int
