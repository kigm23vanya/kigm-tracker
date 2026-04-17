from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user, require_admin_or_curator
from app.core.database import get_db
from app.models.core import Assignment, Event, EventParticipation, GoogleCourse, Subject, Submission, User, UserAchievement, UserRole
from app.schemas.api import EventOut, EventParticipationOut, ExperienceOut, ProfileOut, SubjectGradeOut, TeacherProfileOut, UserAchievementOut, UserOut
from app.services.experience import calculate_user_experience
from app.services.profile_meta import (
    get_phone_for_user,
    get_role_title,
    get_teacher_curator_group_name,
    get_work_years_for_user,
)

router = APIRouter(prefix="/profile", tags=["profile"])


def _event_out(event: Event) -> EventOut:
    link = event.subject_links[0] if event.subject_links else None
    return EventOut(
        id=event.id,
        title=event.title,
        description=event.description,
        starts_at=event.starts_at,
        location=event.location,
        organizer=event.organizer,
        activity_points=event.activity_points,
        subject_id=link.subject_id if link else None,
        subject_name=link.subject.name if link and link.subject else None,
    )


def _profile_summary_for_user(db: Session, user: User) -> ProfileOut:
    participations = db.query(EventParticipation).filter(EventParticipation.user_id == user.id).all()
    achievement_count = db.query(UserAchievement).filter(UserAchievement.user_id == user.id).count()

    # Profile shows explicit activity points awarded by event moderators/admin.
    activity_points = sum(item.points_awarded for item in participations)
    experience_snapshot = calculate_user_experience(db, user)

    teacher_profile: TeacherProfileOut | None = None
    if user.role == UserRole.teacher:
        organized_events = (
            db.query(Event)
            .filter(Event.organizer == user.full_name)
            .order_by(Event.starts_at.desc())
            .all()
        )
        teacher_profile = TeacherProfileOut(
            curator_group=get_teacher_curator_group_name(db, user),
            work_experience_years=get_work_years_for_user(user),
            organized_events=[_event_out(event) for event in organized_events],
        )

    return ProfileOut(
        user=user,
        title=get_role_title(user.role),
        phone=get_phone_for_user(user),
        total_achievements=achievement_count,
        activity_points=activity_points,
        experience=ExperienceOut(
            experience=experience_snapshot.experience,
            level=experience_snapshot.level,
            progress_percent=experience_snapshot.progress_percent,
            current_level_xp=experience_snapshot.current_level_xp,
            next_level_xp=experience_snapshot.next_level_xp,
            infinite=experience_snapshot.infinite,
        ),
        teacher_profile=teacher_profile,
    )


def _profile_achievements_for_user(db: Session, user_id: int) -> list[UserAchievement]:
    return (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == user_id)
        .order_by(UserAchievement.awarded_at.desc())
        .all()
    )


def _profile_grades_for_user(db: Session, user_id: int) -> list[SubjectGradeOut]:
    subjects = db.query(Subject).order_by(Subject.name.asc()).all()
    result: list[SubjectGradeOut] = []

    for subject in subjects:
        course_ids = [course.id for course in db.query(GoogleCourse).filter(GoogleCourse.subject_id == subject.id).all()]
        if not course_ids:
            continue

        submissions = (
            db.query(Submission)
            .join(Submission.assignment)
            .filter(Submission.student_id == user_id)
            .filter(Assignment.course_id.in_(course_ids))
            .all()
        )
        grades = [item.assigned_grade for item in submissions if item.assigned_grade is not None]
        final_grade = round(grades[-1], 2) if grades else None
        average_grade = round(sum(grades) / len(grades), 2) if grades else None
        completed = len([item for item in submissions if item.submission_state.value in {"TURNED_IN", "RETURNED"}])

        result.append(
            SubjectGradeOut(
                subject_name=subject.name,
                final_grade=final_grade,
                average_grade=average_grade,
                completed_assignments=completed,
            )
        )

    return result


def _profile_events_for_user(db: Session, user_id: int) -> list[EventParticipationOut]:
    participations = (
        db.query(EventParticipation)
        .join(EventParticipation.event)
        .filter(EventParticipation.user_id == user_id)
        .order_by(EventParticipation.id.desc())
        .all()
    )

    return [
        EventParticipationOut(
            id=item.id,
            event_id=item.event_id,
            event_title=item.event.title,
            date=item.event.starts_at,
            participation_status=item.participation_status,
            result=item.result,
            points_awarded=item.points_awarded,
        )
        for item in participations
    ]


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("", response_model=ProfileOut)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileOut:
    return _profile_summary_for_user(db, current_user)


@router.get("/achievements", response_model=list[UserAchievementOut])
def get_profile_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserAchievement]:
    return _profile_achievements_for_user(db, current_user.id)


@router.get("/grades", response_model=list[SubjectGradeOut])
def get_profile_grades(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SubjectGradeOut]:
    return _profile_grades_for_user(db, current_user.id)


@router.get("/events", response_model=list[EventParticipationOut])
def get_profile_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[EventParticipationOut]:
    return _profile_events_for_user(db, current_user.id)


@router.get("/group/students", response_model=list[UserOut])
def get_group_students(
    group_id: int | None = Query(default=None),
    current_user: User = Depends(require_admin_or_curator),
    db: Session = Depends(get_db),
) -> list[User]:
    query = db.query(User).filter(User.role == UserRole.student)

    if current_user.role == UserRole.curator:
        if current_user.group_id is None:
            return []
        query = query.filter(User.group_id == current_user.group_id)
    elif group_id is not None:
        query = query.filter(User.group_id == group_id)

    return query.order_by(User.full_name.asc()).all()


@router.get("/users", response_model=list[UserOut])
def list_users_for_profile_browse(
    role: UserRole | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[User]:
    query = db.query(User)

    if role is not None:
        query = query.filter(User.role == role)

    if current_user.role == UserRole.curator and current_user.group_id is not None:
        # Curator sees staff + students of the curator group.
        query = query.filter((User.role != UserRole.student) | (User.group_id == current_user.group_id))

    return query.order_by(User.full_name.asc()).all()


@router.get("/{user_id}", response_model=ProfileOut)
def get_profile_by_user_id(
    user_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileOut:
    user = _get_user_or_404(db, user_id)
    return _profile_summary_for_user(db, user)


@router.get("/{user_id}/achievements", response_model=list[UserAchievementOut])
def get_profile_achievements_by_user_id(
    user_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserAchievement]:
    _ = _get_user_or_404(db, user_id)
    return _profile_achievements_for_user(db, user_id)


@router.get("/{user_id}/grades", response_model=list[SubjectGradeOut])
def get_profile_grades_by_user_id(
    user_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SubjectGradeOut]:
    _ = _get_user_or_404(db, user_id)
    return _profile_grades_for_user(db, user_id)


@router.get("/{user_id}/events", response_model=list[EventParticipationOut])
def get_profile_events_by_user_id(
    user_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[EventParticipationOut]:
    _ = _get_user_or_404(db, user_id)
    return _profile_events_for_user(db, user_id)
