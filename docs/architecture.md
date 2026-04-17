# Architecture Overview

## Context

Kigm Tracker is split into two primary applications:

- Frontend: Next.js web UI for students and administrators.
- Backend: FastAPI REST API with PostgreSQL persistence.

## High-level modules

1. Authentication and user binding
- Google OAuth 2.0 login entry point.
- Mapping `google_user_id` to local user profile.

2. Classroom integration
- Service boundary for Google Classroom API.
- Sync operations for courses, coursework, and student submissions.

3. Profile module
- Base student data.
- Achievements, subject grades, event participation, and totals.

4. Events module
- CRUD for events (admin role).
- Participation and result tracking.

5. Leaderboards module
- Grades leaderboard.
- Activity leaderboard.
- Achievements leaderboard.
- Scope filters: group, course, college.

## Data strategy

- PostgreSQL is the source of truth.
- Assignment comments are local-only in MVP.
- Sync jobs store external data into local tables for fast reads and cache fallback.

## Resilience

- Sync layer designed for retries with exponential backoff.
- Last known data served from local DB when external API is unavailable.

## Security

- Role-based checks for admin-only endpoints.
- OAuth tokens are not persisted in this scaffold and should be stored securely in production.
