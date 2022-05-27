from other.exceptions import *
from databases import DBBase
from DeviceManage.IP_distribute import linkIP
from setting import Setting, DIR
import sqlite3
import netaddr
import os



class DeviceModel(DBBase):
    def queryDeviceList(self):
        #查询当前设备列表
        self.cursor.execute("select IP from DeviceInfo_%s;" %self.fabric)
        return [i[0] for i in self.cursor.fetchall()]
    

    def queryDeviceAndRole(self):
        #查询当前设备和角色列表
        self.cursor.execute("select IP, ROLE from DeviceInfo_%s;" %self.fabric)
        return self.cursor.fetchall()


    def queryRid(self, host=None):
        #查询当前设备的所有rid
        if host:
            self.cursor.execute("select RID from DeviceInfo_%s where IP = \"%s\";" %(self.fabric, host))
            return [i[0] for i in self.cursor.fetchall()]
        else:
            self.cursor.execute("select RID from DeviceInfo_%s;" %self.fabric)
            return [i[0] for i in self.cursor.fetchall()]


    def queryNve(self, host=None):
        #查询当前设备的所有nve
        if host:
            self.cursor.execute("select NVE from DeviceInfo_%s where IP = \"%s\";" %(self.fabric, host))
            return [i[0] for i in self.cursor.fetchall()]
        else:
            self.cursor.execute("select NVE from DeviceInfo_%s;" %self.fabric)
            return [i[0] for i in self.cursor.fetchall()]

    
    def queryName(self, host):
        #查询设备名
        self.cursor.execute("select NAME from DeviceInfo_%s WHERE IP = \"%s\";" %(self.fabric, host))
        return [i[0] for i in self.cursor.fetchall()]


    def setDeviceRole(self, host, role):
        #设置IP的角色
        if host not in self.queryDeviceList():
            #如果设备不在
            return False
        if role not in ["spine","leaf"]:
            #如果设定的角色不符合设定
            raise RoleNameError(role)
        self.cursor.execute("update DeviceInfo_%s set ROLE = \"%s\" where IP = \"%s\"" %(self.fabric, role, host))
        return True


    def createNewDevice(self, IP, deviceName, model):
        if IP in self.queryDeviceList():
            return False
        self.cursor.execute("INSERT INTO DeviceInfo_%s (IP, NAME, MODEL, RID, NVE, ROLE) VALUES (\"%s\", \"%s\", \"%s\", \"null\", \"null\", \"null\");" %(self.fabric, IP, deviceName, model))
        return True


    def deleteDevice(self, IP):
        #删除一台设备
        if IP not in self.queryDeviceList():
            return False
        self.cursor.execute("DELETE FROM DeviceInfo_%s WHERE IP=\"%s\"" %(self.fabric, IP))
        return True


    def createRID(self, host, rid):
        #设置设备的rid
        if host not in self.queryDeviceList() or rid in self.queryRid():
            #如果设备不在
            raise notDevice(host)
        self.cursor.execute("update DeviceInfo_%s set RID = \"%s\" where IP = \"%s\"" %(self.fabric, rid, host))
        return True


    def createNVE(self, host, nve):
        #设置设备的rid
        if host not in self.queryDeviceList() or nve in self.queryNve():
            #如果设备不在
            raise
        self.cursor.execute("update DeviceInfo_%s set NVE = \"%s\" where IP = \"%s\"" %(self.fabric, nve, host))
        return True


class DeviceLldp(DBBase):
    def queryItem(self):
        #查询当前设备连接表
        res = []
        self.cursor.execute("select ITEM1, ITEM2 from DeviceLldp_%s;" %self.fabric)
        for i in self.cursor.fetchall():
            res.append(i[0])
            res.append(i[1])
        return res


    def createItem(self, localPort, localIp, remotePort, remoteIp):
        #插入互联
        #虽然数据库内有分本地和远程，但是同一条链路，只会有一个表项
        itemName1 = localIp + "_" + localPort
        itemName2 = remoteIp + "_" + remotePort
        current_query = self.queryItem()
        if itemName1 in current_query or itemName2 in current_query:
            return False
        self.cursor.execute("INSERT INTO DeviceLldp_%s (ITEM1, ITEM2, LOCAL_PORT, LOCAL_IP, REMOTE_PORT, REMOTE_IP) VALUES (\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\");" %(self.fabric, itemName1, itemName2, localPort, localIp, remotePort, remoteIp))
        return True

    
    def linkIPDisable(self):
        #查询当前链路未配置ip的链路
        self.cursor.execute("select ITEM1, LOCAL_PORT, LOCAL_IP, REMOTE_PORT, REMOTE_IP from DeviceLldp_%s WHERE IP_ENABLE = \"null\";" %self.fabric)
        return self.cursor.fetchall()


    def IP_ENABLE_SET(self, ITEM1):
        #将IP_ENABLE改为true
        self.cursor.execute("update DeviceLldp_%s set IP_ENABLE = \"True\" where ITEM1 = \"%s\"" %(self.fabric, ITEM1))
        

