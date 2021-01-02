from flask_login import UserMixin

from app.db import get_db

class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic, remote_addr, login_date):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.remote_addr = remote_addr
        self.login_date = login_date

    @staticmethod
    def get(user_id):
        db = get_db()
        user = db.execute(
            "SELECT * FROM user WHERE id = ?", (user_id,)
        ).fetchone()

        if not user:
            return None

        user = User(
            id_=user[0], name=user[1], email=user[2], profile_pic=user[3], remote_addr=user[4], login_date=user[5]
        )

        return user

    @staticmethod
    def create(id_, name, email, profile_pic, remote_addr, login_date):
        db = get_db()
        db.execute(
            "INSERT INTO user (id, name, email, profile_pic, remote_addr, login_date)"
            "VALUES (?, ?, ?, ?, ?, ?)",
            (id_, name, email, profile_pic, remote_addr, login_date)
        )
        db.commit()

    @staticmethod
    def update(id_, name, email, profile_pic, remote_addr, login_date):
        db = get_db()
        db.execute(
            "UPDATE user SET (name, email, profile_pic, remote_addr, login_date)"
            "= (?, ?, ?, ?, ?) where id=?",
            (name, email, profile_pic, remote_addr, login_date, id_)
        )
        db.commit()