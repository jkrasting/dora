"""logging.py : logging module"""


def create_error_log_table(db, cursor):
    cmd = (
        "CREATE TABLE `logs` (`errid` INT(11) NOT NULL "
        + "AUTO_INCREMENT COMMENT 'Error ID number', `timestamp` DATETIME "
        + "NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Timestamp of error', `ip` "
        + "VARCHAR(100) NULL DEFAULT NULL COMMENT 'IP address of client', "
        + "`hostname` VARCHAR(100) NULL DEFAULT NULL COMMENT "
        + "'Hostname of client', `username` VARCHAR(100) NULL DEFAULT "
        + "NULL COMMENT 'Username', `url` TEXT NULL DEFAULT NULL COMMENT "
        + "'Offending URL', `error` VARCHAR(500) NULL DEFAULT NULL COMMENT "
        + "'Error Message', `traceback` TEXT NULL DEFAULT NULL COMMENT "
        + "'Traceback', PRIMARY KEY(`errid`)) ENGINE = InnoDB;"
    )
    cursor.execute(cmd)

    db.commit()
