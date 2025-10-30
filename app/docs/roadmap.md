# Gamification Roadmap (MVP → v1)

This document summarizes a prioritized plan to add gamification and engagement features to the app.

## Sprint 0 — Goals
- Provide a minimum viable XP system for completed labs.
- Show level progress and a level-up modal with animation.
- Persist XP and streaks in a backend (dev: SQLite; prod: Postgres).
- Provide a basic leaderboard and badge gallery.

## Sprint 1 (1–2 weeks) — XP core & frontend
- Backend: Flask API, models (User, XPEvent), endpoints:
  - POST `/api/v1/xp/award`
  - GET `/api/v1/users/:id/stats`
  - GET `/api/v1/leaderboard`
- Frontend: `LevelProgress`, `LevelUpModal` (animated), integrate lab completion to call award endpoint.
- Persistence: dev DB (SQLite) + env-configured production DB URL.

Acceptance Criteria:
- Awarding XP updates user XP and level on the server.
- Frontend shows animated level-up modal when level increases.

## Sprint 2 (1–2 weeks) — Badges & Leaderboard
- Badge model + awarding rules.
- `BadgeGrid` UI and `/achievements` page.
- Leaderboard page (paginated) and SSE endpoint for live updates.

Acceptance Criteria:
- Badges can be listed and earned, leaderboard shows top users.

## Sprint 3 (1–2 weeks) — Streaks, reminders & challenges
- Daily streak system + backend job to compute streaks.
- In-app reminders and optional email/web notifications.
- Challenge enrollment and streak rewards (e.g., 5-day Python Champ).

## Sprint 4 — Community & Mentorship
- Decide between embedding Discourse or lightweight built-in forum.
- Mentorship connect flow (requests, accept/decline, review comments).

## Operational & infra notes
- Local dev: SQLite. Production: Postgres with Alembic migrations.
- Real-time: start with SSE, move to WebSocket when scaling.
- Runner architecture (notebook execution) described separately — JupyterHub / containerized kernels.

---

Next steps: choose where to start (backend scaffold, frontend components, or product doc expansion).