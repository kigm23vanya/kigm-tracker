from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.core import (
    Assignment,
    Event,
    EventParticipation,
    EventSubjectLink,
    GoogleCourse,
    ParticipationStatus,
    StudyGroup,
    Subject,
    Submission,
    SubmissionState,
    TeacherSubjectAccess,
    User,
    UserRole,
)
from app.services.achievements import award_by_code, award_on_registration, seed_achievements
from app.services.profile_meta import WORK_YEARS_BY_EMAIL


def _upsert_group(db: Session, name: str, course_number: int) -> StudyGroup:
    group = db.query(StudyGroup).filter(StudyGroup.name == name).first()
    if group is None:
        group = StudyGroup(name=name, course_number=course_number)
        db.add(group)
    else:
        group.course_number = course_number
    db.flush()
    return group


def _upsert_user(
    db: Session,
    *,
    google_user_id: str,
    full_name: str,
    email: str,
    role: UserRole,
    group_id: int | None,
    course_number: int,
    avatar_url: str | None = None,
    legacy_emails: list[str] | None = None,
) -> User:
    user = db.query(User).filter(User.google_user_id == google_user_id).first()
    lookup_emails = [email] + (legacy_emails or [])
    if user is None:
        user = db.query(User).filter(User.email.in_(lookup_emails)).first()

    if user is None:
        user = User(
            google_user_id=google_user_id,
            full_name=full_name,
            email=email,
            role=role,
            group_id=group_id,
            course_number=course_number,
            avatar_url=avatar_url,
        )
        db.add(user)
    else:
        user.google_user_id = google_user_id
        user.full_name = full_name
        user.email = email
        user.role = role
        user.group_id = group_id
        user.course_number = course_number
        user.avatar_url = avatar_url

    db.flush()
    return user


def _upsert_teacher_subject_access(db: Session, teacher: User, subject: Subject) -> TeacherSubjectAccess:
    access = (
        db.query(TeacherSubjectAccess)
        .filter(
            TeacherSubjectAccess.teacher_id == teacher.id,
            TeacherSubjectAccess.subject_id == subject.id,
        )
        .first()
    )
    if access is None:
        access = TeacherSubjectAccess(teacher_id=teacher.id, subject_id=subject.id)
        db.add(access)
    db.flush()
    return access


def _upsert_event_subject_link(db: Session, event: Event, subject: Subject | None) -> EventSubjectLink | None:
    link = db.query(EventSubjectLink).filter(EventSubjectLink.event_id == event.id).first()
    if subject is None:
        if link is not None:
            db.delete(link)
            db.flush()
        return None

    if link is None:
        link = EventSubjectLink(event_id=event.id, subject_id=subject.id)
        db.add(link)
    else:
        link.subject_id = subject.id
    db.flush()
    return link


def _upsert_subject(db: Session, name: str) -> Subject:
    subject = db.query(Subject).filter(Subject.name == name).first()
    if subject is None:
        subject = Subject(name=name)
        db.add(subject)
    db.flush()
    return subject


def _upsert_course(db: Session, google_course_id: str, title: str, subject_id: int | None) -> GoogleCourse:
    course = db.query(GoogleCourse).filter(GoogleCourse.google_course_id == google_course_id).first()
    if course is None:
        course = GoogleCourse(google_course_id=google_course_id, title=title, subject_id=subject_id)
        db.add(course)
    else:
        course.title = title
        course.subject_id = subject_id
    db.flush()
    return course


def _upsert_assignment(
    db: Session,
    *,
    google_coursework_id: str,
    course_id: int,
    title: str,
    description: str,
    due_date: datetime,
    max_points: float,
) -> Assignment:
    assignment = db.query(Assignment).filter(Assignment.google_coursework_id == google_coursework_id).first()
    if assignment is None:
        assignment = Assignment(
            google_coursework_id=google_coursework_id,
            course_id=course_id,
            title=title,
            description=description,
            due_date=due_date,
            max_points=max_points,
            state="PUBLISHED",
        )
        db.add(assignment)
    else:
        assignment.course_id = course_id
        assignment.title = title
        assignment.description = description
        assignment.due_date = due_date
        assignment.max_points = max_points
        assignment.state = "PUBLISHED"

    db.flush()
    return assignment


