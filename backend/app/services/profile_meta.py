from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.core import StudyGroup, User, UserRole

ROLE_TITLES: dict[UserRole, str] = {
    UserRole.student: "студент",
    UserRole.curator: "куратор",
    UserRole.teacher: "преподаватель",
    UserRole.admin: "администратор",
}

PHONE_BY_EMAIL: dict[str, str] = {
    "st.student@kigm23.ru": "89996665267",
    "maria.petrova@kigm23.ru": "89990000001",
    "alina.kim@kigm23.ru": "89990000002",
    "oleg.ivanov@kigm23.ru": "89990000003",
    "nikita.smirnov@kigm23.ru": "89990000004",
    "sofia.romanova@kigm23.ru": "89990000005",
    "artem.belov@kigm23.ru": "89990000006",
    "ekaterina.orlova@kigm23.ru": "89990000007",
    "denis.morozov@kigm23.ru": "89990000008",
    "polina.fadeeva@kigm23.ru": "89990000009",
    "kirill.volkov@kigm23.ru": "89990000010",
    "vladislav.novikov@kigm23.ru": "89990000011",
    "daria.kuznetsova@kigm23.ru": "89990000012",
    "ilya.egorov@kigm23.ru": "89990000013",
    "yana.stepanova@kigm23.ru": "89990000014",
    "maksim.lebedev@kigm23.ru": "89990000015",
    "elena.gracheva@kigm23.ru": "89990000016",
    "roman.kozlov@kigm23.ru": "89990000017",
    "valeria.semenova@kigm23.ru": "89990000018",
    "georgiy.melnikov@kigm23.ru": "89990000019",
    "curator.ivanova@kigm23.ru": "89991110001",
    "curator.petrov@kigm23.ru": "89991110002",
    "teacher.math@kigm23.ru": "89992220001",
    "teacher.network@kigm23.ru": "89992220002",
}

WORK_YEARS_BY_EMAIL: dict[str, int] = {
    "teacher.math@kigm23.ru": 12,
    "teacher.network@kigm23.ru": 27,
    "curator.ivanova@kigm23.ru": 9,
    "curator.petrov@kigm23.ru": 17,
}

# Streak for handled groups. Curators and teachers may accumulate it over years.
CURATED_GROUP_STREAK_BY_EMAIL: dict[str, int] = {
    "teacher.math@kigm23.ru": 1,
    "teacher.network@kigm23.ru": 3,
    "curator.ivanova@kigm23.ru": 2,
    "curator.petrov@kigm23.ru": 4,
}

TEACHER_CURATOR_GROUP_BY_EMAIL: dict[str, str | None] = {
    "teacher.math@kigm23.ru": None,
    "teacher.network@kigm23.ru": "КИГМ-202",
}


def get_role_title(role: UserRole) -> str:
    return ROLE_TITLES.get(role, role.value)


def get_phone_for_user(user: User) -> str | None:
    if user.role == UserRole.admin:
        return None
    return PHONE_BY_EMAIL.get(user.email)


def get_work_years_for_user(user: User) -> int:
    return WORK_YEARS_BY_EMAIL.get(user.email, 0)


def get_curated_group_streak_for_user(user: User) -> int:
    return CURATED_GROUP_STREAK_BY_EMAIL.get(user.email, 0)


def get_teacher_curator_group_name(db: Session, user: User) -> str | None:
    if user.role == UserRole.curator and user.group_id is not None:
        group = db.get(StudyGroup, user.group_id)
        return group.name if group else None
    if user.role == UserRole.teacher:
        return TEACHER_CURATOR_GROUP_BY_EMAIL.get(user.email)
    return None
