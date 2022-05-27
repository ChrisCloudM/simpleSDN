from Netconf_Client.client import Netconf
from DeviceManage.DB_Operation import DeviceModel
from other.exceptions import *
from setting import Setting
from netaddr import *
import threading


def getRid(fabric, host):
    #通过管理IP获取rid
    with DeviceModel(fabric) as dbobj:
        res = dbobj.queryRid(host)
    if res:
        return res[0].split("/")[0]


def configurate(host,api):
    #用于多线程配置交换机
    session = Netconf(host)
    session.netconf_edit_config(api)


def IPConfiguration(host, kwargs):
    #配置ip地址
    #kwargs为字典参数，key为端口，value为(IP,描述)
    api_head = """<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <interfaces>
    """
    api_tail = """</interfaces>
    </ifm>
    </config>
    """
    api_body_form = """<interface xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <ifName>%s</ifName>
        <ifDescr>%s</ifDescr>
        <ifAdminStatus>up</ifAdminStatus>
        <ipv4Config>
            <am4CfgAddrs>
                <am4CfgAddr nc:operation="create">
                    <ifIpAddr>%s</ifIpAddr>
                    <subnetMask>%s</subnetMask>
                    <addrType>main</addrType>
                </am4CfgAddr>
            </am4CfgAddrs>
        </ipv4Config>
    </interface>
    """
    api = api_head
    for k, v in kwargs.items():
        ip = str(IPNetwork(v[0]).ip)
        subnet = str(IPNetwork(v[0]).netmask)
        api = api + api_body_form %(k, v[1], ip, subnet)
    api = api + api_tail
    session = Netconf(host)
    session.netconf_edit_config(api)


def portSwitch(mode, ports):
    """
    切换端口23层状态，传入的字典包括端口和二三层状态
    mode: True为二层，False为三层
    """
    #生成以太网口配置节点
    if mode:
        switch_mode = "enable"
    else:
        switch_mode = "disable"
    api_head = """<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <ethernet xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <ethernetIfs>
    """
    api_tail = """
            </ethernetIfs>
        </ethernet>
    </config>
    """
    api_body_form = """
    <ethernetIf operation="merge">
        <ifName>%s</ifName>
        <l2Enable>%s</l2Enable>
    </ethernetIf>
    """
    api_dict = {}
    for k, v in ports.items():
        api_body = ""
        for i in v:
            api_body += api_body_form %(i, switch_mode)
            api = api_head + api_body + api_tail
        else:
            api_dict[k] = api
    threading_list = []
    for k, v in api_dict.items():
        threading_list.append(threading.Thread(target=configurate, args=(k,v), name=k))
    for i in threading_list:
        i.start()
    for i in threading_list:
        i.join()


def ospf_configuration(fabric, RID, NVE, kwargs):
    #fabric : fabric的名字
    #NVE: 是否通告nve ip
    #RID：是否通告rid ip
    #配置ospf，需要传入数据如{'192.168.140.101': ['GE1/0/0', 'GE1/0/1'], '192.168.140.102': ['GE1/0/0'], '192.168.140.103': ['GE1/0/0']}
    api_header = """
    <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <ospfv2 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <ospfv2comm>
          <ospfSites>
            <ospfSite>
              <processId>1</processId>
              <routerId>%s</routerId>
              <areas>
                <area>
                  <areaId>0.0.0.0</areaId>
                  <interfaces>""" 
    api_tail = """
                  </interfaces>
                </area>
              </areas>
            </ospfSite>
          </ospfSites>
        </ospfv2comm>
      </ospfv2>
    </config>
    """
    api_body_form = """
    <interface operation="create">
        <ifName>%s</ifName>
        <networkType>p2p</networkType>
    </interface>
    """
    api_dict = {}
    #合成api
    for k, v in kwargs.items():
        api_body = ""
        with DeviceModel(fabric) as dbobj:
            rid = dbobj.queryRid(k)[0].split("/")[0]
        if RID == True:
            v.append("LoopBack127")
        if NVE == True:
            v.append("LoopBack126")
        for port in v:
            api_body += api_body_form %port
        else:
            api = api_header %rid + api_body + api_tail
            api_dict[k] = api
    thread_list = []
    #配置ospf
    for k, v in api_dict.items():
        thread_list.append(threading.Thread(target=configurate, args=(k,v), name=k))
    for i in thread_list:
        i.start()
    for i in thread_list:
        i.join()


