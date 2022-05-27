import fire
from DeviceManage.operation import Device, Fabric_logic, VPC, BGP
from other.exceptions import *
import threading


class FabricCli:
    def create(self, name):
        crtFabric = Fabric_logic()
        crtFabric.create(name)
        print("%s has created successfully" %name)
        

class DeviceOperation:
    def __init__(self, fabric):
        self.fabric = fabric


    def collect(self, *ip):
        if self.fabric == None or ip == None:
            print("fabric or ip can't be None")
        dev_class = Device(self.fabric)
        res = dev_class.createFabric(*ip)
        if res:
            print(res)


    def setrole(self, ip=None, role=None):
        if self.fabric == None or ip == None or role == None:
            print("fabric or ip or role can't be None")
        dev_class = Device(self.fabric)
        res = dev_class.setDeviceRole(ip, role)
        if res:
            print("%s has been set %s" %(ip, role))
        else:
            print("Someting Wrong had happend, please check out")
    

    def createbgp(self):
        bgpInstance = BGP(self.fabric)
        bgpInstance.bgp_build()
        


class VPCCli:
    def __init__(self, fabric=None):
        self.fabric = fabric


    def create(self, name):
        try:
            vpc_instance = VPC(self.fabric)
            vpc_instance.createVPC(name)
            print("%s VPC创建成功" %name)
        except VPCExist:
            print("%s VPC已经被占用" %name)
        except:
            print("%s VPC创建失败" %name)

    
    def delete(self,name):
        try:
            vpc_instance = VPC(self.fabric)
            vpc_instance.deleteVPC(name)
            print("%s VPC删除成功" %name)
        except:
            print("%s VPC删除失败" %name)


class Groups:
    def __init__(self, fabric=None):
        self.device = DeviceOperation(fabric)
        self.fabric = FabricCli()
        self.vpc = VPCCli(fabric)

    
if __name__ == "__main__":
    fire.Fire(Groups)