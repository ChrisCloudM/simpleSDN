from SNMP import SNMP
import re


class Device_base_info:
    #查找设备的设备名，系统型号版本，IP地址
    def __init__(self, host):
        self.host = host
        self.snmp_session = SNMP(host)

    @property
    def sysName(self):
        #查找设备名
        response = self.snmp_session.get("1.3.6.1.2.1.1.5.0")
        if response:
            return str(response[0], encoding="utf-8")

    @property
    def sysDescr(self):
        #查找设备的系统信息和版本,model
        response = self.snmp_session.get("1.3.6.1.2.1.1.1.0")
        if response:
            return re.search("(?<=\s\()[^)]+?(?=\)\s\r)", str(response[0], encoding="utf-8")).group()

    @property
    def deviceIP(self):
        #设备IP
        return self.host

    def baseInfo(self):
        #返回所有base_info
        res = {
            "deviceIP": self.deviceIP,
            "sysName": self.sysName,
            "sysDescr": self.sysDescr
        }
        return res


if __name__ == "__main__":
    a = Device_base_info("192.168.140.101")
