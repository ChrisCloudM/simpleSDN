#这个文件是设备管理最终提供出来的端口

from DeviceManage.device_info import Device_base_info
from DeviceManage.DB_Operation import DeviceModel, IPDistribute, IPDistribute, DeviceLldp, Fabric, VPCModel
from DeviceManage.IP_distribute import *
from DeviceManage.lldp import LldpInfo
import netaddr
from other.exceptions import *
from north.operation import *
from setting import Setting
import threading
from other.multi_threading import Multi_threading
from netmiko import ConnectHandler
import sqlite3
from other.exceptions import *


def checkFabric(name):
    with Fabric() as dbobj:
        fabricList = dbobj.queryFabric()
    if name not in fabricList:
        raise fabricNotExist(name)
    else:
        return True


class Device:
    #设备除lldp和ip配置之外的初始化操作
    def __init__(self, fabric):
        self.fabric = fabric
        checkFabric(fabric)


    def collect(self, host):
        #添加设备
        base_info_instance = Device_base_info(host)
        base_info = base_info_instance.baseInfo()
        #base_info = (deviceIP, sysName, sysDescr)
        with DeviceModel(self.fabric) as dbobj:
            if dbobj.createNewDevice(base_info["deviceIP"], base_info["sysName"], base_info["sysDescr"]):
                #添加新设备
                return base_info
                #返回结果
            else:
                raise IPOccupy(host)


    def deleteDevice(self, host):
        #删除设备
        #删除OSPF和BGP
        with DeviceModel(self.fabric) as dbobj:
            dbobj.deleteDevice(host)
            return True
    

    def setDeviceRole(self, host, role):
        #设置设备角色
        with DeviceModel(self.fabric) as dbobj:
            dbobj.setDeviceRole(host, role)
            return True

    
    def setDeviceRID(self, host):
        #自动设置设备rid
        with DeviceModel(self.fabric) as dbobj:
            ridList = dbobj.queryRid()
        g = distribute_RID()
        while True:
            rid = next(g)
            if rid not in ridList:
                break
        with DeviceModel(self.fabric) as dbobj:
            dbobj.createRID(host, rid)
            return rid

    
    def setDeviceNVE(self, host):
        #自动设置设备nve
        with DeviceModel(self.fabric) as dbobj:
            nveList = dbobj.queryNve()
        g = distribute_NVE()
        while True:
            nve = next(g)
            if nve not in nveList:
                break
        with DeviceModel(self.fabric) as dbobj:
            dbobj.createNVE(host, nve)
            return nve


    @Multi_threading
    def collectDevice(self, kwargs):
        #执行设备纳管操作,并且添加NVE和RID的IP
        host = kwargs["host"]
        collection = self.collect(host)
        try:
            rid = self.setDeviceRID(host)
            nve = self.setDeviceNVE(host)
        except:
            self.deleteDevice(host)
            raise
        config = {"loopback126": (nve, "NVE"), "loopback127": (rid, "RID")}
        IPConfiguration(host, config)
        #配置环回口


    @Multi_threading
    def evpnEnable(self, kwargs):
        host = kwargs["host"]
        overlay_evpn(host)


    @Multi_threading
    def createNVE(self, kwargs):
        host = kwargs["host"]
        create_nve(self.fabric, host)
    

    def createFabric(self,*args):
        #创建fabric的逻辑
        #1、确定fabric内所有的设备 -- collectDevice
        #2、扫描设备的链路，并且排除非fabric内的设备互联
        #3、将所有互联写入到DeviceLldp表中，IP_ENABLE为默认的null值
        #4、扫描DeviceLldp，将值为null的项取出，校验，通过Lldp.distribute分配IP，写入数据库，IP_ENABLE至为TRUE
        #5、配置IP
        ip_dict = {}
        for i in args:
            #{"192.168.140.101":{"host": "192.168.140.101"}}
            ip_dict[i] = {"host": i}
        self.collectDevice(**ip_dict) 
        self.evpnEnable(**ip_dict)  #开启overlay_evpn
        self.createNVE(**ip_dict)   #创建nve接口
        lldpInstance = Lldp(self.fabric)
        lldpInstance.linkSummary(*args)
        print("正在配置互联......")
        lldpInstance.underlayIPConfig()
        print("正在配置OSPF......")
        ospfConfig = OSPF(self.fabric)
        ospfConfig.ospf_build()
        # bgpInstance = BGP(self.fabric)
        # bgpInstance.bgp_build()    


