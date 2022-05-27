import sys
import os
import re
import configparser

DIR = os.path.abspath(os.path.dirname(__file__)) + "/"

settingName = "setting.conf"


class Setting:
    @classmethod
    @property
    def context(self):
        with open(DIR + settingName) as setr:
            settingContext = setr.read()
        LINK_IP = re.findall("LINK_IP = (.+)", settingContext)[0]
        RID = re.findall("RID = (.+)", settingContext)[0]
        NVE = re.findall("NVE = (.+)", settingContext)[0]
        NETCONF_USER = re.findall("NETCONF_USER = (.+)", settingContext)[0]
        NETCONF_PWD = re.findall("NETCONF_PWD = (.+)", settingContext)[0]
        DBFILE = re.findall("DBFILE = (.+)", settingContext)[0]
        AS = re.findall("AS = (.+)", settingContext)[0]
        VNI_RANGE = re.findall("VNI_RANGE = (.+)", settingContext)[0].split("-")
        return {"LINK_IP": LINK_IP, "RID": RID, "NVE": NVE, "NETCONF_USER": NETCONF_USER, "NETCONF_PWD": NETCONF_PWD, "DBFILE": DBFILE, "AS": AS, "VNI_RANGE": VNI_RANGE}


class Setting:
    @classmethod
    @property
    def context(self):
        settings = {
            "LINK_IP":      None,
            "RID":          None,
            "NVE":          None,
            "NETCONF_USER": None,
            "NETCONF_PWD":  None,
            "DBFILE":       None,
            "AS":           None,
            "VNI_RANGE":    None  
        }
        with open(DIR + settingName) as setr:
            settingContext = setr.read()
        LINK_IP = re.findall("LINK_IP = (.+)", settingContext)[0]
        RID = re.findall("RID = (.+)", settingContext)[0]
        NVE = re.findall("NVE = (.+)", settingContext)[0]
        NETCONF_USER = re.findall("NETCONF_USER = (.+)", settingContext)[0]
        NETCONF_PWD = re.findall("NETCONF_PWD = (.+)", settingContext)[0]
        DBFILE = re.findall("DBFILE = (.+)", settingContext)[0]
        AS = re.findall("AS = (.+)", settingContext)[0]
        VNI_RANGE = re.findall("VNI_RANGE = (.+)", settingContext)[0].split("-")
        return {"LINK_IP": LINK_IP, "RID": RID, "NVE": NVE, "NETCONF_USER": NETCONF_USER, "NETCONF_PWD": NETCONF_PWD, "DBFILE": DBFILE, "AS": AS, "VNI_RANGE": VNI_RANGE}



    





if __name__ == "__main__":
    a = Setting.context
    print(a)