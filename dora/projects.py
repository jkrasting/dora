""" Module for project-related pages """

from dora.paramdiff import parameter_diff
import yaml
from flask import request
from flask import render_template
from flask_login import current_user, login_required
from dora import dora

from .db import get_db
from .project_util import (
    associate_with_project,
    create_project_map,
    list_projects,
)


@dora.route("/projects/<project_name>")
def display_project(project_name):
    """Displays a table or set of tables for a given project

    Parameters
    ----------
    project_name : str
        Name of the project to display

    Returns
    -------
    flask.render_template
        Renders a template from the template folder with the given context
    """

    error = ""

    # open a database connection and cursor
    db = get_db()
    cursor = db.cursor()

    # define "always visible" projects regardless of the user
    auth_proj = ["mdt", "cmip6", "postmdt"]

    # determine what projects the user is permitted to view
    if current_user.is_authenticated:
        auth_proj = auth_proj + current_user.perm_view
    sql = (
        "SELECT project_id,project_config,project_description "
        + f"from projects where project_name='{project_name}'"
    )
    cursor.execute(sql)
    config_result = cursor.fetchone()

    # check if project exists
    if project_name not in list_projects():
        return render_template(
            "page-500.html", msg=f"Project '{project_name}' does not exist."
        )

    # exit here if user is not authorized
    if project_name not in auth_proj:
        return render_template(
            "page-500.html", msg=f"You are not authorized to view {project_name}"
        )

    # construct the command to fetch the experiments based on the project's
    # yaml configuration. A table is generated for each entry in the yaml
    # configuration file.
    #
    #   * The "remap_sql" modifier:
    #         instructs the system remap master table ids to project ids
    #
    #   * The "sql" modifier:
    #         performs a specific sql query on the master table

    # get model configuration
    if config_result["project_config"] != "":
        config = yaml.load(config_result["project_config"], Loader=yaml.SafeLoader)
    else:
        config = {"All Experiments": {"remap_sql": ""}}

    # loop over tables
    tables = []
    for k in list(config.keys()):
        table_data = {}
        table_data["title"] = k

        # construct the sql query
        if "remap_sql" in list(config[k].keys()):
            _remap_sql = config[k]["remap_sql"]
            _remap_sql = f"where {_remap_sql}" if (len(_remap_sql) > 0) else ""
            sql = (
                f"SELECT A.*,B.* from master A join {project_name}_map "
                + f"B on A.id = B.master_id {_remap_sql} order by B.experiment_id DESC"
            )

        elif "sql" in list(config[k].keys()):
            sql = config[k]["sql"]

        else:
            return render_template(
                "page-500.html", msg="Malformed SQL query in project config."
            )

        # execute the database query
        cursor.execute(sql)
        table_data["experiments"] = cursor.fetchall()

        # append project name in front of ids if they are remapped
        if "remap_sql" in list(config[k].keys()):
            for x in table_data["experiments"]:
                x["id"] = f"{project_name}-{x['experiment_id']}"

        tables.append(table_data)

    # get list of parameters from URL
    parameter = request.args.getlist("parameter")

    # get parameters from database
    if len(parameter) > 0:
        masterlist = [
            [x["master_id"] for x in table["experiments"]] for table in tables
        ]
        masterlist = [value for sublist in masterlist for value in sublist]
        masterlist = sorted(list(set(masterlist)))
        masterlist = [str(x) for x in masterlist]
        sql = f"SELECT expID, param, val from parameters where param in {str(tuple(parameter)).replace(',)',')')} and expID in {tuple(masterlist)}"

        try:
            cursor.execute(sql)
            results = cursor.fetchall()
            params = {k: {k: "" for k in parameter} for k in masterlist}
            for result in results:
                params[result["expID"]][result["param"]] = result["val"]
        except Exception as e:
            print(sql)
            error = str(e)
            params = {}
            parameter = []
    else:
        params = {}

    # close the database cursor
    cursor.close()

    # render the web page
    return render_template(
        "view-table.html",
        tables=tables,
        project_name=project_name,
        project_description=config_result["project_description"],
        parameter=parameter,
        params=params,
        error=error,
    )


@dora.route("/admin/projects/<project_id>")
@login_required
def project(
    project_id,
    params={"project_description": "", "project_name": "", "project_config": ""},
):
    """Returns page with project parameters

    Parameters
    ----------
    project_id : int or str
        Project integer id or name string
    params : dict, optional
        Dictionary of project parameters, by default
        {"project_description": "", "project_name": "", "project_config": ""}

    Returns
    -------
    flask.render_template
        Renders a template from the template folder with the given context
    """

    error = ""

    # add project id from url to the params dict
    params["project_id"] = project_id

    # if a specific project is specified (something other than "new"),
    # fetch its existing parameters from the database
    if project_id != "new":

        # open a database connection and cursor
        db = get_db()
        cursor = db.cursor()

        # check to see if project exists
        proj_list = list_projects()
        if not project_id[0].isdigit():
            proj_is_known = project_id in [x[1] for x in proj_list]
        else:
            proj_is_known = project_id in [x[0] for x in proj_list]
        if not proj_is_known:
            return render_template(
                "page-500.html", msg=f"{project_id} is not a recognized project"
            )

        # construct the sql command
        if not project_id[0].isdigit():
            sql = f"SELECT * from projects where project_name='{project_id}'"
        else:
            sql = f"select * from projects where project_id={project_id}"

        # execute the database query
        cursor.execute(sql)
        result = cursor.fetchone()

        # close the cursor
        cursor.close()

        # update the params dictionary
        params = result if isinstance(result, dict) else params
        project_id = result["project_id"]

    # map the params dictionary into the content dictionary
    content = {}
    content["project_id"] = params["project_id"]
    content["project_name"] = params["project_name"]
    content["project_description"] = params["project_description"]
    content["project_config"] = params["project_config"]

    return render_template("project.html", **content)


@dora.route("/admin/projects")
@login_required
def project_list_view():
    projects = [project[1] for project in list_projects()]
    return render_template("project_list.html", projects=projects)


@dora.route("/admin/projects/membership/<project_name>")
@login_required
def project_membership(project_name):
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


@dora.route("/admin/projects/membership_update", methods=["POST"])
@login_required
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
    permission_add = project_name in current_user.perm_add
    permission_del = project_name in current_user.perm_del

    # determine if user had permission to make changes
    add_list = list(set(new_members) - set(current_members))
    remove_list = list(set(current_members) - set(new_members))

    if (len(add_list) > 0 and not permission_add) or (
        len(remove_list) > 0 and not permission_del
    ):
        cursor.close()
        result = render_template(
            "page-500.html",
            msg="You are not authorized to make this project modifcation. "
            + "Please check your permissions.",
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

        result = render_template(
            "success.html", msg="Updated project membership successfully."
        )

    return result


@dora.route("/admin/project_update.html", methods=["POST"])
@login_required
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
