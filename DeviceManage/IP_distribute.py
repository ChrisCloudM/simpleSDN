from setting import Setting


def linkIP():
    #分配互联IP，每次分配一个/30的网段，每次都是从头开始分配，使用时需要到数据库进行比对查看占用
    IPinstance = Setting()
    IPs = IPinstance.context["LINK_IP"]
    D_segment = IPs.split("/")[0].split(".")[-1]
    C_segment = IPs.split("/")[0].split(".")[-2]
    AB_segment = ".".join(IPs.split(".")[0:2])
    while True:
        yield AB_segment + "." + C_segment + "." + D_segment + "/16"
        if int(D_segment) == 252:
            if int(C_segment) < 255:
                C_segment = str(int(C_segment) + 1)
                D_segment = "0"
            else:
                raise TypeError
        else:
            D_segment = str(int(D_segment) + 4)


def distribute_RID():
    #分配RID，每次分配一个/32的IP，每次都是从头开始分配，使用时需要到数据库进行比对查看占用
    IPinstance = Setting()
    IPs = IPinstance.context["RID"]
    D_segment = IPs.split("/")[0].split(".")[-1]
    ABC_segment = ".".join(IPs.split(".")[0:-1])
    while True:
        yield ABC_segment + "." + str(int(D_segment) + 1) + "/32"
        if int(D_segment) == 253:
            raise TypeError
        else:
            D_segment = str(int(D_segment) + 1)


def distribute_NVE():
    #分配NVE，每次分配一个/32的IP，每次都是从头开始分配，使用时需要到数据库进行比对查看占用
    IPinstance = Setting()
    IPs = IPinstance.context["NVE"]
    D_segment = IPs.split("/")[0].split(".")[-1]
    ABC_segment = ".".join(IPs.split(".")[0:-1])
    while True:
        yield ABC_segment + "." + str(int(D_segment) + 1) + "/32"
        if int(D_segment) == 253:
            raise TypeError
        else:
            D_segment = str(int(D_segment) + 1)




if __name__ == "__main__":
    g = linkIP()
    for i in range(1, 100):
        print(next(g))