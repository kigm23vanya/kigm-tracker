from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.core import User
from app.schemas.api import LeaderboardEntryOut, LeaderboardScope
from app.services.leaderboard import achievements_leaderboard, activity_leaderboard, grades_leaderboard

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/grades", response_model=list[LeaderboardEntryOut])
def get_grades_leaderboard(
    scope: LeaderboardScope = Query(default=LeaderboardScope.group),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LeaderboardEntryOut]:
    return grades_leaderboard(db, current_user, scope)


@router.get("/activity", response_model=list[LeaderboardEntryOut])
def get_activity_leaderboard(
    scope: LeaderboardScope = Query(default=LeaderboardScope.group),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LeaderboardEntryOut]:
    return activity_leaderboard(db, current_user, scope)


@router.get("/achievements", response_model=list[LeaderboardEntryOut])
def get_achievements_leaderboard(
    scope: LeaderboardScope = Query(default=LeaderboardScope.group),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LeaderboardEntryOut]:
    return achievements_leaderboard(db, current_user, scope)
