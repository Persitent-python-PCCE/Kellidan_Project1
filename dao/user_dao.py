from config.database import db
from models.user import User

class UserDAO:
    def create_user(self, username, password, role):
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    def get_by_id(self, user_id):
        return db.session.get(User, user_id)

    def get_by_username(self, username):
        return User.query.filter_by(username=username).first()

    def get_all(self):
        return User.query.all()

    def delete(self, user):
        db.session.delete(user)
        db.session.commit()