def _upsert_submission(
    db: Session,
    *,
    assignment: Assignment,
    user: User,
    submission_state: SubmissionState,
    draft_grade: float,
    assigned_grade: float,
) -> Submission:
    submission = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment.id, Submission.student_id == user.id)
        .first()
    )

    external_id = f"sub-{assignment.google_coursework_id}-{user.google_user_id or user.id}"[:64]
    if submission is None:
        submission = Submission(
            google_submission_id=external_id,
            assignment_id=assignment.id,
            student_id=user.id,
            submission_state=submission_state,
            draft_grade=draft_grade,
            assigned_grade=assigned_grade,
            last_synced_at=datetime.utcnow(),
        )
        db.add(submission)
    else:
        submission.google_submission_id = external_id
        submission.submission_state = submission_state
        submission.draft_grade = draft_grade
        submission.assigned_grade = assigned_grade
        submission.last_synced_at = datetime.utcnow()

    db.flush()
    return submission


def _upsert_event(
    db: Session,
    *,
    title: str,
    description: str,
    starts_at: datetime,
    location: str,
    organizer: str,
    activity_points: int,
) -> Event:
    event = db.query(Event).filter(Event.title == title).first()
    if event is None:
        event = Event(
            title=title,
            description=description,
            starts_at=starts_at,
            location=location,
            organizer=organizer,
            activity_points=activity_points,
        )
        db.add(event)
    else:
        event.description = description
        event.starts_at = starts_at
        event.location = location
        event.organizer = organizer
        event.activity_points = activity_points

    db.flush()
    return event


def _upsert_participation(
    db: Session,
    *,
    event: Event,
    user: User,
    participation_status: ParticipationStatus,
    result: str | None,
    points_awarded: int,
) -> EventParticipation:
    participation = (
        db.query(EventParticipation)
        .filter(EventParticipation.event_id == event.id, EventParticipation.user_id == user.id)
        .first()
    )

    if participation is None:
        participation = EventParticipation(
            event_id=event.id,
            user_id=user.id,
            participation_status=participation_status,
            result=result,
            points_awarded=points_awarded,
        )
        db.add(participation)
    else:
        participation.participation_status = participation_status
        participation.result = result
        participation.points_awarded = points_awarded

    db.flush()
    return participation


def _award_teacher_progress_achievements(db: Session, teacher: User) -> None:
    years = WORK_YEARS_BY_EMAIL.get(teacher.email, 0)
    for milestone in range(5, 51, 5):
        if years >= milestone:
            award_by_code(
                db,
                teacher,
                f"teacher_service_{milestone}",
                f"Выслуга лет достигла {milestone} лет",
            )

    organized_events_count = db.query(Event).filter(Event.organizer == teacher.full_name).count()
    if organized_events_count > 0:
        award_by_code(db, teacher, "teacher_first_event", "Организовано первое мероприятие")


def _award_student_default_achievements(db: Session, student: User) -> None:
    submissions = db.query(Submission).filter(Submission.student_id == student.id).all()
    grades = [int(round(item.assigned_grade)) for item in submissions if item.assigned_grade is not None]

    for value, code in [(2, "first_grade_2"), (3, "first_grade_3"), (4, "first_grade_4"), (5, "first_grade_5")]:
        if value in grades:
            award_by_code(db, student, code, f"Получена оценка {value}")

    if student.course_number >= 2:
        award_by_code(db, student, "course_upgrade", "Переход на новое мастерство")

    participation = db.query(EventParticipation).filter(EventParticipation.user_id == student.id).all()
    if participation:
        award_by_code(db, student, "event_participation", "Первое участие в мероприятии")

    if any(item.result and ("место" in item.result.lower() or "winner" in item.result.lower()) for item in participation):
        award_by_code(db, student, "event_prize", "Призовое место в мероприятии")


