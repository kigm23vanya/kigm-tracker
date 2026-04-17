from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ensure_group_scope_access, get_current_user, require_admin_or_curator
from app.core.database import get_db
from app.models.core import Achievement, User, UserAchievement, UserRole
from app.schemas.api import AchievementOut, UserAchievementAssignRequest, UserAchievementOut

router = APIRouter(prefix="/achievements", tags=["achievements"])


@router.get("", response_model=list[AchievementOut])
def list_achievements(db: Session = Depends(get_db)) -> list[Achievement]:
    return db.query(Achievement).order_by(Achievement.id.asc()).all()


@router.get("/me", response_model=list[UserAchievementOut])
def list_my_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserAchievement]:
    return (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == current_user.id)
        .order_by(UserAchievement.awarded_at.desc())
        .all()
    )


@router.post("/users/{user_id}", response_model=UserAchievementOut)
def assign_user_achievement(
    user_id: int,
    payload: UserAchievementAssignRequest,
    current_user: User = Depends(require_admin_or_curator),
    db: Session = Depends(get_db),
) -> UserAchievement:
    target_user = db.get(User, user_id)
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if current_user.role != UserRole.admin:
        if target_user.role != UserRole.student:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Curator can manage only students")
        ensure_group_scope_access(current_user, target_user)

    achievement = db.query(Achievement).filter(Achievement.code == payload.achievement_code).first()
    if achievement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Achievement code not found")

    existing = (
        db.query(UserAchievement)
        .filter(
            UserAchievement.user_id == target_user.id,
            UserAchievement.achievement_id == achievement.id,
        )
        .first()
    )
    if existing is not None:
        return existing

    user_achievement = UserAchievement(
        user_id=target_user.id,
        achievement_id=achievement.id,
        awarded_at=datetime.utcnow(),
        reason=payload.reason,
    )
    db.add(user_achievement)
    db.commit()
    db.refresh(user_achievement)
    return user_achievement


@router.delete("/users/{user_id}/{achievement_code}", response_model=list[UserAchievementOut])
def revoke_user_achievement(
    user_id: int,
    achievement_code: str,
    current_user: User = Depends(require_admin_or_curator),
    db: Session = Depends(get_db),
) -> list[UserAchievement]:
    target_user = db.get(User, user_id)
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if current_user.role != UserRole.admin:
        if target_user.role != UserRole.student:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Curator can manage only students")
        ensure_group_scope_access(current_user, target_user)

    achievement = db.query(Achievement).filter(Achievement.code == achievement_code).first()
    if achievement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Achievement code not found")

    user_achievement = (
        db.query(UserAchievement)
        .filter(
            UserAchievement.user_id == target_user.id,
            UserAchievement.achievement_id == achievement.id,
        )
        .first()
    )
    if user_achievement is not None:
        db.delete(user_achievement)
        db.commit()

    return (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == target_user.id)
        .order_by(UserAchievement.awarded_at.desc())
        .all()
    )
