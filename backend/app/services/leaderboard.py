from sqlalchemy.orm import Session

from app.models.core import EventParticipation, Submission, User, UserAchievement, UserRole
from app.schemas.api import LeaderboardEntryOut, LeaderboardScope
from app.services.activity import ACTIVITY_POINTS_CONFIG, RARITY_WEIGHTS, calculate_event_points, calculate_submission_points
from app.services.experience import calculate_user_experience


def _scoped_students(db: Session, current_user: User, scope: LeaderboardScope) -> list[User]:
    query = db.query(User).filter(User.role == UserRole.student)
    if scope == LeaderboardScope.group and current_user.group_id is not None:
        query = query.filter(User.group_id == current_user.group_id)
    elif scope == LeaderboardScope.course:
        query = query.filter(User.course_number == current_user.course_number)
    return query.order_by(User.full_name.asc()).all()


def _rank(scores: list[tuple[int, str, float]]) -> list[LeaderboardEntryOut]:
    sorted_scores = sorted(scores, key=lambda item: item[2], reverse=True)
    return [
        LeaderboardEntryOut(position=index + 1, user_id=user_id, full_name=full_name, score=score)
        for index, (user_id, full_name, score) in enumerate(sorted_scores)
    ]


def grades_leaderboard(db: Session, current_user: User, scope: LeaderboardScope) -> list[LeaderboardEntryOut]:
    users = _scoped_students(db, current_user, scope)
    scores: list[tuple[int, str, float]] = []

    for user in users:
        submissions = db.query(Submission).filter(Submission.student_id == user.id).all()
        grades = [submission.assigned_grade for submission in submissions if submission.assigned_grade is not None]
        avg = sum(grades) / len(grades) if grades else 0.0
        scores.append((user.id, user.full_name, round(avg, 2)))

    return _rank(scores)


def activity_leaderboard(db: Session, current_user: User, scope: LeaderboardScope) -> list[LeaderboardEntryOut]:
    users = _scoped_students(db, current_user, scope)
    scores: list[tuple[int, str, float]] = []

    for user in users:
        experience_snapshot = calculate_user_experience(db, user)
        scores.append((user.id, user.full_name, float(experience_snapshot.experience)))

    return _rank(scores)


def achievements_leaderboard(db: Session, current_user: User, scope: LeaderboardScope) -> list[LeaderboardEntryOut]:
    users = _scoped_students(db, current_user, scope)
    scores: list[tuple[int, str, float]] = []

    for user in users:
        user_achievements = (
            db.query(UserAchievement)
            .filter(UserAchievement.user_id == user.id)
            .all()
        )

        weighted_score = sum(RARITY_WEIGHTS[item.achievement.rarity] for item in user_achievements)
        scores.append((user.id, user.full_name, float(weighted_score)))

    return _rank(scores)