class Lldp:
    def __init__(self, fabric):
        self.fabric = fabric
        checkFabric(fabric)


    def distribute(self, arg):
        #给一对互联分配互联地址，需要传入一对互联信息({"device1":"port1"}, {"device2":"port2"}) --> ({"192.168.140.100": "G1/0/1"}, {"192.168.140.101": "G1/0/1"})
        #分配好后会写入数据库
        res = []
        g = linkIP()
        with IPDistribute(self.fabric) as dbobj:
            segment_now = dbobj.querySegment()
        while True:
            link_segment = next(g)
            link_segment = link_segment.replace("/16", "/30")
            if link_segment in segment_now:
                continue
            else:
                link_segment_item = list(netaddr.IPNetwork(link_segment))[1:3]
                for i in arg:
                    res.append({"segment":link_segment, "device":list(i.keys())[0], "port": list(i.values())[0], "ip": str(link_segment_item.pop()) + '/30'})
                #记录互联信息
                with IPDistribute(self.fabric) as dbobj:
                    segment_now = dbobj.recordSegment(tuple(res))
                return tuple(res)

    
    def getDeviceNei(self, host):
        #获取设备的远端信息
        #res返回：
        #({'192.168.140.100': 'GE1/0/1', '192.168.140.101': 'GE1/0/0'},)
        #({'192.168.140.100': 'GE1/0/2', '192.168.140.102': 'GE1/0/0'},)
        info = LldpInfo.deviceNei(host)
        res = []
        for i in info:
            res.append(tuple([{i["local_ip"]: i["local_port"], i["remote_ip"]: i["remote_port"]}]))
        return res

    
    def linkSummary(self, *args):
        #传入多个IP,对它们之间的链路进行扫描
        #每台设备都会获取自己的lldp邻居信息,但是链路会去重
        deviceNei = []
        for ip in args:
            deviceNei += self.getDeviceNei(ip)
        links = []
        for i in deviceNei:
            links.append(i[0])
        links_dict = []
        for i in [tuple(i.items()) for i in links]:
            if dict(i) not in links_dict and i[0][0] in args and i[1][0] in args:
                #链路两端的ip必须都在args里面，防止采集到fabric外的链路
                links_dict.append(dict(i))
        for i in links_dict:
            link_tuple = tuple(i.items())
            localPort = link_tuple[0][1]
            localIp = link_tuple[0][0]
            remotePort = link_tuple[1][1]
            remoteIp = link_tuple[1][0]
            with DeviceLldp(self.fabric) as dbobj:
                res = dbobj.createItem(localPort, localIp, remotePort, remoteIp)
                if res == False:
                    raise linkExist(i)
    
    
    def linkQuery(self):
        #查询当前未配置ip的链路
        with DeviceLldp(self.fabric) as dbobj:
            res = dbobj.linkIPDisable()
        return res


    @Multi_threading
    def ipConfig(self, kwargs):
        host = kwargs["host"]
        config = kwargs["config"]
        IPConfiguration(host, config)


    def underlayIPConfig(self):
        #先查询数据库，获取未配置的链路,会对整个数据库对应的所有设备做操作
        res = []
        link_noIP = self.linkQuery()
        #根据链路分配IP, 并且把DeviceLldp库中的链路表项的IP_ENABLE字段置为True
        for link in link_noIP:
            arg = ({link[2]: link[1]}, {link[4]: link[3]})
            res.append(self.distribute(arg))
            with DeviceLldp(self.fabric) as dbobj:
                dbobj.IP_ENABLE_SET(link[0])
        #把二层口转成三层口
        ports = {}
        for i in res:
            for j in i:
                if j["device"] not in ports:
                    ports[j["device"]] = [j["port"]]
                else:
                    ports[j["device"]].append(j["port"])
        #portSwitch需要传入字典，
        portSwitch(False, ports)
        #res中放着本次分配的设备端口IP，根据这个信息对交换机进行配置
        #res : [({'segment': '10.10.0.24/30', 'device': '192.168.140.101', 'port': 'GE1/0/0', 'ip': '10.10.0.26/30'}, {'segment': '10.10.0.24/30', 'device': '192.168.140.102', 'port': 'GE1/0/0', 'ip': '10.10.0.25/30'}), 
        #       ({'segment': '10.10.0.28/30', 'device': '192.168.140.101', 'port': 'GE1/0/1', 'ip': '10.10.0.30/30'}, {'segment': '10.10.0.28/30', 'device': '192.168.140.103', 'port': 'GE1/0/0', 'ip': '10.10.0.29/30'})]
        devicePortInfo = {}
        #处理res
        for i in res:
            devicePortInfo.setdefault(i[0]["device"],{}).update({i[0]["port"]: (i[0]["ip"], i[1]["device"] + "_" + i[1]["port"] + "_" + i[1]["ip"])})
            devicePortInfo.setdefault(i[1]["device"],{}).update({i[1]["port"]: (i[1]["ip"], i[0]["device"] + "_" + i[0]["port"] + "_" + i[0]["ip"])})
        kwargs = {}
        for k, v in devicePortInfo.items():
            kwargs[k] = {"host": k, "config": v}
        self.ipConfig(**kwargs)  #多进程配置IP地址


