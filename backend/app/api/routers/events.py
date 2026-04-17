from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_group_scope_access, get_current_user, has_teacher_subject_access
from app.core.database import get_db
from app.models.core import Event, EventParticipation, EventSubjectLink, ParticipationStatus, Subject, User, UserRole
from app.schemas.api import EventCreate, EventOut, EventParticipationCreate, EventParticipationOut, EventParticipationUpdate, EventUpdate
from app.services.achievements import award_on_event_participation

router = APIRouter(prefix="/events", tags=["events"])


def _event_subject_id(event: Event) -> int | None:
    if not event.subject_links:
        return None
    return event.subject_links[0].subject_id


def _set_event_subject(db: Session, event: Event, subject_id: int | None) -> None:
    existing = db.query(EventSubjectLink).filter(EventSubjectLink.event_id == event.id).first()

    if subject_id is None:
        if existing is not None:
            db.delete(existing)
        return

    subject = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    if existing is None:
        db.add(EventSubjectLink(event_id=event.id, subject_id=subject_id))
    else:
        existing.subject_id = subject_id


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


def _ensure_event_management_access(
    db: Session,
    current_user: User,
    *,
    current_subject_id: int | None,
    target_subject_id: int | None,
) -> None:
    if current_user.role == UserRole.admin:
        return

    if current_user.role != UserRole.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin or teacher can edit events")

    subject_id = target_subject_id if target_subject_id is not None else current_subject_id
    if subject_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher can manage only events linked to a subject",
        )

    if not has_teacher_subject_access(db, current_user, subject_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher has no access to this subject",
        )


@router.get("", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)) -> list[EventOut]:
    events = db.query(Event).order_by(Event.starts_at.desc()).all()
    return [_event_out(event) for event in events]


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)) -> EventOut:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return _event_out(event)


@router.post("", response_model=EventOut)
def create_event(
    payload: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EventOut:
    _ensure_event_management_access(
        db,
        current_user,
        current_subject_id=None,
        target_subject_id=payload.subject_id,
    )

    event_payload = payload.model_dump(exclude={"subject_id"})
    event = Event(**event_payload)
    db.add(event)
    db.commit()
    db.refresh(event)

    _set_event_subject(db, event, payload.subject_id)
    db.commit()
    db.refresh(event)
    return _event_out(event)


@router.put("/{event_id}", response_model=EventOut)
def update_event(
    event_id: int,
    payload: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EventOut:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    current_subject_id = _event_subject_id(event)
    _ensure_event_management_access(
        db,
        current_user,
        current_subject_id=current_subject_id,
        target_subject_id=payload.subject_id,
    )

    for key, value in payload.model_dump(exclude_none=True).items():
        if key == "subject_id":
            continue
        setattr(event, key, value)

    if "subject_id" in payload.model_fields_set:
        _set_event_subject(db, event, payload.subject_id)

    db.commit()
    db.refresh(event)
    return _event_out(event)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    _ensure_event_management_access(
        db,
        current_user,
        current_subject_id=_event_subject_id(event),
        target_subject_id=None,
    )

    db.delete(event)
    db.commit()


@router.post("/{event_id}/participation", response_model=EventParticipationOut)
def register_participation(
    event_id: int,
    payload: EventParticipationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EventParticipationOut:
    if current_user.role == UserRole.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student role has read-only access")

    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    participation = (
        db.query(EventParticipation)
        .filter(EventParticipation.event_id == event_id, EventParticipation.user_id == current_user.id)
        .first()
    )
    if participation is None:
        participation = EventParticipation(
            event_id=event_id,
            user_id=current_user.id,
            participation_status=payload.participation_status,
            points_awarded=0,
        )
        db.add(participation)
    else:
        participation.participation_status = payload.participation_status

    db.commit()
    db.refresh(participation)

    award_on_event_participation(db, current_user, participation)

    return EventParticipationOut(
        id=participation.id,
        event_id=event_id,
        event_title=event.title,
        date=event.starts_at,
        participation_status=participation.participation_status,
        result=participation.result,
        points_awarded=participation.points_awarded,
    )


@router.put("/{event_id}/participation/{user_id}", response_model=EventParticipationOut)
def update_participation(
    event_id: int,
    user_id: int,
    payload: EventParticipationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EventParticipationOut:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    target_user = db.get(User, user_id)
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if current_user.role == UserRole.admin:
        pass
    elif current_user.role == UserRole.curator:
        ensure_group_scope_access(current_user, target_user)
    elif current_user.role == UserRole.teacher:
        if not has_teacher_subject_access(db, current_user, _event_subject_id(event)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher has no access to this event subject",
            )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student role has read-only access")

    participation = (
        db.query(EventParticipation)
        .filter(EventParticipation.event_id == event_id, EventParticipation.user_id == user_id)
        .first()
    )
    if participation is None:
        participation = EventParticipation(
            event_id=event_id,
            user_id=user_id,
            participation_status=ParticipationStatus.registered,
            points_awarded=0,
        )
        db.add(participation)

    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(participation, key, value)

    db.commit()
    db.refresh(participation)

    award_on_event_participation(db, target_user, participation)

    return EventParticipationOut(
        id=participation.id,
        event_id=event_id,
        event_title=event.title,
        date=event.starts_at,
        participation_status=participation.participation_status,
        result=participation.result,
        points_awarded=participation.points_awarded,
    )
