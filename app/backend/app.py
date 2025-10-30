import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Configure app and DB
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///./dev.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
app.config['ALLOW_DEV_LOGIN'] = os.getenv('ALLOW_DEV_LOGIN', '1') in ('1', 'true', 'True')

# initialize DB without binding to app so tests can override `app.config` before init
db = SQLAlchemy()

# import models and blueprints (registered below to avoid circular imports)
from backend import models  # noqa: E402
from backend.routes.xp import xp_bp
from backend.routes.users import users_bp
from backend.routes.badges import badges_bp
from backend.routes.auth import auth_bp
from backend.routes.jobs import jobs_bp

app.register_blueprint(xp_bp)
app.register_blueprint(users_bp)
app.register_blueprint(badges_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(jobs_bp)

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/v1/ping')
def ping():
    return jsonify({'ok': True, 'message': 'pong'})

if __name__ == '__main__':
    # create all tables in dev mode
    # bind DB from app config then create tables
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
