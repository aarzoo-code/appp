from datetime import datetime
from backend.app import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    display_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=True)
    password_hash = db.Column(db.String(300), nullable=True)
    github_id = db.Column(db.String(200), unique=True, nullable=True)
    xp_total = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'email': self.email,
            'xp_total': self.xp_total,
            'level': self.level,
            'created_at': self.created_at.isoformat(),
        }

class XPEvent(db.Model):
    __tablename__ = 'xp_events'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(50), nullable=True)
    source_id = db.Column(db.String(200), nullable=True)
    meta = db.Column(db.JSON, nullable=True)
    # optional idempotency key provided by clients to prevent duplicate awards
    idempotency_key = db.Column(db.String(200), nullable=True)
    # Note: SQLAlchemy will reflect __table_args__ when creating tables. Alembic migration
    # already provides the constraints for existing DBs; keeping __table_args__ here
    # ensures the ORM knows about uniqueness for new DBs created with db.create_all().
    __table_args__ = (
        # prevent accidental duplicate events for same user+source+source_id
        db.UniqueConstraint('user_id', 'source', 'source_id', name='uq_user_source_sourceid'),
        db.UniqueConstraint('user_id', 'idempotency_key', name='uq_user_idempotency_key'),
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Badge(db.Model):
    __tablename__ = 'badges'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    icon = db.Column(db.String(500), nullable=True)

class UserBadge(db.Model):
    __tablename__ = 'user_badges'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

class Streak(db.Model):
    __tablename__ = 'streaks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    current_streak = db.Column(db.Integer, default=0)
    last_checkin_date = db.Column(db.Date)


class JobRecord(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    language = db.Column(db.String(50), default='python')
    payload = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(40), default='queued')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    output = db.Column(db.Text, nullable=True)
