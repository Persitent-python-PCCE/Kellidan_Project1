class UserService:
    def __init__(self, user_dao):
        self.user_dao = user_dao

    def register_user(self, username, password, role):
        if self.user_dao.get_by_username(username):
            raise ValueError("Username already exists")
        return self.user_dao.create_user(username, password, role)

    def authenticate_user(self, username, password):
        user = self.user_dao.get_by_username(username)
        if user and user.check_password(password):
            return user
        return None