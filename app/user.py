from flask_login import UserMixin
from app.db import get_db
from .project_util import *


class User(UserMixin):
    def __init__(
        self,
        id_,
        name,
        email,
        profile_pic,
        remote_addr,
        login_date,
        admin=False,
        perm_view=[],
        perm_add=[],
        perm_modify=[],
        perm_del=[],
        firstlast="",
    ):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.remote_addr = remote_addr
        self.login_date = login_date
        self.admin = admin
        self.perm_add = perm_add
        self.perm_del = perm_del
        self.perm_modify = perm_modify
        self.perm_view = perm_view
        self.firstlast = firstlast

    @staticmethod
    def get(user_id):
        db = get_db()
        cursor = db.cursor()
        sql = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute(sql)
        user = cursor.fetchone()
        cursor.close()

        if user is None:
            return None

        perm_view = (
            [lookup_project_from_id(x) for x in user["perm_view"].split(",")]
            if user["perm_view"] is not None
            else []
        )
        perm_add = (
            [lookup_project_from_id(x) for x in user["perm_add"].split(",")]
            if user["perm_add"] is not None
            else []
        )
        perm_modify = (
            [lookup_project_from_id(x) for x in user["perm_modify"].split(",")]
            if user["perm_modify"] is not None
            else []
        )
        perm_del = (
            [lookup_project_from_id(x) for x in user["perm_del"].split(",")]
            if user["perm_del"] is not None
            else []
        )

        firstlast = user["email"].split("@")[0].lower().split(".")
        firstlast = [firstlast] if not isinstance(firstlast, list) else firstlast
        firstlast = [x.capitalize() for x in firstlast]
        firstlast = str(".").join(firstlast)

        user = User(
            id_=user["id"],
            name=user["name"],
            email=user["email"],
            profile_pic=user["profile_pic"],
            remote_addr=user["remote_addr"],
            login_date=user["login_date"],
            admin=True if user["admin"] == 1 else False,
            perm_add=perm_add,
            perm_del=perm_del,
            perm_modify=perm_modify,
            perm_view=perm_view,
            firstlast=firstlast,
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


def user_experiment_count(username):
    db = get_db()
    cursor = db.cursor()
    sql = f"select count(id) from master where lower(userName)='{username}' or lower(owner)='{username}'"
    cursor.execute(sql)
    result = cursor.fetchone()
    result = result["count(id)"] if result is not None else "N/A"
    return result
