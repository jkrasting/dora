from flask_login import UserMixin
from dora.db import get_db
from .project_util import *
import socket

# from .user import user_experiment_count
# from .project_util import *

# from flask import g


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
        hostname="",
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
        self.hostname = hostname

    @staticmethod
    def get(value, key="id"):
        db = get_db()
        cursor = db.cursor()
        sql = f"SELECT * FROM users WHERE {key}='{value}'"
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

        # hostname = socket.gethostbyaddr(user["remote_addr"])[0]
        hostname = ""

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
            hostname=hostname,
        )

        return user

    def update_permission(self, key, value):
        db = get_db()
        cursor = db.cursor()
        sql = f"UPDATE users SET {key}='{value}' WHERE id='{self.id}'"
        print(sql)
        cursor.execute(sql)
        db.commit()
        cursor.close()

    @staticmethod
    def create(id_, name, email, profile_pic, remote_addr, login_date):
        """Adds a new user to the database

        Parameters
        ----------
        id_ : str
            openidc user id
        name : str
            real name
        email : str, email-like
            email address
        profile_pic : str, url-like
            url of profile pic
        remote_addr : str
            ip address of login
        login_date : str
            login time
        """

        # open the database and insert user into the database
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (id, name, email, profile_pic, remote_addr, login_date) "
            + f"VALUES ('{id_}', '{name}', '{email}', '{profile_pic}', '{remote_addr}', '{login_date}')"
        )
        db.commit()

        # If this is the first user, make them admin by default
        cursor.execute("SELECT @@IDENTITY")
        result = cursor.fetchone()
        userid = result["@@IDENTITY"]
        if userid == 1:
            sql = f"UPDATE users set admin='1' where userid='{userid}'"
            cursor.execute(sql)
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

    @staticmethod
    def reset(id_, name, email, profile_pic, remote_addr, login_date):
        db = get_db()
        cursor = db.cursor()
        sql = (
            f"UPDATE users SET id='{id_}', name='{name}', profile_pic='{profile_pic}', "
            + f"remote_addr='{remote_addr}', login_date='{login_date}' WHERE email='{email}'"
        )
        cursor.execute(sql)
        db.commit()
        cursor.close()

    @property
    def token(self):
        return get_api_token(self.email)


def user_experiment_count(username):
    db = get_db()
    cursor = db.cursor()
    sql = f"select count(id) from master where lower(userName)='{username}' or lower(owner)='{username}'"
    cursor.execute(sql)
    result = cursor.fetchone()
    result = result["count(id)"] if result is not None else "N/A"
    return result


def check_sql_table_exists(table, cursor):
    sql = f"SELECT * FROM information_schema.tables WHERE table_name = '{table}'"
    cursor.execute(sql)
    table_info = cursor.fetchall()
    result = True if len(table_info) > 0 else False
    return result


#    cmd = "CREATE TABLE `tokens` ( `number` int(11) NOT NULL COMMENT "+ \
#          "'Primary key index for API token', `token` varchar(60) CHARACTER "+ \
#          "SET latin1 COLLATE latin1_swedish_ci NOT NULL COMMENT 'URL-safe "+ \
#          "token from secrets.token_urlsafe()', `active` int(1) NOT NULL "+ \
#          "DEFAULT 1 COMMENT 'Active=1; Inactive=0', `email` varchar(100) "+ \
#          "CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL "+ \
#          "COMMENT 'Email address', `created` datetime DEFAULT NULL COMMENT "+ \
#          "'Token creation date', `expires` datetime NOT NULL DEFAULT "+ \
#          "'2099-12-31 23:59:59' COMMENT 'Token expiration date', "+ \
#          "`login_date` datetime DEFAULT NULL COMMENT 'Timestamp last use',"+ \
#          " `remote_addr` varchar(40) CHARACTER SET latin1 COLLATE "+ \
#          "latin1_swedish_ci DEFAULT NULL COMMENT 'Remote address of "+ \
#          "last use' ) ENGINE=InnoDB DEFAULT "+ \
#          "COLLATE=latin1_swedish_ci;"


def create_tokens_table(db, cursor):
    cmd = (
        "CREATE TABLE `tokens` ( `token` varchar(60) CHARACTER "
        + "SET latin1 COLLATE latin1_swedish_ci NOT NULL COMMENT 'URL-safe "
        + "token from secrets.token_urlsafe()', `active` int(1) NOT NULL "
        + "DEFAULT 1 COMMENT 'Active=1; Inactive=0', `email` varchar(100) "
        + "CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL "
        + "COMMENT 'Email address', `created` datetime DEFAULT NULL COMMENT "
        + "'Token creation date', `expires` datetime NOT NULL DEFAULT "
        + "'2099-12-31 23:59:59' COMMENT 'Token expiration date', "
        + "`login_date` datetime DEFAULT NULL COMMENT 'Timestamp last use',"
        + " `remote_addr` varchar(40) CHARACTER SET latin1 COLLATE "
        + "latin1_swedish_ci DEFAULT NULL COMMENT 'Remote address of "
        + "last use' ) ENGINE=InnoDB DEFAULT "
        + "COLLATE=latin1_swedish_ci;"
    )
    cursor.execute(cmd)

    cmd = "ALTER TABLE `tokens` ADD PRIMARY KEY (`email`);"
    cursor.execute(cmd)

    # cmd = "ALTER TABLE `tokens` MODIFY `number` int(11) NOT NULL "+\
    #      "AUTO_INCREMENT COMMENT 'Primary key index for API token';"
    # cursor.execute(cmd)

    db.commit()


def get_api_token(email):
    db = get_db()
    cursor = db.cursor()
    sql = f"SELECT * FROM tokens WHERE email='{email}'"
    cursor.execute(sql)
    token = cursor.fetchone()
    cursor.close()
    result = None if token is None else token["token"]
    return result


class Token:
    def __init__(self, token):
        db = get_db()
        cursor = db.cursor()
        sql = f"SELECT * from tokens WHERE token='{token}';"
        cursor.execute(sql)
        attrs = cursor.fetchone()

        if attrs is not None:
            self.__dict__ = {**self.__dict__, **attrs}

        print(self.__dict__)

    @property
    def user(self):
        result = User(None, None, None, None, None, None).get(self.email, key="email")
        return result

    def __repr__(self):
        return str(self.token)
