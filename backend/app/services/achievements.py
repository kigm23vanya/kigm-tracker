from datetime import datetime

from sqlalchemy.orm import Session

from app.models.core import Achievement, AchievementRarity, EventParticipation, Submission, User, UserAchievement
from app.services.activity import ACTIVITY_POINTS_CONFIG

DEFAULT_ACHIEVEMENTS: list[dict[str, str | AchievementRarity]] = [
    {
        "code": "enrollment",
        "title": "Зачисление",
        "description": "Студент зарегистрирован в системе",
        "rarity": AchievementRarity.common,
    },
    {
        "code": "first_grade_2",
        "title": "Первая двойка",
        "description": "Получена первая оценка 2",
        "rarity": AchievementRarity.common,
    },
    {
        "code": "first_grade_3",
        "title": "Первая тройка",
        "description": "Получена первая оценка 3",
        "rarity": AchievementRarity.common,
    },
    {
        "code": "first_grade_4",
        "title": "Первая четверка",
        "description": "Получена первая оценка 4",
        "rarity": AchievementRarity.rare,
    },
    {
        "code": "first_grade_5",
        "title": "Первая пятерка",
        "description": "Получена первая оценка 5",
        "rarity": AchievementRarity.epic,
    },
    {
        "code": "event_participation",
        "title": "Участие в мероприятии",
        "description": "Студент впервые принял участие в мероприятии",
        "rarity": AchievementRarity.rare,
    },
    {
        "code": "event_prize",
        "title": "Призовое место",
        "description": "Получено призовое место в мероприятии",
        "rarity": AchievementRarity.legendary,
    },
    {
        "code": "course_upgrade",
        "title": "Новый курс",
        "description": "Студент переведен на новый курс",
        "rarity": AchievementRarity.epic,
    },
    {
        "code": "teacher_first_event",
        "title": "Первое мероприятие",
        "description": "Преподаватель организовал первое мероприятие",
        "rarity": AchievementRarity.rare,
    },
]

for years in range(5, 51, 5):
    DEFAULT_ACHIEVEMENTS.append(
        {
            "code": f"teacher_service_{years}",
            "title": f"Выслуга лет: {years}",
            "description": f"{years} лет работы в колледже",
            "rarity": AchievementRarity.epic if years >= 25 else AchievementRarity.rare,
        }
    )


def seed_achievements(db: Session) -> None:
    existing_codes = {code for (code,) in db.query(Achievement.code).all()}
    for achievement in DEFAULT_ACHIEVEMENTS:
        if achievement["code"] not in existing_codes:
            db.add(
                Achievement(
                    code=achievement["code"],
                    title=achievement["title"],
                    description=achievement["description"],
                    rarity=achievement["rarity"],
                )
            )
    db.commit()


def award_by_code(db: Session, user: User, code: str, reason: str | None = None) -> bool:
    achievement = db.query(Achievement).filter(Achievement.code == code).first()
    if not achievement:
        return False

    exists = (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == user.id, UserAchievement.achievement_id == achievement.id)
        .first()
    )
    if exists:
        return False

    user_achievement = UserAchievement(
        user_id=user.id,
        achievement_id=achievement.id,
        awarded_at=datetime.utcnow(),
        reason=reason,
    )
    db.add(user_achievement)
    db.commit()
    return True


def award_on_registration(db: Session, user: User) -> bool:
    return award_by_code(db, user, "enrollment", "Регистрация в системе")


def award_on_course_upgrade(db: Session, user: User, old_course: int, new_course: int) -> bool:
    if new_course > old_course:
        return award_by_code(db, user, "course_upgrade", f"Переход с {old_course} на {new_course} курс")
    return False


def award_on_submission_grade(db: Session, user: User, submission: Submission) -> bool:
    if submission.assigned_grade is None:
        return False

    grade = int(submission.assigned_grade)
    mapping = {
        2: "first_grade_2",
        3: "first_grade_3",
        4: "first_grade_4",
        5: "first_grade_5",
    }
    code = mapping.get(grade)
    if not code:
        return False

    return award_by_code(db, user, code, f"Первая оценка {grade}")


def award_on_event_participation(db: Session, user: User, participation: EventParticipation) -> int:
    awarded = 0
    if participation.participation_status.value in {"registered", "participated"}:
        if award_by_code(db, user, "event_participation", "Регистрация участия"):
            awarded += ACTIVITY_POINTS_CONFIG["achievement_awarded"]

    if participation.result:
        normalized = participation.result.lower()
        if "1" in normalized or "приз" in normalized or "winner" in normalized:
            if award_by_code(db, user, "event_prize", "Получено призовое место"):
                awarded += ACTIVITY_POINTS_CONFIG["achievement_awarded"]

    return awarded
