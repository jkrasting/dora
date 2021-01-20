#!/usr/bin/env python3

import os
import pymysql
import sys
from db import get_db, close_db


def open_db():
    return pymysql.connect(
        host=os.environ["DB_HOSTNAME"],
        user=os.environ["DB_USERNAME"],
        password=os.environ["DB_PASSWORD"],
        db=os.environ["DB_DATABASE"],
        cursorclass=pymysql.cursors.DictCursor,
    )


class Experiment:
    expected_keys = [
        "expName",
        "displayName",
        "userName",
        "pathPP",
        "pathDB",
        "pathXML",
        "expLabels",
        "pathAnalysis",
        "urlCurator",
        "pathScript",
        "modelType",
        "expType",
        "expLength",
        "expMIP",
        "refresh",
        "pathLog",
        "status",
    ]

    def __init__(self, input, db=None):
        self.__dict__ = {k: None for k in self.expected_keys}

        if isinstance(input, dict):
            self.id = None
            self.source = "sql"
            dict_items = {k: v for (k, v) in input.items() if k in self.expected_keys}
            self.__dict__ = {**self.__dict__, **dict_items}

        elif isinstance(input, int):
            self.id = str(input)
            self.source = "sql"
            db = get_db() if db is None else db
            cursor = db.cursor()
            sql = f"select * from master where id='{self.id}'"
            cursor.execute(sql)
            result = cursor.fetchone()
            self.__dict__ = {**self.__dict__, **result}

        elif id[0:5] == "exper":
            import UseCurator

            # -- Curator tripleIDs begin with the 'exper' string
            self.source = "curator"
            self.expName, self.commName = UseCurator.getExperimentMap(id)
            curator_paths = UseCurator.getArchivePPFromCure(id)
            self.pathPP = os.path.join(curator_paths[1], "")
            self.expLabels = ""  # these are exclusive to dora
            self.pathAnalysis = curator_paths[2]
            self.urlCurator = id
            dictInfo = UseCurator.getInfoFromExperID(id)
            self.userName = dictInfo["ownerName"]
            self.displayName = self.expName
            self.pathDB = os.path.join(curator_paths[0], "db/")
            self.pathDB = self.pathDB.replace("/archive/", "/home/")
            self.source = "sqlite"

        elif id[0] == "/":
            id = fixDirPath(id)
            self.source = "sqlite"
            self.expName = id
            self.displayName = id
            self.userName = ""
            self.pathPP = id
            self.pathDB = id
            self.expLabels = ""
            self.pathAnalysis = id
            self.urlCurator = ""
            self.pathDB = self.pathDB.replace("/home/", "/gfdlhome/")

        else:
            raise ValueError(
                "You have supplied an invalid type for id.  Expecting either "
                + "an integer corresponding to an experiment on the MDT Tracker, "
                + "Curator tripleID, or a filesystem path."
            )

    def modify(self, **kwargs):
        if "id" in list(dict(**kwargs).keys()):
            raise ValueError("Experiment ID cannot be updated.")
        modifications = {
            k: v for (k, v) in dict(**kwargs).items() if k in self.expected_keys
        }
        self.__dict__ = {**self.__dict__, **modifications}

    def to_dict(self):
        return self.__dict__

    def __str__(self):
        return str(self.__dict__)


if __name__ == "__main__":
    db = open_db()

    A = Experiment(int(sys.argv[1]), db=db)
    print(A)

    db.close()
