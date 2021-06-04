#!/usr/bin/env python3

import os
import pymysql
import sys

try:
    from db import get_db, close_db
except:
    from .db import get_db, close_db


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
        "id",
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
        "owner",
    ]

    def __init__(self, input, db=None):
        self.__dict__ = {k: None for k in self.expected_keys}

        def fix_dir_paths(dict_items):
            for k in dict_items.keys():
                value = dict_items[k]
                if isinstance(value, str):
                    if ("path" in k.lower()) and (len(value) > 0):
                        dict_items[k] = value + "/" if value[-1] != "/" else value
            return dict_items

        def _fetch_from_master(master_id, db=None):
            db = get_db() if db is None else db
            cursor = db.cursor()
            sql = f"select * from master where id='{master_id}'"
            cursor.execute(sql)
            result = cursor.fetchone()
            cursor.close()
            return result

        if isinstance(input, dict):
            self.source = "sql"
            dict_items = {k: v for (k, v) in input.items() if k in self.expected_keys}
            self.__dict__ = {**self.__dict__, **dict_items}

        elif isinstance(input, int) or input.isnumeric():
            self.id = str(input)
            self.source = "sql"
            result = _fetch_from_master(self.id, db=db)
            result = fix_dir_paths(result)
            self.__dict__ = {**self.__dict__, **result}

        elif input[0:5] == "exper":
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

        elif input[0] == "/":
            path = f"{input}/" if input[-1] != "/" else input
            self.source = "path"
            self.pathPP = path
            self.pathAnalysis = path
            self.pathDB = path
            path = path.split("/")
            if len(path) > 4:
                self.expName = path[-4]

        elif len(input.split("-")) == 2:
            split_input = input.split("-")
            db = get_db() if db is None else db
            cursor = db.cursor()
            sql = f"SELECT master_id from {split_input[0]}_map where experiment_id='{split_input[1]}'"
            cursor.execute(sql)
            result = cursor.fetchone()
            master_id = result["master_id"]
            cursor.close()

            self.id = str(input)
            self.source = "sql"
            result = _fetch_from_master(master_id, db=db)
            result = fix_dir_paths(result)
            self.__dict__ = {**self.__dict__, **result}

        # else:
        #    raise ValueError(
        #        "You have supplied an invalid type for id.  Expecting either "
        #        + "an integer corresponding to an experiment on the MDT Tracker, "
        #        + "Curator tripleID, or a filesystem path."
        #    )

    def modify(self, **kwargs):
        if "id" in list(dict(**kwargs).keys()):
            raise ValueError("Experiment ID cannot be updated.")
        modifications = {
            k: v for (k, v) in dict(**kwargs).items() if k in self.expected_keys
        }
        self.__dict__ = {**self.__dict__, **modifications}

    def insert(self, db):
        if self.source == "path":
            raise ValueError("Experiments derived from paths cannot be added")

        attrs = self.__dict__
        attrs = {k: v for (k, v) in attrs.items() if v is not None}
        attrs = {k: v for (k, v) in attrs.items() if v != ""}

        if "owner" not in list(attrs.keys()):
            attrs["owner"] = attrs["userName"]
        if "id" in list(attrs.keys()):
            del attrs["id"]
        if "source" in list(attrs.keys()):
            del attrs["source"]

        keys, values = list(zip(*attrs.items()))
        keys = str(tuple([str(x) for x in keys])).replace("'", "")
        values = str(tuple([str(x) for x in values]))
        sql = f"insert into master {keys} values {values}"
        db = get_db() if db is None else db
        cursor = db.cursor()
        cursor.execute(sql)
        db.commit()
        cursor.execute("SELECT @@IDENTITY")
        result = cursor.fetchone()
        cursor.close()
        return result["@@IDENTITY"]

    def update(self, db):
        if self.source == "path":
            raise ValueError("Experiments derived from paths cannot be updated")

        attrs = self.__dict__
        idnum = attrs["id"]
        attrs = {k: v for (k, v) in attrs.items() if v is not None}
        attrs = {k: v for (k, v) in attrs.items() if v != ""}
        if "id" in list(attrs.keys()):
            del attrs["id"]
        if "source" in list(attrs.keys()):
            del attrs["source"]
        pairs = [f"{k}='{str(v)}'" for (k, v) in attrs.items()]
        pairs = str(", ").join(pairs)
        sql = f"update master set {pairs} where id='{idnum}'"
        db = get_db() if db is None else db
        cursor = db.cursor()
        cursor.execute(sql)
        db.commit()
        cursor.close()

    def remove_key(self, key):
        del self.__dict__[key]

    def list_keys(self):
        return list(self.__dict__.keys())

    def value(self, key):
        return self.__dict__[key]

    def to_dict(self):
        return self.__dict__

    def __str__(self):
        return str(self.__dict__)


if __name__ == "__main__":
    db = open_db()

    A = Experiment(sys.argv[1], db=db)
    print(A.source)
    print(A)

    db.close()
