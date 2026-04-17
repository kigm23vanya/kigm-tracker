# Recommended implementation plan

## Phase 1

- Finalize DB schema and migrations.
- Configure Google Cloud project and OAuth consent screen.
- Implement OAuth callback and token handling.
- Implement Classroom sync: courses, coursework, submissions.

## Phase 2

- Build profile endpoint aggregation.
- Add events module and participation flow.
- Add achievement awarding engine with triggers.

## Phase 3

- Add leaderboard materialized queries and caching.
- Implement scope filtering rules and ranking tie policy.
- Externalize activity points config for admin management.

## Phase 4

- Add assignment comments moderation.
- Add admin console.
- Improve sync with retries and optional push notifications.