class OSPF:
    def __init__(self, fabric):
        self.fabric = fabric
        checkFabric(fabric)


    def ospf_build(self, kwargs=None):
        #创建ospf
        #根据链路数据库里的端口，在端口上配置ospf
        #传入参数和没有传入参数需要分开处理
        #配置ospf，需要传入数据如{'192.168.140.101': ['GE1/0/0', 'GE1/0/1'], '192.168.140.102': ['GE1/0/0'], '192.168.140.103': ['GE1/0/0']}
        if not kwargs:
            with IPDistribute(self.fabric) as dbobj:
                ipList = dbobj.queryDevicePorts()
            ospf_configuration(self.fabric, True, True, ipList)
        else:
            pass


class BGP:
    def __init__(self, fabric):
        self.fabric = fabric
        checkFabric(fabric)


    def bgp_members(self):
        #需要确认的参数：设备，rid，角色（决定是否是spine，是否是反射器），是否是更新单台设备，如果是更新单台设备，需要哪些信息
        #{"ip","role","neighbor","as"}
        with DeviceModel(self.fabric) as dbobj:
            deviceRole = dbobj.queryDeviceAndRole()
        deviceInfo = {}
        spine = []
        for i in deviceRole:
            deviceInfo.setdefault(i[0], {}).update({"role": i[1]})
            if i[1] == "spine":
                spine.append(i[0])
            deviceInfo[i[0]]["as"] = Setting.context["AS"]
            deviceInfo[i[0]]["host"] = i[0]
        for i in deviceInfo:
            if deviceInfo[i]["role"] == "leaf":
                deviceInfo[i]["neighbor"] = []
                for k in spine:
                    deviceInfo[i]["neighbor"].append(k)
            elif deviceInfo[i]["role"] == "spine":
                deviceInfo[i]["neighbor"] = [j for j in deviceInfo if j != i]
        return deviceInfo
    

    def bgp_run(self, kwargs):
        #创建BGP
        role = kwargs["role"]
        AS = kwargs["as"]
        neighbor = kwargs["neighbor"]
        host = kwargs["host"]
        bgp_configuration(self.fabric, host, role, neighbor, AS)


    def L2VPN(self, kwargs):
        """
        需要先创建BGP
        配置L2VPN，需要确认设备是不是spine，本端IP已经对端IP
        localIP: RID
        """
        role = kwargs["role"]
        AS = kwargs["as"]
        neighbors = kwargs["neighbor"]
        host = kwargs["host"]
        device = {
            "host": host,
            "device_type": "huawei",
            "username": Setting.context["NETCONF_USER"],
            "password": Setting.context["NETCONF_PWD"]}
        net_connect = ConnectHandler(**device)
        command_list = ["bgp %s" %AS,"l2vpn-family evpn","undo policy vpn-target"]
        for neighbor in neighbors:
            command_list.append("peer %s enable" %getRid(self.fabric, neighbor))
            command_list.append("y")
            command_list.append("peer %s advertise irb" %getRid(self.fabric, neighbor))
            if role == "spine":
                command_list.append("peer %s reflect-client" %getRid(self.fabric, neighbor))
        command_list.append("commit")
        net_connect.send_config_set(command_list, cmd_verify=False)
        net_connect.disconnect()

    
    @Multi_threading
    def bgp_unit(self, kwargs):
        #创建BGP和配置L2VPN
        self.bgp_run(kwargs)
        self.L2VPN(kwargs)


    def bgp_build(self):
        kwargs = self.bgp_members()
        self.bgp_unit(**kwargs)


