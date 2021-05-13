""" Module for project-related pages """

import yaml

from .project_util import *

from app import app
from flask import request
from flask import render_template

from flask_login import current_user


@app.route("/admin/project_update.html", methods=["POST"])
def project_update():
    """Updates SQL database with new project metadata

    Returns
    -------
    flask.render_template
        Renders a template from the template folder with the given context
    """
    # get URL variables
    args = dict(request.form)

    # open database connection (rely on flask tear-down to close)
    db = get_db()

    # obtain the next available project ID number
    cursor = db.cursor()
    sql = (
        "select AUTO_INCREMENT from information_schema.TABLES where "
        + 'TABLE_SCHEMA = "mdt_tracker" and TABLE_NAME = "projects"'
    )
    cursor.execute(sql)
    nextid = cursor.fetchone()["AUTO_INCREMENT"]

    # assign next available id if a new project is being entered
    if args["project_id"] == "new":
        args["project_id"] = nextid

    # prevent user from adding a new project number out of sequence
    if int(args["project_id"]) > int(nextid):
        return render_template("page-500.html", msg="Project ID is too high.")

    # loop over keys and values to construct a SQL call
    keys = str(",").join([f"{x}" for x in list(args.keys())])
    keys = f"({keys})"
    vals = str(",").join([f"'{x}'" for x in list(args.values())])
    vals = f"({vals})"
    update = str(",").join([f"{k}='{v}'" for (k, v) in args.items()])
    sql = f"INSERT into projects {keys} VALUES {vals} ON DUPLICATE KEY UPDATE {update}"

    # execute command, flush the database, and close the cursor
    cursor.execute(sql)
    db.commit()
    cursor.close()

    # create a project id map table in the database if it doesn't exist
    create_project_map(args["project_name"])

    return render_template("success.html", msg="Updated project successfully.")


@app.route("/projects/<project_name>")
def display_project(project_name):
    auth_proj = ["mdt", "cmip6", "blubber"]
    if current_user.is_authenticated:
        auth_proj = auth_proj + current_user.perm_view
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
            _remap_sql = config[k]["remap_sql"]
            _remap_sql = f"where {_remap_sql}" if (len(_remap_sql) > 0) else ""
            sql_ = f"SELECT A.*,B.* from master A join {project_name}_map B on A.id = B.master_id {_remap_sql} order by B.experiment_id DESC"
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
    if project_name in auth_proj:
        return render_template(
            "view-table.html",
            tables=tables,
            project_name=project_name,
            project_description=config_result["project_description"],
        )
    else:
        return render_template(
            "page-500.html", msg=f"You are not authorized to view {project_name}"
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


@app.route("/admin/projects")
def project_list_view():
    projects = [project[1] for project in list_projects()]
    return render_template("project_list.html", projects=projects)


@app.route("/admin/projects/membership/<project_name>")
def project_membership(project_name):
    projects = [project[1] for project in list_projects()]
    db = get_db()
    cursor = db.cursor()
    sql = "select id,userName,expName from master"
    cursor.execute(sql)
    experiments = cursor.fetchall()
    sql = f"select master_id from {project_name}_map"
    cursor.execute(sql)
    project_members = cursor.fetchall()
    project_members = [exper["master_id"] for exper in project_members]
    cursor.close()
    return render_template(
        "project_membership.html",
        experiments=experiments,
        project_members=project_members,
        project_name=project_name,
    )


@app.route("/admin/projects/membership_update", methods=["POST"])
def project_membership_update():
    # process form input
    args = dict(request.form)
    project_name = args["project_name"]

    # open database and obtain cursor
    db = get_db()
    cursor = db.cursor()

    # get current project membershoip
    sql = f"select master_id from {project_name}_map"
    cursor.execute(sql)
    current_members = cursor.fetchall()
    current_members = [str(exper["master_id"]) for exper in current_members]

    # list of ids that the project membership should now become
    new_members = request.form.getlist("id")

    print(current_members)
    print(new_members)

    # logical for permission error
    permission_add = True if project_name in current_user.perm_add else False
    permission_del = True if project_name in current_user.perm_del else False

    # determine if user had permission to make changes
    add_list = list(set(new_members) - set(current_members))
    remove_list = list(set(current_members) - set(new_members))

    if (len(add_list) > 0 and not permission_add) or (
        len(remove_list) > 0 and not permission_del
    ):
        cursor.close()
        return render_template(
            "page-500.html",
            msg=f"You are not authorized to make this project modifcation. Please check your permissions.",
        )
    else:
        if len(add_list) > 0:
            if project_name in current_user.perm_add:
                for exper in add_list:
                    associate_with_project(exper, project_name)

        if len(remove_list) > 0:
            if project_name in current_user.perm_del:
                remove_list = f"({str(',').join(remove_list)})"
                sql = f"DELETE from {project_name}_map WHERE master_id IN {remove_list}"
                cursor.execute(sql)
                db.commit()

        cursor.close()

        return render_template(
            "success.html", msg="Updated project membership successfully."
        )
