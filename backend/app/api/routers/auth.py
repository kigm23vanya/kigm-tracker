from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.core import StudyGroup, User, UserRole
from app.schemas.api import AuthGoogleRequest, AuthLoginOut, AuthLoginRequest, UserOut
from app.services.achievements import award_on_registration

router = APIRouter(prefix="/auth", tags=["auth"])

DEMO_PASSWORDS: dict[str, str] = {
    "st.student@kigm23.ru": "student2026",
    "maria.petrova@kigm23.ru": "maria2026",
    "alina.kim@kigm23.ru": "alina2026",
    "oleg.ivanov@kigm23.ru": "oleg2026",
    "nikita.smirnov@kigm23.ru": "nikita2026",
    "sofia.romanova@kigm23.ru": "sofia2026",
    "artem.belov@kigm23.ru": "artem2026",
    "ekaterina.orlova@kigm23.ru": "ekaterina2026",
    "denis.morozov@kigm23.ru": "denis2026",
    "polina.fadeeva@kigm23.ru": "polina2026",
    "kirill.volkov@kigm23.ru": "kirill2026",
    "vladislav.novikov@kigm23.ru": "vladislav2026",
    "daria.kuznetsova@kigm23.ru": "daria2026",
    "ilya.egorov@kigm23.ru": "ilya2026",
    "yana.stepanova@kigm23.ru": "yana2026",
    "maksim.lebedev@kigm23.ru": "maksim2026",
    "elena.gracheva@kigm23.ru": "elena2026",
    "roman.kozlov@kigm23.ru": "roman2026",
    "valeria.semenova@kigm23.ru": "valeria2026",
    "georgiy.melnikov@kigm23.ru": "georgiy2026",
    "curator.ivanova@kigm23.ru": "curator1",
    "curator.petrov@kigm23.ru": "curator2",
    "teacher.math@kigm23.ru": "teachmath2026",
    "teacher.network@kigm23.ru": "teachnet2026",
    "admin@kigm23.ru": "admin2026",
    # Legacy aliases kept for compatibility in existing local DB snapshots.
    "curator@kigm23.ru": "curator2026",
    "teacher.ru@kigm23.ru": "teachru2026",
}


def _ensure_college_email(email: str) -> str:
    normalized = email.strip().lower()
    if not normalized.endswith("@kigm23.ru"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email must belong to @kigm23.ru domain",
        )
    return normalized


@router.post("/google", response_model=UserOut)
def auth_google(payload: AuthGoogleRequest, db: Session = Depends(get_db)) -> User:
    normalized_email = _ensure_college_email(str(payload.email))
    user = db.query(User).filter(User.email == normalized_email).first()
    if user is None:
        group = db.query(StudyGroup).filter(StudyGroup.name == "КИГМ-201").first()
        if group is None:
            group = StudyGroup(name="КИГМ-201", course_number=2)
            db.add(group)
            db.commit()
            db.refresh(group)

        user = User(
            google_user_id=payload.google_user_id,
            full_name=payload.full_name,
            email=normalized_email,
            role=UserRole.student,
            group_id=group.id,
            course_number=group.course_number,
            avatar_url=payload.avatar_url,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        award_on_registration(db, user)
    else:
        user.google_user_id = payload.google_user_id or user.google_user_id
        user.full_name = payload.full_name
        user.avatar_url = payload.avatar_url
        db.commit()
        db.refresh(user)

    return user


@router.post("/login", response_model=AuthLoginOut)
def auth_login(payload: AuthLoginRequest, db: Session = Depends(get_db)) -> AuthLoginOut:
    normalized_email = _ensure_college_email(str(payload.email))
    expected_password = DEMO_PASSWORDS.get(normalized_email)
    if expected_password is None or payload.password != expected_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user = db.query(User).filter(User.email == normalized_email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return AuthLoginOut(
        access_token=f"demo-token-{user.id}",
        user=user,
    )


@router.get("/me", response_model=UserOut)
def auth_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