class VPC:
    def __init__(self, fabric):
        self.fabric = fabric
        checkFabric(fabric)

    
    def createVPC(self, vpc_name):
        with VPCModel(self.fabric) as dbobj:
            dbobj.createVPCTable()
        with DeviceModel(self.fabric) as dbobj:
            deviceList = dbobj.queryDeviceList()
        with VPCModel(self.fabric) as dbobj:
            VPCcurrent = dbobj.VPCNameOccupy()
        if vpc_name in VPCcurrent:
            raise VPCExist(vpc_name)
        kwargs = {}
        for i in deviceList:
            kwargs[i] = {"host": i, "vpc_name": vpc_name}
        self.createBD(**kwargs)


    def deleteVPC(self, vpc_name):
        #通过vpc_name获得对应的vni
        with VPCModel(self.fabric) as dbobj:
            vni = dbobj.getVNI(vpc_name)
        with VPCModel(self.fabric) as dbobj:
            #删除表项
            dbobj.deleteVPC(vpc_name)
        with DeviceModel(self.fabric) as dbobj:
            deviceList = dbobj.queryDeviceList()
        kwargs = {}
        for i in deviceList:
            kwargs[i] = {"host": i, "vni": vni}
        self.deleteDB(**kwargs)
        
        

    
    @Multi_threading
    def createBD(self, kwargs):
        #创建BD
        #{"host": "192.168.140.101", "vpc_name": "hcie"}
        host = kwargs["host"]
        name = kwargs["vpc_name"]
        vni = self.getNewVni()
        vpc_name = self.vpc_name(name)
        rd = self.evpn_rd(host, vni)
        ert = self.evpn_ert(vni)
        irt = self.evpn_irt(vni)
        createBD(host, vni, vpc_name, rd, ert, irt)
        with VPCModel(self.fabric) as dbobj:
            dbobj.createVPC(vni, vpc_name, rd, ert, irt)


    @Multi_threading
    def deleteDB(self, kwargs):
        #{"host": "192.168.140.101", "vni": "hcie"}
        host = kwargs["host"]
        vni = kwargs["vni"]
        deleteDB(host, vni)


    def vpc_name(self,name):
        return name


    def evpn_rd(self,host,vni):
        return "%s:%s" %(host, vni)


    def getNewVni(self):
        with VPCModel(self.fabric) as dbobj:
            vniOccupied = dbobj.vniOccupy()
        for i in range(int(Setting.context["VNI_RANGE"][0]), int(Setting.context["VNI_RANGE"][1])+1):
            if str(i) not in vniOccupied:
                vni = i
                break
        else:
            raise TypeError
        return vni


    def evpn_ert(self, vni):
        return "%s:%s" %(vni,vni)

    
    def evpn_irt(self, vni):
        return "%s:%s" %(vni,vni)


class Fabric_logic:
    #用来新建fabric
    def create(self, name):
        try:
            with Fabric(name) as dbobj:
                dbobj.createTable()
        except sqlite3.IntegrityError:
            raise fabricExist(name)
        else:
            return True


    


if __name__ == "__main__":
    #a = BGP("hcie")
    # b = a.bgp_members()
    #a.bgp_members() 
    # a = Fabric_logic()
    # a.create("hcie")
    #a = checkFabric("adsfadf")
    a = VPC("hcie")
    print(a.getNewVni())
    # a.deleteVPC("HCIE")