from ncclient import manager
from setting import Setting


class Netconf:
    def __init__(self, host ,device_type="huawei"):
        self.session = manager.connect(host=host,
                                port="830",
                                username=Setting.context["NETCONF_USER"],
                                password=Setting.context["NETCONF_PWD"],
                                hostkey_verify = False,
                                device_params={'name': device_type},
                                allow_agent = False,
                                look_for_keys = False)


    def netconf_edit_config(self, api):
        self.session.edit_config(target="running",config=api)
        self.session.close_session()



    def netconf_get_config(self, api):
        res = self.session.get_config(source="running")
        self.session.close_session()
        return res


if __name__ == "__main__":
    api = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">  
<ospfv2 xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">      
<ospfv2comm>          
<ospfSites>            
<ospfSite>              
<processId>1</processId>            
<routerId>172.16.254.1</routerId>            
<areas>               
<area>              
<areaId>0.0.0.0</areaId>               
<interfaces> 
<interface operation="create">       
<ifName>GE1/0/0</ifName>       
<networkType>p2p</networkType>   
</interface>   
<interface operation="create">      
<ifName>GE1/0/1</ifName>       
<networkType>p2p</networkType>   
</interface>
<interface operation="create">       
<ifName>GE1/0/0</ifName>   
<networkType>p2p</networkType>   
</interface>                
</interfaces>               
</area>           
</areas>           
</ospfSite>          
</ospfSites>        
</ospfv2comm>     
</ospfv2>    
</config>"""
    a = Netconf("192.168.140.102", "huawei")
    print(a.netconf_edit_config(api))