def seed_initial_data(db: Session) -> None:
    seed_achievements(db)
    now = datetime.utcnow()

    group_a = _upsert_group(db, "КИГМ-201", 2)
    group_b = _upsert_group(db, "КИГМ-202", 2)

    admin = _upsert_user(
        db,
        google_user_id="admin-google-id",
        full_name="Администратор",
        email="admin@kigm23.ru",
        role=UserRole.admin,
        group_id=None,
        course_number=2,
        legacy_emails=["admin@kigm.local"],
    )

    curator_ivanova = _upsert_user(
        db,
        google_user_id="curator-ivanova-google-id",
        full_name="Ирина Иванова",
        email="curator.ivanova@kigm23.ru",
        role=UserRole.curator,
        group_id=group_a.id,
        course_number=2,
        legacy_emails=["curator@kigm23.ru"],
    )

    curator_petrov = _upsert_user(
        db,
        google_user_id="curator-petrov-google-id",
        full_name="Павел Петров",
        email="curator.petrov@kigm23.ru",
        role=UserRole.curator,
        group_id=group_b.id,
        course_number=2,
    )

    teacher_math = _upsert_user(
        db,
        google_user_id="teacher-math-google-id",
        full_name="Антон Жуков",
        email="teacher.math@kigm23.ru",
        role=UserRole.teacher,
        group_id=None,
        course_number=2,
    )

    teacher_network = _upsert_user(
        db,
        google_user_id="teacher-network-google-id",
        full_name="Елена Соколова",
        email="teacher.network@kigm23.ru",
        role=UserRole.teacher,
        group_id=None,
        course_number=2,
        legacy_emails=["teacher.ru@kigm23.ru"],
    )

    group_a_specs = [
        ("student-google-id", "Степан Студент", "st.student@kigm23.ru"),
        ("student2-google-id", "Мария Петрова", "maria.petrova@kigm23.ru"),
        ("student3-google-id", "Алина Ким", "alina.kim@kigm23.ru"),
        ("student4-google-id", "Олег Иванов", "oleg.ivanov@kigm23.ru"),
        ("student5-google-id", "Никита Смирнов", "nikita.smirnov@kigm23.ru"),
        ("student6-google-id", "София Романова", "sofia.romanova@kigm23.ru"),
        ("student7-google-id", "Артем Белов", "artem.belov@kigm23.ru"),
        ("student8-google-id", "Екатерина Орлова", "ekaterina.orlova@kigm23.ru"),
        ("student9-google-id", "Денис Морозов", "denis.morozov@kigm23.ru"),
        ("student10-google-id", "Полина Фадеева", "polina.fadeeva@kigm23.ru"),
    ]

    group_b_specs = [
        ("student11-google-id", "Кирилл Волков", "kirill.volkov@kigm23.ru"),
        ("student12-google-id", "Владислав Новиков", "vladislav.novikov@kigm23.ru"),
        ("student13-google-id", "Дарья Кузнецова", "daria.kuznetsova@kigm23.ru"),
        ("student14-google-id", "Илья Егоров", "ilya.egorov@kigm23.ru"),
        ("student15-google-id", "Яна Степанова", "yana.stepanova@kigm23.ru"),
        ("student16-google-id", "Максим Лебедев", "maksim.lebedev@kigm23.ru"),
        ("student17-google-id", "Елена Грачева", "elena.gracheva@kigm23.ru"),
        ("student18-google-id", "Роман Козлов", "roman.kozlov@kigm23.ru"),
        ("student19-google-id", "Валерия Семенова", "valeria.semenova@kigm23.ru"),
        ("student20-google-id", "Георгий Мельников", "georgiy.melnikov@kigm23.ru"),
    ]

    students: list[User] = []
    for google_id, full_name, email in group_a_specs:
        students.append(
            _upsert_user(
                db,
                google_user_id=google_id,
                full_name=full_name,
                email=email,
                role=UserRole.student,
                group_id=group_a.id,
                course_number=2,
                legacy_emails=["student@kigm.local"] if email == "st.student@kigm23.ru" else None,
            )
        )

    for google_id, full_name, email in group_b_specs:
        students.append(
            _upsert_user(
                db,
                google_user_id=google_id,
                full_name=full_name,
                email=email,
                role=UserRole.student,
                group_id=group_b.id,
                course_number=2,
            )
        )

    db.commit()

    for user in [admin, curator_ivanova, curator_petrov, teacher_math, teacher_network]:
        award_on_registration(db, user)

    for student in students:
        award_on_registration(db, student)

    subject_names = [
        "Русский язык",
        "Алгоритмы и структура данных",
        "Высшая математика",
        "Базы данных",
        "Английский язык",
        "Операционные сети, среды архитектура аппаратных средства",
        "Компьютерные сети",
        "Разработка, поддержка и тестирование программных модулей",
    ]

    subjects: dict[str, Subject] = {}
    assignments: list[tuple[str, Assignment, Assignment]] = []

    for index, subject_name in enumerate(subject_names, start=1):
        subject = _upsert_subject(db, subject_name)
        subjects[subject_name] = subject

        course = _upsert_course(
            db,
            google_course_id=f"bootstrap-course-{index}",
            title=subject_name,
            subject_id=subject.id,
        )

        practice = _upsert_assignment(
            db,
            google_coursework_id=f"bootstrap-cw-{index}-practice",
            course_id=course.id,
            title=f"Практика: {subject_name}",
            description="Практическое задание по предмету",
            due_date=now + timedelta(days=index + 2),
            max_points=5,
        )

        exam = _upsert_assignment(
            db,
            google_coursework_id=f"bootstrap-cw-{index}-exam",
            course_id=course.id,
            title=f"Экзамен: {subject_name}",
            description="Итоговый экзамен по предмету",
            due_date=now + timedelta(days=index + 12),
            max_points=5,
        )

        assignments.append((subject_name, practice, exam))

    for subject_name in [
        "Алгоритмы и структура данных",
        "Высшая математика",
        "Базы данных",
        "Разработка, поддержка и тестирование программных модулей",
    ]:
        _upsert_teacher_subject_access(db, teacher_math, subjects[subject_name])

    for subject_name in [
        "Русский язык",
        "Английский язык",
        "Операционные сети, среды архитектура аппаратных средства",
        "Компьютерные сети",
    ]:
        _upsert_teacher_subject_access(db, teacher_network, subjects[subject_name])

    db.commit()

    regular_cycle = [5, 4, 3, 5, 4, 2, 5, 4, 3, 5]
    exam_cycle = [5, 5, 4, 5, 4, 3, 5, 4, 3, 4]

    for student_index, student in enumerate(students):
        for subject_index, (subject_name, practice, exam) in enumerate(assignments):
            if student.email == "st.student@kigm23.ru" and subject_name == "Русский язык":
                practice_grade = 4
                exam_grade = 4
            elif student.email == "st.student@kigm23.ru" and subject_name == "Высшая математика":
                practice_grade = 5
                exam_grade = 5
            else:
                practice_grade = regular_cycle[(student_index + subject_index) % len(regular_cycle)]
                exam_grade = exam_cycle[(student_index + subject_index * 2) % len(exam_cycle)]
                if subject_index % 3 == 0 and student_index % 7 == 0:
                    practice_grade = max(2, practice_grade - 2)
                    exam_grade = max(2, exam_grade - 1)

            _upsert_submission(
                db,
                assignment=practice,
                user=student,
                submission_state=SubmissionState.returned,
                draft_grade=practice_grade,
                assigned_grade=practice_grade,
            )
            _upsert_submission(
                db,
                assignment=exam,
                user=student,
                submission_state=SubmissionState.returned,
                draft_grade=exam_grade,
                assigned_grade=exam_grade,
            )

    hackathon = _upsert_event(
        db,
        title='Хакатон "СтудКод"',
        description="Командная разработка цифрового сервиса",
        starts_at=now + timedelta(days=2),
        location="IT-лаборатория",
        organizer=teacher_math.full_name,
        activity_points=40,
    )
    olympiad = _upsert_event(
        db,
        title="Олимпиада",
        description="Предметная олимпиада по математике и алгоритмам",
        starts_at=now + timedelta(days=5),
        location="Учебный корпус 2",
        organizer=teacher_math.full_name,
        activity_points=35,
    )
    subbotnik = _upsert_event(
        db,
        title="Субботник",
        description="Общеколледжный субботник для студентов",
        starts_at=now + timedelta(days=7),
        location="Территория колледжа",
        organizer=curator_ivanova.full_name,
        activity_points=15,
    )
    training_camp = _upsert_event(
        db,
        title="Учебные сборы",
        description="Учебно-практические сборы по сетевым дисциплинам",
        starts_at=now + timedelta(days=9),
        location="Тренировочный центр",
        organizer=teacher_network.full_name,
        activity_points=25,
    )

    _upsert_event_subject_link(db, hackathon, subjects["Алгоритмы и структура данных"])
    _upsert_event_subject_link(db, olympiad, subjects["Высшая математика"])
    _upsert_event_subject_link(db, subbotnik, None)
    _upsert_event_subject_link(db, training_camp, subjects["Компьютерные сети"])

    for index, student in enumerate(students):
        _upsert_participation(
            db,
            event=subbotnik,
            user=student,
            participation_status=ParticipationStatus.participated,
            result="Участник",
            points_awarded=12 + (index % 4),
        )

        if student.group_id == group_a.id:
            if student.email == "st.student@kigm23.ru":
                _upsert_participation(
                    db,
                    event=hackathon,
                    user=student,
                    participation_status=ParticipationStatus.participated,
                    result="Финалист",
                    points_awarded=40,
                )
            else:
                result = "Участник"
                points = 24 + (index % 6) * 3
                if index == 1:
                    result = "1 место"
                    points = 60
                elif index == 2:
                    result = "2 место"
                    points = 52
                elif index == 3:
                    result = "3 место"
                    points = 45

                _upsert_participation(
                    db,
                    event=hackathon,
                    user=student,
                    participation_status=ParticipationStatus.participated,
                    result=result,
                    points_awarded=points,
                )
        else:
            _upsert_participation(
                db,
                event=training_camp,
                user=student,
                participation_status=ParticipationStatus.participated,
                result="Участник",
                points_awarded=20 + (index % 7) * 2,
            )

        if index < 8:
            result = "Участник"
            points = 28 + index * 2
            if index == 0:
                result = "1 место"
                points = 62
            elif index == 1:
                result = "2 место"
                points = 55
            elif index == 2:
                result = "3 место"
                points = 49

            _upsert_participation(
                db,
                event=olympiad,
                user=student,
                participation_status=ParticipationStatus.participated,
                result=result,
                points_awarded=points,
            )

    db.commit()

    for student in students:
        _award_student_default_achievements(db, student)

    _award_teacher_progress_achievements(db, teacher_math)
    _award_teacher_progress_achievements(db, teacher_network)

    award_by_code(db, curator_ivanova, "course_upgrade", "Куратор ведет группу нового уровня")
    award_by_code(db, curator_petrov, "course_upgrade", "Куратор ведет группу нового уровня")

    db.commit()
