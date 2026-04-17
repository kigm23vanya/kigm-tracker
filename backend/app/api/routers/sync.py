from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.core import User
from app.schemas.api import SyncResultOut
from app.services.achievements import award_on_submission_grade
from app.services.classroom_sync import ClassroomSyncService

router = APIRouter(prefix="/sync", tags=["sync"])
service = ClassroomSyncService()


@router.post("/classroom", response_model=SyncResultOut)
def sync_classroom(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> SyncResultOut:
    result = service.sync_all_for_user(db, current_user)

    for submission in current_user.submissions:
        award_on_submission_grade(db, current_user, submission)

    return result


@router.post("/classroom/course/{course_id}", response_model=SyncResultOut)
def sync_classroom_course(
    course_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> SyncResultOut:
    result = service.sync_course_for_user(db, current_user, course_id)

    for submission in current_user.submissions:
        award_on_submission_grade(db, current_user, submission)

    return result
