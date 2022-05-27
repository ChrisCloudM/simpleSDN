class RoleNameError(Exception):
    def __str__(self):
        return "role name must be spine or leaf"


class HostMissingError(Exception):
    def __init__(self, host):
        self.host = host

    def __str__(self):
        return self.host + " not in DB.DeviceInfo"


class NVEError(Exception):
    def __init__(self,host):
        self.host = host

    def __str__(self):
        return "{IP} NVE IP is Null".format(IP=self.host)


class RouterIDError(NVEError):
    def __str__(self):
        return "{IP} RouterID is Null".format(IP=self.host)


class PortIPNullError(Exception):
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __str__(self):
        return "{IP} - {port} had not distributed IP".format(IP=self.host, port=self.port)


class BGPConfigError(Exception):
    def __init__(self,arg):
        self.arg = arg

    def __str__(self):
        return "Miss {}".format(self.arg)


class NVESRC(Exception):
    def __str__(self):
        return "This host has not been queried in db"


class IPOccupy(Exception):
    def __init__(self,arg):
        self.arg = arg

    def __str__(self):
        return "%s IP has been occupied" %self.arg


class linkExist(Exception):
    def __init__(self,arg):
        self.arg = str(arg)

    def __str__(self):
        return "%s link has existed" %self.arg


class notDevice(Exception):
    def __init__(self,arg):
        self.arg = str(arg)

    def __str__(self):
        return "Not this Device: %s" %self.arg


class fabricExist(Exception):
    def __init__(self, arg):
        self.arg = arg
    
    def __str__(self):
        return "The name of fabric %s has exist" %self.arg


class fabricNotExist(Exception):
    def __init__(self, arg):
        self.arg = arg
    
    def __str__(self):
        return "The name of fabric %s has not exist" %self.arg


class VPCExist(Exception):
    def __init__(self, arg):
        self.arg = arg
    
    def __str__(self):
        return "The name of VPC %s has exist" %self.arg


if __name__ == "__main__":
    raise VPCExist("HCIE")
