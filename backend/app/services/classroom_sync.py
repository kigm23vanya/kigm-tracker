from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.core import Assignment, GoogleCourse, Submission, SubmissionState, Subject, User
from app.schemas.api import SyncResultOut


class ClassroomSyncService:
    """
    MVP mock sync layer.
    Replace internals with real Google Classroom API integration after OAuth setup.
    """

    def sync_all_for_user(self, db: Session, user: User) -> SyncResultOut:
        if not db.query(Subject).first():
            db.add(Subject(name="Информатика"))
            db.commit()

        subject = db.query(Subject).first()
        course = db.query(GoogleCourse).filter(GoogleCourse.google_course_id == "mock-course-1").first()
        if not course:
            course = GoogleCourse(google_course_id="mock-course-1", title="Программирование", subject_id=subject.id)
            db.add(course)
            db.commit()
            db.refresh(course)

        assignment = db.query(Assignment).filter(Assignment.google_coursework_id == "mock-cw-1").first()
        if not assignment:
            assignment = Assignment(
                google_coursework_id="mock-cw-1",
                course_id=course.id,
                title="Практическая работа 1",
                description="Базовое задание для MVP синхронизации",
                due_date=datetime.utcnow() + timedelta(days=5),
                max_points=5,
                state="PUBLISHED",
            )
            db.add(assignment)
            db.commit()
            db.refresh(assignment)

        submission = (
            db.query(Submission)
            .filter(Submission.assignment_id == assignment.id, Submission.student_id == user.id)
            .first()
        )
        if not submission:
            submission = Submission(
                google_submission_id=f"mock-sub-{user.id}-{assignment.id}",
                assignment_id=assignment.id,
                student_id=user.id,
                submission_state=SubmissionState.turned_in,
                draft_grade=4,
                assigned_grade=4,
                last_synced_at=datetime.utcnow(),
            )
            db.add(submission)
            db.commit()

        return SyncResultOut(synced_courses=1, synced_assignments=1, synced_submissions=1)

    def sync_course_for_user(self, db: Session, user: User, course_id: str) -> SyncResultOut:
        # For MVP we reuse full sync and ignore the concrete course id.
        return self.sync_all_for_user(db, user)
