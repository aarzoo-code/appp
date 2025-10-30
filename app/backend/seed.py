"""Seed the dev SQLite DB with example users and badges."""
from backend.app import app, db
from backend.models import User, Badge, XPEvent

with app.app_context():
    # create tables
    db.create_all()

    # create users if not existing
    if not User.query.first():
        alice = User(display_name='Alice', email='alice@example.com', xp_total=250, level=2)
        bob = User(display_name='Bob', email='bob@example.com', xp_total=420, level=3)
        carol = User(display_name='Carol', email='carol@example.com', xp_total=50, level=1)
        db.session.add_all([alice, bob, carol])
        db.session.commit()
        print('Created sample users')
    else:
        print('Users already exist')

    # create some badges
    if not Badge.query.first():
        b1 = Badge(code='first_lab', name='First Lab', description='Completed first lab')
        b2 = Badge(code='python_beginner', name='Python Beginner', description='Completed Python module')
        db.session.add_all([b1, b2])
        db.session.commit()
        print('Created sample badges')
    else:
        print('Badges already exist')

    # create an XP event for Bob
    bob = User.query.filter_by(display_name='Bob').first()
    if bob and not XPEvent.query.filter_by(user_id=bob.id).first():
        e = XPEvent(user_id=bob.id, amount=100, source='seed', source_id='seed-1', meta={'note': 'seeded event'})
        db.session.add(e)
        bob.xp_total = (bob.xp_total or 0) + 100
        db.session.commit()
        print('Seeded XP event for Bob')
    else:
        print('XP events already exist or Bob missing')

    print('Seeding complete')