def bgp_configuration(fabric, host=None, role=None, neighbor=None, AS=None):
    #配置bgp
    #这个函数需要考虑到两个情况，一个是设备初始化的时候，一个是单独添加某一台设备的时候
    # {'role': 'leaf', 'as': '100', 'neighbor': ['192.168.140.103', '192.168.140.101']}
    rid = getRid(fabric, host)
    api_header = """
    <config>
    <bgp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <bgpcomm>
        <bgpSite operation="merge">
            <bgpEnable>true</bgpEnable>
            <asNumber>%s</asNumber>
        </bgpSite>
		<bgpVrfs>
            <bgpVrf>
                <vrfName>_public_</vrfName>
                <routerId>%s</routerId>
                <bgpPeers>
    """ %(AS, rid)
    api_tail = """
                </bgpPeers>
            </bgpVrf>
        </bgpVrfs>
    </bgpcomm>
    </bgp>
    </config>
    """
    api_body_from = """
    <bgpPeer operation="create">
        <peerAddr>%s</peerAddr>
        <remoteAs>%s</remoteAs>
		<localIfName>loopback127</localIfName>
    </bgpPeer>
    """
    api_body = ""
    for i in neighbor:
        rid = getRid(fabric, i)
        if not rid:
            raise HostMissingError(i)
        api_body += api_body_from %(rid, AS)
    api = api_header + api_body + api_tail
    session = Netconf(host)
    session.netconf_edit_config(api)


def overlay_evpn(host):
    api = """
    <config>
    <evn xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <evnGlobal operation="merge">
          <evpnOverLay>true</evpnOverLay>
        </evnGlobal>
    </evn>
    </config>
    """
    session = Netconf(host)
    session.netconf_edit_config(api)


def create_nve(fabric, host):
    #创建NVE接口
    rid = getRid(fabric, host)
    api = """
    <config>
    <ifm content-version="1.0" format-version="1.0" xmlns="http://www.huawei.com/netconf/vrp">
        <interfaces>
            <interface operation="merge">
                <ifName>Nve1</ifName>
            </interface>
        </interfaces>
    </ifm>
    <nvo3 content-version="1.0" format-version="1.0" xmlns="http://www.huawei.com/netconf/vrp">
        <nvo3Nves>
            <nvo3Nve operation="merge">
                <ifName>Nve1</ifName>
                    <nveType>mode-l2</nveType>
                <srcAddr>%s</srcAddr>
            </nvo3Nve>
        </nvo3Nves>
    </nvo3>
    </config>
    """ %rid
    session = Netconf(host)
    session.netconf_edit_config(api)


def createBD(host, vni, vpc_name, rd, ert, irt):
    #创建BD
    api = """
    <config>
      <evc xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bds>
          <bd operation="merge">
            <bdId>{vni}</bdId>
            <bdDesc>vpc {vpc_name} create by openytedu</bdDesc>
            <statistic>disable</statistic>
            <macLearn>enable</macLearn>
          </bd>
        </bds>
      </evc>
      <nvo3 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <nvo3Vni2Bds>
          <nvo3Vni2Bd operation="merge">
            <vniId>{vni}</vniId>
            <bdId>{vni}</bdId>
          </nvo3Vni2Bd>
        </nvo3Vni2Bds>
        <nvo3Nves>
          <nvo3Nve>
            <ifName>Nve1</ifName>
            <vniMembers>
              <vniMember operation="merge">
                <vniId>{vni}</vniId>
                <protocol>bgp</protocol>
              </vniMember>
            </vniMembers>
          </nvo3Nve>
        </nvo3Nves>
      </nvo3>
      <evpn xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <evpnInstances>
          <evpnInstance operation="merge">
            <evpnName>{vni}</evpnName>
            <bdId>{vni}</bdId>
            <evpnRD>{rd}</evpnRD>
            <evpnRTs>
              <evpnRT operation="merge">
                <vrfRTValue>{irt}</vrfRTValue>
                <vrfRTType>import_extcommunity</vrfRTType>
              </evpnRT>
              <evpnRT operation="merge">
                <vrfRTValue>{ert}</vrfRTValue>
                <vrfRTType>export_extcommunity</vrfRTType>
              </evpnRT>
            </evpnRTs>
          </evpnInstance>
        </evpnInstances>
      </evpn>
    </config>""".format(vni=vni, vpc_name=vpc_name, rd=rd, irt=irt, ert=ert)
    session = Netconf(host)
    session.netconf_edit_config(api)


def deleteDB(host, vni):
    #删除BD域
    api = """
    <config>
      <evc xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bds>
          <bd operation="delete">
            <bdId>%s</bdId>
          </bd>
        </bds>
      </evc>
    </config>
    """ %vni
    session = Netconf(host)
    session.netconf_edit_config(api)




if __name__ == "__main__":
    print(getRid("hcie", "192.168.140.101"))
    a = bgp_configuration("hcie", "192.168.140.101", "spine", ['192.168.140.102', '192.168.140.103'], "100")
    #overlay_evpn("192.168.140.101")
    #create_nve("hcie", "192.168.140.101")
    #createBD("192.168.140.101", "1", "hcie", "192.168.140.101:1", "1:1", "1:1")
    #deleteDB("192.168.140.101", "1")