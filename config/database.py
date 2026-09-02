import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")

    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    app.config.setdefault('UPLOAD_FOLDER', os.path.join(app.root_path, 'uploads'))
    app.config.setdefault('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)  # 16 MB Limit
    
    db.init_app(app)