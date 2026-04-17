from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, has_teacher_subject_access
from app.core.database import get_db
from app.models.core import Assignment, AssignmentComment, Submission, SubmissionState, User, UserRole
from app.schemas.api import AssignmentCardOut, AssignmentCommentCreate, AssignmentCommentOut, SubmissionGradeUpdate, SubmissionOut
from app.services.achievements import award_on_submission_grade

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("", response_model=list[AssignmentCardOut])
def list_assignments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[AssignmentCardOut]:
    assignments = db.query(Assignment).join(Assignment.course).order_by(Assignment.due_date.desc()).all()
    cards: list[AssignmentCardOut] = []

    for assignment in assignments:
        submission = (
            db.query(Submission)
            .filter(Submission.assignment_id == assignment.id, Submission.student_id == current_user.id)
            .first()
        )

        latest_comment = None
        if submission:
            latest_comment = (
                db.query(AssignmentComment)
                .filter(AssignmentComment.submission_id == submission.id)
                .order_by(AssignmentComment.created_at.desc())
                .first()
            )

        cards.append(
            AssignmentCardOut(
                id=assignment.id,
                course_title=assignment.course.title,
                assignment_title=assignment.title,
                assignment_description=assignment.description,
                due_date=assignment.due_date,
                max_points=assignment.max_points,
                submission_state=submission.submission_state if submission else None,
                draft_grade=submission.draft_grade if submission else None,
                assigned_grade=submission.assigned_grade if submission else None,
                comment=latest_comment.comment_text if latest_comment else None,
            )
        )

    return cards


@router.get("/{assignment_id}", response_model=AssignmentCardOut)
def get_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssignmentCardOut:
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    submission = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment.id, Submission.student_id == current_user.id)
        .first()
    )

    return AssignmentCardOut(
        id=assignment.id,
        course_title=assignment.course.title,
        assignment_title=assignment.title,
        assignment_description=assignment.description,
        due_date=assignment.due_date,
        max_points=assignment.max_points,
        submission_state=submission.submission_state if submission else None,
        draft_grade=submission.draft_grade if submission else None,
        assigned_grade=submission.assigned_grade if submission else None,
        comment=None,
    )


@router.get("/{assignment_id}/submissions/me", response_model=SubmissionOut)
def get_my_submission(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Submission:
    submission = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment_id, Submission.student_id == current_user.id)
        .first()
    )
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    return submission


@router.get("/{assignment_id}/submissions", response_model=list[SubmissionOut])
def list_assignment_submissions(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Submission]:
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    query = db.query(Submission).filter(Submission.assignment_id == assignment.id)

    if current_user.role == UserRole.admin:
        pass
    elif current_user.role == UserRole.curator:
        if current_user.group_id is None:
            return []
        query = query.join(Submission.student).filter(User.group_id == current_user.group_id)
    elif current_user.role == UserRole.teacher:
        if not has_teacher_subject_access(db, current_user, assignment.course.subject_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher has no access to this subject")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student role has read-only access")

    return query.order_by(Submission.id.asc()).all()


@router.put("/{assignment_id}/submissions/{student_id}/grade", response_model=SubmissionOut)
def update_submission_grade(
    assignment_id: int,
    student_id: int,
    payload: SubmissionGradeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Submission:
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    student = db.get(User, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    if student.role != UserRole.student:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target user is not a student")

    if current_user.role == UserRole.admin:
        pass
    elif current_user.role == UserRole.teacher:
        if not has_teacher_subject_access(db, current_user, assignment.course.subject_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher has no access to this subject",
            )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin or teacher can edit grades")

    if payload.assigned_grade is None and payload.draft_grade is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one grade value must be provided")

    submission = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment.id, Submission.student_id == student.id)
        .first()
    )
    if submission is None:
        submission = Submission(
            google_submission_id=f"manual-sub-{assignment.id}-{student.id}",
            assignment_id=assignment.id,
            student_id=student.id,
            submission_state=SubmissionState.returned,
            draft_grade=payload.draft_grade,
            assigned_grade=payload.assigned_grade,
            last_synced_at=datetime.utcnow(),
        )
        db.add(submission)
    else:
        if payload.draft_grade is not None:
            submission.draft_grade = payload.draft_grade
        if payload.assigned_grade is not None:
            submission.assigned_grade = payload.assigned_grade
            submission.submission_state = SubmissionState.returned
        submission.last_synced_at = datetime.utcnow()

    db.commit()
    db.refresh(submission)

    award_on_submission_grade(db, student, submission)
    return submission


@router.get("/{assignment_id}/comments", response_model=list[AssignmentCommentOut])
def get_assignment_comments(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AssignmentComment]:
    submission = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment_id, Submission.student_id == current_user.id)
        .first()
    )
    if submission is None:
        return []
    return (
        db.query(AssignmentComment)
        .filter(AssignmentComment.submission_id == submission.id)
        .order_by(AssignmentComment.created_at.desc())
        .all()
    )


@router.post("/{assignment_id}/comments", response_model=AssignmentCommentOut)
def add_assignment_comment(
    assignment_id: int,
    payload: AssignmentCommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssignmentComment:
    if current_user.role == UserRole.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student role has read-only access")

    submission = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment_id, Submission.student_id == current_user.id)
        .first()
    )
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    comment = AssignmentComment(
        submission_id=submission.id,
        author_id=current_user.id,
        comment_text=payload.comment_text,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
