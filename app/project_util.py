from .db import get_db


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
    cursor.close()
    return [tuple(x.values()) for x in projs]


def lookup_project_from_id(idnum):
    db = get_db()
    cursor = db.cursor()
    sql = f"SELECT project_name from projects where project_id='{idnum}'"
    cursor.execute(sql)
    result = cursor.fetchone()
    cursor.close()
    result = result["project_name"] if result is not None else result
    return result


def lookup_project_from_name(proj):
    db = get_db()
    cursor = db.cursor()
    sql = f"SELECT project_id from projects where project_name='{proj}'"
    cursor.execute(sql)
    result = cursor.fetchone()
    cursor.close()
    result = result["project_id"] if result is not None else result
    return result
