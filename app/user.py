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
        cursor = db.cursor()
        sql = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute(sql)
        user = cursor.fetchone()
        cursor.close()

        print("User: ", user)

        if user is None:
            return None

        user = User(
            id_=user["id"],
            name=user["name"],
            email=user["email"],
            profile_pic=user["profile_pic"],
            remote_addr=user["remote_addr"],
            login_date=user["login_date"],
        )

        return user

    @staticmethod
    def create(id_, name, email, profile_pic, remote_addr, login_date):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (id, name, email, profile_pic, remote_addr, login_date) "
            + f"VALUES ('{id_}', '{name}', '{email}', '{profile_pic}', '{remote_addr}', '{login_date}')"
        )
        db.commit()
        cursor.close()

    @staticmethod
    def update(id_, name, email, profile_pic, remote_addr, login_date):
        db = get_db()
        cursor = db.cursor()
        sql = (
            f"UPDATE users SET name='{name}', email='{email}', profile_pic='{profile_pic}', "
            + f"remote_addr='{remote_addr}', login_date='{login_date}' WHERE id='{id_}'"
        )
        cursor.execute(sql)
        db.commit()
        cursor.close()
