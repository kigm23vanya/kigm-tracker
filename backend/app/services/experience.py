from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.core import Event, EventParticipation, Submission, User, UserAchievement, UserRole
from app.services.profile_meta import (
    get_curated_group_streak_for_user,
    get_teacher_curator_group_name,
    get_work_years_for_user,
)

GRADE_XP_MAP = {
    2: 0,
    3: 5,
    4: 10,
    5: 15,
}

GRADE_STREAK_MULTIPLIER = {
    3: 0.5,
    4: 0.10,
    5: 0.25,
}

MASTERING_BONUS_PER_COURSE = 500
ADMIN_INFINITY_XP = 10**12


@dataclass
class ExperienceSnapshot:
    experience: int
    level: int | None
    progress_percent: float
    current_level_xp: int
    next_level_xp: int | None
    infinite: bool


def _is_exam_submission(submission: Submission) -> bool:
    assignment_title = submission.assignment.title.lower()
    return "экзамен" in assignment_title or "exam" in assignment_title


def _calculate_student_grade_experience(submissions: list[Submission]) -> int:
    total_xp = 0
    current_grade: int | None = None
    grade_streak = 0
    lose_streak_twos = 0

    ordered_submissions = sorted(submissions, key=lambda item: item.last_synced_at)
    for submission in ordered_submissions:
        raw_grade = submission.assigned_grade
        if raw_grade is None:
            continue

        grade = int(round(raw_grade))
        base_xp = GRADE_XP_MAP.get(grade, 0)
        if _is_exam_submission(submission):
            base_xp *= 3

        total_xp += base_xp

        if grade == current_grade:
            grade_streak += 1
        else:
            current_grade = grade
            grade_streak = 1

        if grade_streak >= 3 and grade in GRADE_STREAK_MULTIPLIER and base_xp > 0:
            total_xp += int(round(base_xp * GRADE_STREAK_MULTIPLIER[grade]))

        if grade == 2:
            lose_streak_twos += 1
            if lose_streak_twos >= 3:
                total_xp -= 10
        else:
            lose_streak_twos = 0

    return total_xp


def _calculate_student_event_experience(participations: list[EventParticipation]) -> int:
    event_xp = 0
    for participation in participations:
        event_xp += participation.points_awarded
        if participation.participation_status.value in {"registered", "participated"}:
            event_xp += max(0, participation.event.activity_points // 2)
    return event_xp


def _calculate_teacher_experience(db: Session, user: User) -> int:
    work_years = get_work_years_for_user(user)
    curated_group_name = get_teacher_curator_group_name(db, user)
    curated_group_streak = get_curated_group_streak_for_user(user)

    achievements_count = db.query(UserAchievement).filter(UserAchievement.user_id == user.id).count()
    organized_events = db.query(Event).filter(Event.organizer == user.full_name).count()

    base_xp = work_years * 10000
    if curated_group_name:
        base_xp += 1000
    base_xp += organized_events * 500

    multiplier = 1.0
    multiplier += curated_group_streak * 0.10
    multiplier += (work_years // 5) * 0.25
    multiplier += achievements_count * 0.50

    return int(round(base_xp * multiplier))


def _calculate_curator_experience(db: Session, user: User) -> int:
    work_years = get_work_years_for_user(user)
    curated_group_streak = get_curated_group_streak_for_user(user)
    achievements_count = db.query(UserAchievement).filter(UserAchievement.user_id == user.id).count()

    base_xp = 1000 + work_years * 10000
    multiplier = 1.0 + curated_group_streak * 0.10 + (work_years // 5) * 0.25 + achievements_count * 0.20
    return int(round(base_xp * multiplier))


def _experience_for_level(level: int) -> int:
    return 1000 + (level - 1) * 250


def _calculate_level_snapshot(experience: int) -> ExperienceSnapshot:
    if experience <= 0:
        return ExperienceSnapshot(
            experience=0,
            level=1,
            progress_percent=0.0,
            current_level_xp=0,
            next_level_xp=_experience_for_level(1),
            infinite=False,
        )

    remaining = experience
    level = 1
    needed = _experience_for_level(level)

    while remaining >= needed:
        remaining -= needed
        level += 1
        needed = _experience_for_level(level)

    progress = round((remaining / needed) * 100, 2) if needed > 0 else 100.0
    return ExperienceSnapshot(
        experience=experience,
        level=level,
        progress_percent=progress,
        current_level_xp=remaining,
        next_level_xp=needed,
        infinite=False,
    )


def calculate_user_experience(db: Session, user: User) -> ExperienceSnapshot:
    if user.role == UserRole.admin:
        return ExperienceSnapshot(
            experience=ADMIN_INFINITY_XP,
            level=None,
            progress_percent=100.0,
            current_level_xp=ADMIN_INFINITY_XP,
            next_level_xp=None,
            infinite=True,
        )

    if user.role == UserRole.student:
        submissions = db.query(Submission).filter(Submission.student_id == user.id).all()
        participations = db.query(EventParticipation).filter(EventParticipation.user_id == user.id).all()

        grade_xp = _calculate_student_grade_experience(submissions)
        event_xp = _calculate_student_event_experience(participations)
        mastery_xp = max(user.course_number - 1, 0) * MASTERING_BONUS_PER_COURSE

        total_xp = max(0, grade_xp + event_xp + mastery_xp)
        return _calculate_level_snapshot(total_xp)

    if user.role == UserRole.teacher:
        return _calculate_level_snapshot(_calculate_teacher_experience(db, user))

    # Curator role
    return _calculate_level_snapshot(_calculate_curator_experience(db, user))
