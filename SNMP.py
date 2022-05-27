import netsnmp
#yutianedu@123

version = 2
community = ""
RemotePort = "161"
Timeout = "500000"
Retries = "3"
AuthProto = "SHA"
AuthPass = ""
PrivProto = "AES"
PrivPass = ""
SecLevel = "authPriv"
SecName = "yutianedu" 


class SNMP:
    #SNMP采集模块
    def __init__(self, host, community=community, version=version):
        self.sess = netsnmp.Session(
            Version=version,
            DestHost=host,
            Community=community
            )

    def get(self,*OIDS):
        def varbind(OIDS):
            VAR = []
            for i in OIDS:
                VAR.append(netsnmp.Varbind("."+i))
            return VAR
        vars = netsnmp.VarList(*varbind(OIDS))
        vals = self.sess.get(vars)
        return vals
        
    def getbulk(self,OIDS):
        def varbind(OIDS):
            VAR = []
            for i in OIDS:
                VAR.append(netsnmp.Varbind(i))
            return VAR
        vars = netsnmp.VarList(*varbind(OIDS))
        self.sess.getbulk(0, 10, vars)
        res = {}
        for var in vars:
            res[str(var.tag)+"."+str(var.iid)] = bytes.decode(var.val)
        return res

    def getnext(self,OID):
        vars = netsnmp.VarList(netsnmp.Varbind(OID))
        vals = self.sess.getnext(vars)
        return bytes.decode(vals[0])

    def walk(self,OID):
        vars = netsnmp.VarList(netsnmp.Varbind(OID))
        self.sess.walk(vars)
        res = {}
        for var in vars:
            res[str(var.tag)+"."+str(var.iid)] = var.val.decode("utf-8")
        return res




if __name__ == "__main__":
    a = SNMP("192.168.140.101")
    print(a.walk(".1.3.6.1.2.1.2.2.1.1"))