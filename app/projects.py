import yaml

from app import app
from .db import get_db
from flask import request
from flask import render_template


def associate_with_project(idnum, project):
    sql = (
        f"INSERT INTO {project}_map (master_id) SELECT '{idnum}' "
        + f"WHERE NOT EXISTS (SELECT * FROM {project}_map "
        + f"WHERE master_id='{idnum}')"
    )
    db = get_db()
    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()
    cursor.close()


def create_project_map(project_name):
    db = get_db()
    cursor = db.cursor()
    sql = (
        f"CREATE TABLE IF NOT EXISTS `{project_name}_map` "
        + "(`experiment_id` int(11) NOT NULL AUTO_INCREMENT COMMENT "
        + "'Local project id', `master_id` int(11) NOT NULL "
        + "COMMENT 'Master project id', PRIMARY KEY (`experiment_id`), "
        + "UNIQUE KEY `experiment_id` (`experiment_id`), "
        + "UNIQUE KEY `master_id` (`master_id`)) "
        + "ENGINE=InnoDB DEFAULT CHARSET=latin1"
    )
    cursor.execute(sql)
    db.commit()
    cursor.close()


def list_projects():
    db = get_db()
    cursor = db.cursor()
    sql = "SELECT project_id,project_name from projects;"
    cursor.execute(sql)
    projs = cursor.fetchall()
    return [tuple(x.values()) for x in projs]


@app.route("/admin/project_update.html", methods=["POST"])
def project_update():
    args = dict(request.form)

    db = get_db()
    cursor = db.cursor()
    sql = 'select AUTO_INCREMENT from information_schema.TABLES where TABLE_SCHEMA = "mdt_tracker" and TABLE_NAME = "projects"'
    cursor.execute(sql)
    nextid = cursor.fetchone()["AUTO_INCREMENT"]

    if args["project_id"] == "new":
        args["project_id"] = nextid

    if int(args["project_id"]) > int(nextid):
        return render_template("page-500.html", msg="Project ID is too high.")
    keys = str(",").join([f"{x}" for x in list(args.keys())])
    keys = f"({keys})"
    vals = str(",").join([f"'{x}'" for x in list(args.values())])
    vals = f"({vals})"
    update = str(",").join([f"{k}='{v}'" for (k, v) in args.items()])
    sql = f"INSERT into projects {keys} VALUES {vals} ON DUPLICATE KEY UPDATE {update}"
    cursor.execute(sql)
    db.commit()
    cursor.close()

    create_project_map(args["project_name"])

    return render_template("success.html", msg="Updated project successfully.")


@app.route("/projects/<project_name>")
def display_project(project_name):
    db = get_db()
    cursor = db.cursor()
    sql = f"SELECT project_id,project_config,project_description from projects where project_name='{project_name}'"
    cursor.execute(sql)
    config_result = cursor.fetchone()
    if config_result["project_config"] != "":
        config = yaml.load(config_result["project_config"], Loader=yaml.SafeLoader)
    else:
        config = {"All Experiments": {"remap_sql": ""}}
    tables = []
    for k in list(config.keys()):
        table_data = {}
        table_data["title"] = k
        if "remap_sql" in list(config[k].keys()):
            sql_ = f"SELECT A.*,B.* from master A join {project_name}_map B on A.id = B.master_id order by B.experiment_id DESC"
            cursor.execute(sql_)
            table_data["experiments"] = cursor.fetchall()
            for x in table_data["experiments"]:
                x["id"] = f"{project_name}-{x['experiment_id']}"
        elif "mod_sql" in list(config[k].keys()):
            cursor.execute(config[k]["mod_sql"])
            table_data["experiments"] = cursor.fetchall()
        elif "sql" in list(config[k].keys()):
            cursor.execute(config[k]["sql"])
            table_data["experiments"] = cursor.fetchall()
        else:
            return render_template(
                "page-500.html", msg="Malformed SQL query in project config."
            )
        tables.append(table_data)
    cursor.close
    return render_template(
        "view-table.html",
        tables=tables,
        project_name=project_name,
        project_description=config_result["project_description"],
    )


@app.route("/admin/projects/<project_id>")
def project(
    project_id,
    params={"project_description": "", "project_name": "", "project_config": ""},
):
    params["project_id"] = project_id
    if project_id != "new":
        db = get_db()
        cursor = db.cursor()
        if not project_id[0].isdigit():
            sql = f"SELECT * from projects where project_name='{project_id}'"
        else:
            sql = f"select * from projects where project_id={project_id}"
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        params = result if isinstance(result, dict) else params
        project_id = result["project_id"]
    content = {}
    content["project_id"] = params["project_id"]
    content["project_name"] = params["project_name"]
    content["project_description"] = params["project_description"]
    content["project_config"] = params["project_config"]
    return render_template("project.html", **content)
