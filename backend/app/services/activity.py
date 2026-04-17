from app.models.core import AchievementRarity, EventParticipation, Submission, SubmissionState

ACTIVITY_POINTS_CONFIG = {
    "assignment_completed": 5,
    "assignment_on_time": 3,
    "grade_five": 5,
    "event_participation": 10,
    "event_prize": 20,
    "achievement_awarded": 7,
}

RARITY_WEIGHTS = {
    AchievementRarity.common: 1,
    AchievementRarity.rare: 3,
    AchievementRarity.epic: 5,
    AchievementRarity.legendary: 8,
}


def calculate_submission_points(submission: Submission) -> int:
    points = 0
    if submission.submission_state in {SubmissionState.turned_in, SubmissionState.returned}:
        points += ACTIVITY_POINTS_CONFIG["assignment_completed"]
    if submission.assignment.due_date and submission.last_synced_at <= submission.assignment.due_date:
        points += ACTIVITY_POINTS_CONFIG["assignment_on_time"]
    if submission.assigned_grade is not None and submission.assigned_grade >= 5:
        points += ACTIVITY_POINTS_CONFIG["grade_five"]
    return points


def calculate_event_points(participation: EventParticipation) -> int:
    points = participation.points_awarded
    if participation.participation_status.value in {"registered", "participated"}:
        points += ACTIVITY_POINTS_CONFIG["event_participation"]
    if participation.result:
        normalized = participation.result.lower()
        if "1" in normalized or "приз" in normalized or "winner" in normalized:
            points += ACTIVITY_POINTS_CONFIG["event_prize"]
    return points