class IPDistribute(DBBase):
    def queryDeviceList(self):
        #查询当前设备列表
        self.cursor.execute("select DEVICE from IP_DISTRIBUTE_%s;" %self.fabric)
        return set([i[0] for i in self.cursor.fetchall()])


    def queryDevicePorts(self):
        #查询当前设备列表
        self.cursor.execute("select DEVICE, PORT from IP_DISTRIBUTE_%s;" %self.fabric)
        response = self.cursor.fetchall()
        res = {}
        for i in response:
            if i[0] not in res:
                res[i[0]] = [i[1]]
            else:
                res[i[0]].append(i[1])
        return res
        

    def querySegment(self):
        #查询当前设备互联IP
        self.cursor.execute("select SEGMENT from IP_DISTRIBUTE_%s;" %self.fabric)
        return [i[0] for i in self.cursor.fetchall()]

    
    def recordSegment(self, args):
        #IP分配结果写入到数据库内
        current = self.querySegment()
        for i in args:
            if i["segment"] not in current:
                self.cursor.execute("INSERT INTO IP_DISTRIBUTE_%s (SEGMENT, DEVICE, IP, PORT) VALUES (\"%s\", \"%s\", \"%s\", \"%s\");" %(self.fabric, i["segment"], i["device"], i["ip"], i["port"]))
            else:
                raise
        return True


class Fabric(DBBase):
    def __init__(self, fabric=None):
        #实例化带入库名和表名
        databaseFile = Setting.context["DBFILE"]
        self.session = sqlite3.connect(databaseFile)
        self.cursor = self.session.cursor()
        self.fabric = fabric
        if fabric != None:
            self.cursor.execute("CREATE TABLE IF NOT EXISTS DeviceInfo_%s (IP text primary key,NAME TEXT,ROLE TEXT, RID TEXT, NVE TEXT, MODEL TEXT);" %fabric)
            self.cursor.execute("CREATE TABLE IF NOT EXISTS IP_DISTRIBUTE_%s (ID integer PRIMARY KEY autoincrement,SEGMENT TEXT,DEVICE TEXT, IP TEXT, PORT TEXT);" %fabric)
            self.cursor.execute("CREATE TABLE IF NOT EXISTS DeviceLldp_%s (ITEM1 text,ITEM2 text,LOCAL_PORT TEXT,LOCAL_IP TEXT, REMOTE_PORT TEXT, REMOTE_IP TEXT, IP_ENABLE TEXT DEFAULT \"null\");" %fabric)
            self.cursor.execute("CREATE TABLE IF NOT EXISTS VPC_%s(VNI TEXT, NAME TEXT,ERD TEXT, ERT TEXT, IRT TEXT, IP TEXT, GATEWAY TEXT);" %self.fabric)
            self.session.commit()


    def createTable(self):
        #创建新的Fabric，调用时需要自己做异常处理（比如占用等情况）
        self.cursor.execute("insert into Fabric (NAME) values (\"%s\");" %self.fabric)

    
    def queryFabric(self):
        res = self.cursor.execute("SELECT * FROM Fabric;")
        return [i[0] for i in self.cursor.fetchall()]


class VPCModel(DBBase):
    def createVPCTable(self):
        #创建VPC表
        self.cursor.execute("CREATE TABLE IF NOT EXISTS VPC_%s(VNI TEXT, NAME TEXT,ERD TEXT primary key, ERT TEXT, IRT TEXT, IP TEXT, GATEWAY TEXT);" %self.fabric)
        self.session.commit()


    def createVPC(self, vni, vpc_name, rd, ert, irt):
        #添加VPC表项
        self.cursor.execute("INSERT INTO VPC_%s (VNI, NAME, ERD, IRT, ERT) VALUES (\"%s\", \"%s\", \"%s\", \"%s\", \"%s\");" %(self.fabric, vni, vpc_name, rd, irt, ert))
        self.session.commit()


    def vniOccupy(self):
        #查看当前在用的VNI
        res = self.cursor.execute("SELECT VNI FROM VPC_%s;" %self.fabric)
        return [i[0] for i in self.cursor.fetchall()]


    def VPCNameOccupy(self):
        #查看当前在用的VNI
        res = self.cursor.execute("SELECT NAME FROM VPC_%s;" %self.fabric)
        return [i[0] for i in self.cursor.fetchall()]

    
    def deleteVPC(self, vpc_name):
        #删除VPC表项
        self.cursor.execute("DELETE FROM VPC_%s WHERE NAME = \"%s\";" %(self.fabric, vpc_name))
        self.session.commit()

    def getVNI(self, vpc_name):
        self.cursor.execute("select distinct VNI from VPC_%s where NAME=\"%s\";" %(self.fabric, vpc_name))
        return [i[0] for i in self.cursor.fetchall()][0]



if __name__ == "__main__":
    with VPCModel("hcie") as dbobj:
        print(dbobj.getVNI("HCIE"))

