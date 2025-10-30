from datetime import datetime, timezone
from backend.models import Badge, UserBadge, Streak


def award_badge_if_missing(db_session, user_id: int, badge_code: str, name: str, description: str = ""):
    """Ensure badge exists and award it to the user if not already awarded."""
    # ensure badge exists
    badge = db_session.query(Badge).filter_by(code=badge_code).first()
    if not badge:
        badge = Badge(code=badge_code, name=name, description=description)
        db_session.add(badge)
        db_session.flush()

    # check existing
    existing = db_session.query(UserBadge).filter_by(user_id=user_id, badge_id=badge.id).first()
    if existing:
        return False

    ub = UserBadge(user_id=user_id, badge_id=badge.id, earned_at=datetime.now(timezone.utc))
    db_session.add(ub)
    return True


def evaluate_badges_for_user(db_session, user):
    """Evaluate simple badge rules for a user and award badges where appropriate.

    Rules implemented (simple examples):
    - first_100_xp: award when user.xp_total >= 100
    - five_day_streak: award when user's streak.current_streak >= 5
    """
    awarded = []

    try:
        # Rule: first 100 XP
        xp_total = getattr(user, 'xp_total', 0) or 0
        if xp_total >= 100:
            if award_badge_if_missing(db_session, user.id, 'first_100_xp', 'First 100 XP', 'Awarded for reaching 100 XP'):
                awarded.append('first_100_xp')

        # Rule: 5-day streak
        streak = db_session.query(Streak).filter_by(user_id=user.id).first()
        if streak and (streak.current_streak or 0) >= 5:
            if award_badge_if_missing(db_session, user.id, '5_day_streak', '5 Day Streak', 'Awarded for 5-day checkin streak'):
                awarded.append('5_day_streak')

        # flush to persist any new UserBadge rows
        if awarded:
            db_session.flush()

    except Exception:
        # swallow errors to avoid breaking XP award flow; log in real app
        pass

    return awarded
