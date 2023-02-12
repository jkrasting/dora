from .db import get_db
#from .user import User
#from .user import user_experiment_count
#from .project_util import *

from flask import g

#from dora import dora
from flask import request
from flask import render_template
from flask_login import current_user, login_required

def check_sql_table_exists(table,cursor):
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

def create_tokens_table(db,cursor):
    cmd = "CREATE TABLE `tokens` ( `token` varchar(60) CHARACTER "+\
          "SET latin1 COLLATE latin1_swedish_ci NOT NULL COMMENT 'URL-safe "+\
          "token from secrets.token_urlsafe()', `active` int(1) NOT NULL "+\
          "DEFAULT 1 COMMENT 'Active=1; Inactive=0', `email` varchar(100) "+\
          "CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL "+\
          "COMMENT 'Email address', `created` datetime DEFAULT NULL COMMENT "+\
          "'Token creation date', `expires` datetime NOT NULL DEFAULT "+\
          "'2099-12-31 23:59:59' COMMENT 'Token expiration date', "+\
          "`login_date` datetime DEFAULT NULL COMMENT 'Timestamp last use',"+\
          " `remote_addr` varchar(40) CHARACTER SET latin1 COLLATE "+\
          "latin1_swedish_ci DEFAULT NULL COMMENT 'Remote address of "+\
          "last use' ) ENGINE=InnoDB DEFAULT "+\
          "COLLATE=latin1_swedish_ci;"
    cursor.execute(cmd)

    cmd = "ALTER TABLE `tokens` ADD PRIMARY KEY (`email`);"
    cursor.execute(cmd)

    #cmd = "ALTER TABLE `tokens` MODIFY `number` int(11) NOT NULL "+\
    #      "AUTO_INCREMENT COMMENT 'Primary key index for API token';"
    #cursor.execute(cmd)

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


