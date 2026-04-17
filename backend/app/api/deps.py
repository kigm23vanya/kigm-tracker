from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.core import TeacherSubjectAccess, User, UserRole


def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> User:
    user = None
    if x_user_id is not None:
        user = db.get(User, x_user_id)
    if user is None:
        user = db.query(User).filter(User.role == UserRole.student).order_by(User.id.asc()).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No authenticated user")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return current_user


def require_admin_or_curator(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.admin, UserRole.curator}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or curator role required")
    return current_user


def require_admin_or_teacher(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.admin, UserRole.teacher}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or teacher role required")
    return current_user


def has_teacher_subject_access(db: Session, teacher: User, subject_id: int | None) -> bool:
    if teacher.role == UserRole.admin:
        return True
    if teacher.role != UserRole.teacher or subject_id is None:
        return False
    return (
        db.query(TeacherSubjectAccess)
        .filter(
            TeacherSubjectAccess.teacher_id == teacher.id,
            TeacherSubjectAccess.subject_id == subject_id,
        )
        .first()
        is not None
    )


def ensure_group_scope_access(current_user: User, target_user: User) -> None:
    if current_user.role == UserRole.admin:
        return
    if current_user.role != UserRole.curator:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Curator or admin role required")
    if current_user.group_id is None or target_user.group_id != current_user.group_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Target user is outside curator group")
