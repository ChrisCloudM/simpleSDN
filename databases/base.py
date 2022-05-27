from setting import Setting
import sqlite3
import os


DIR = os.path.dirname(os.path.abspath(__file__))

class DBBase:
    def __init__(self, fabric=None):
        #实例化带入库名和表名
        databaseFile = Setting.context["DBFILE"]
        self.session = sqlite3.connect(databaseFile)
        self.cursor = self.session.cursor()
        self.fabric = fabric
        self.cursor.execute("CREATE TABLE IF NOT EXISTS Fabric(NAME text primary key);")
        self.session.commit()


    def __enter__(self):
        return self


    def __exit__(self, type, value, traceback):
        self.session.commit()
        self.session.close()