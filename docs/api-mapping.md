# API Mapping to Specification

## Auth

- `POST /auth/google`
- `GET /auth/me`

## Profile

- `GET /profile`
- `GET /profile/achievements`
- `GET /profile/grades`
- `GET /profile/events`

## Assignments

- `GET /assignments`
- `GET /assignments/{id}`
- `GET /assignments/{id}/submissions/me`
- `GET /assignments/{id}/comments`
- `POST /assignments/{id}/comments`

## Events

- `GET /events`
- `GET /events/{id}`
- `POST /events`
- `PUT /events/{id}`
- `DELETE /events/{id}`

## Event participation

- `POST /events/{id}/participation`
- `PUT /events/{id}/participation/{userId}`

## Achievements

- `GET /achievements`
- `GET /achievements/me`

## Leaderboards

- `GET /leaderboard/grades?scope=group|course|college`
- `GET /leaderboard/activity?scope=group|course|college`
- `GET /leaderboard/achievements?scope=group|course|college`

## Classroom sync

- `POST /sync/classroom`
- `POST /sync/classroom/course/{courseId}`
