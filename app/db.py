import pymysql
import os

from flask import current_app
from flask import g
from flask.cli import with_appcontext


def get_db():
    if "db" not in g:
        g.db = pymysql.connect(
            host=os.environ["DB_HOSTNAME"],
            user=os.environ["DB_USERNAME"],
            password=os.environ["DB_PASSWORD"],
            db=os.environ["DB_DATABASE"],
            cursorclass=pymysql.cursors.DictCursor,
        )

    return g.db


# def get_db():
#    if "db" not in g:
#        g.db = sqlite3.connect(
#            "sqlite.db", detect_types=sqlite3.PARSE_DECLTYPES
#        )
#        g.db.row_factory = sqlite3.Row
#
#    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


# def init_db():
#    db = get_db()
#
#    with current_app.open_resource("schema.sql") as f:
#        db.executescript(f.read().decode("utf8"))

# @click.command("init-db")
# @with_appcontext
# def init_db_command():
#    init_db()
#    click.echo("Initialized the database")


def init_app(app):
    app.teardown_appcontext(close_db)
    # app.click.add_command(init_db_command)
