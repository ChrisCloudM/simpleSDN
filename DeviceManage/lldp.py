from SNMP import SNMP
from DeviceManage.DB_Operation import DeviceModel
import copy


def sysname_ip(fabric, host):
    #通过数据库查询设备名
    """
    sysName_ip:  {'Border': '192.168.140.100'}
    """
    with DeviceModel(fabric) as obj:
        res = obj.queryName(host)
        return res


def interfaceIndex(host):
    #查询设备端口索引
    """
    ifindex:  {'MEth0/0/0': '1', 'GE1/0/0': '2', 'GE1/0/1': '3', 'GE1/0/2': '4', 'GE1/0/3': '5', 'GE1/0/4': '6', 'GE1/0/5': '7', 'GE1/0/6': '8', 'GE1/0/7': '9', 'GE1/0/8': '10', 'GE1/0/9': '11'}
    """
    snmpInstance = SNMP(host)
    _ifindex = snmpInstance.walk(".1.0.8802.1.1.2.1.3.7.1.3")
    ifindex = {}
    for k,v in _ifindex.items():
        ifindex[k.split("iso.0.8802.1.1.2.1.3.7.1.3.")[-1].replace(".","")] = v.decode("utf-8")
    return ifindex


class LldpInfo:
    @classmethod
    def deviceNei(self, host):
        #获取设备的链路
        """
        获取管理IP所在设备的链路
        {port1 : {ip : port}, port2 : {ip : port}}
        """
        res = []
        link = {}
        ifindex = interfaceIndex(host)
        #端口索引
        snmpInstance = SNMP(host)
        _remote_device = snmpInstance.walk(".1.0.8802.1.1.2.1.4.2.1.3")
        _oid_prefix = snmpInstance.walk(".1.0.8802.1.1.2.1.4.1.1.7")
        _prefix_iter = iter(_oid_prefix.keys())
        oid_prefix = next(_prefix_iter).rstrip(".").split(".")
        
        for k in _remote_device.keys():
            index = k.split(".")[-9]
            oid_prefix[-2] = index
            oid = ".".join(i for i in oid_prefix).replace("iso","1")
            remote_ip = ".".join(i for i in k.split(".")[-5:-1])
            local_port = ifindex[index]
            remote_port = snmpInstance.get(oid)[0].decode("utf-8")
            link["local_ip"] = host
            link["local_port"] = local_port
            link["remote_ip"] = remote_ip
            link["remote_port"] = remote_port
            res.append(copy.deepcopy(link))
        return res



if __name__ == "__main__":
    print(LldpInfo.deviceNei("192.168.140.101"))