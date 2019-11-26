## Network Prerequisites

### NSX-T Physical Network Requirements

__Note__: The requirements below are suitable for a basic deployment of NSX-T using the pipeline. For more elaborate guidance on the design and deployment at scale and different topologies,  please refer to the NSX-T design official guide: https://communities.vmware.com/docs/DOC-37591

The following are the requirements for deploying nsx-t for PAS/PKS using the pipeline:<br> 

Make sure you have vCenter and clusters setup according to the requirements of the workload you plan to run. Usually, for PAS and PKS, you will need a minimum of a management cluster and a payload cluster. Production environments require a minimum of 3 clusters for availability purposes. 

NSX has its requirements such as resources and network configuration that are detailed here: https://docs.vmware.com/en/VMware-NSX-T/2.2/nsxt_22_install.pdf
For this guide, the assumption is that we deploy NSX-T for PKS or PAS or BOTH in a NATed configuration which allows for multiple deployments with same IP scheme. If Routed configuration is required, you will need to configure the parameter file with the required routed network configuration each time this pipeline is deployed.

### 1. Physical Network Configuration

| # | Network Configuration | Description|
|-------------|------------|------------|
| 1.1| Jumbo frames| The physical switches that the ESXi server with NSX installed are connected to require a minimum of 1600 MTU jumbo frames supported. The vDS port groups where the edges will connect also to need to support 1600 MTU as well (See next part for vDS for edges) 
| 1.2 | Management VLAN | This VLAN will be used for the NSX-Manager, NSX controllers and NSX edges management interface. This network will be provided as regular vDS port groups, usually on a management cluster |
| 1.3 | Management IPs | The following IPs are required on the management VLAN: <br> 1. 1 IP for the NSX manager <br> 2.	An IP for each controller (1 or 3) <br> 3. An IP for each edge management interface|
| 1.4 | Uplink VLAN | This VLAN will be used by the edge VMs to communicate with the next hop switch. This can be the same VLAN as the management VLAN or separate. <br> If the edges are deployed in different Racks with different VLANs then more than one VLAN is required)|
| 1.5 | Edge Uplink IPs | Each edge will require an IP on the uplink VLAN (Tier 0 configuration). An additional IP is required for the HA VIP floating IP. Total of 3 IPs on the uplink network. <br> (BGP is yet to be supported by the pipeline) |
| 1.6 | Transport VLAN/s | Used by the ESXi servers where the workloads will run and by the edges. The ESXi servers and edges will establish an overlay tunnel using this VLAN. <br> If deployed in a spine-leaf configuration this will be multiple VLANs (not supported by the pipeline).|
| 1.7 |VTEP IP pool| The ESXi servers and edges get the IP for the creation of the tunnel on the Transport VLAN from this pool. The VTEP IP Pool or pools (depending on the number of transport networks) needs to provide connectivity between all ESXi servers and edges on the transport network|
| 1.8 | Routing – option 1 - Static route| On the physical switches that are the next hop from the edges, we will need to set up a static route. This static route will point to the Tier0 IP to reach the SNAT/VIP subnet (T0 IP is specified in row #1.5 above. The SNAT/VIP is specified in row #2.5)|
| Option 2 |Proxy ARP|starting from version 2.4 NSX-T supports "Proxy ARP" on T0 (defined as the edge network on 1.4). <br> With this feature, NAT, LB or any stateful services can be configured with an IP address that belong to the network of the Tier0 uplink and no additional routed network and static route or BGP is required to it. |
| 1.9 |Network Card|Each ESXi server that will have logical networks configured will need unused NICs that will be claimed by the NSX nSwitches. <br> you can use the same NICs for both esxi services and NSX-T, if you plan to use only 2 NICs for everything you will need to setup an nVDS on one of the NICs and migrate the esxi services|

The following steps are required for setting up NSX for PAS and/or PKS. 
### 2. PAS Subnets

| # | PAS Subnets | IP Subnet 
|-------------|------------|------------|
|2.1|PAS Infra subnet|Non-routable (NAT) or routable <br> Used for BOSH and Ops manager <br> e.g., 192.168.10.0/24|
|2.2|PAS ERT subnet|Non-routable (NAT) or routable <br> Used by ERT components (Go routers, UAA, DB etc.) <br> e.g. 192.168.20.0/24|
|2.3| PAS Services subnet|Non-routable (NAT) or routable <br> Subnet to be used by the PAS services (such as MySQL) <br> e.g. 192.168.30.0/24|
|2.4| Container IP block | Non-routable IP block (NAT) or routable IP Block to be used to carve out subnets for the AIs networks. <br>  The size will depend on the number of containers needed to be deployed. <br> e.g. PAS containers block - 172.16.0.0/16|
|2.5|SNAT/VIP Ip pool|Routable, used in NATed deployments <br> A routable subnet to be used for the NAT addressee and LB VIPs <br> The static route (#1.8) will point to this network through the T0 HA VIP IP, or this network could be part of the T0 network if Proxy ARP is used <br> e.g. SNAT pool for PAS 10.208.40.0/24|

### 3. PKS Subnets
| # | PKS Subnets | IP Subnet|
|-------------|------------|------------|
|3.1|PKS Infra subnet|Non-routable (NAT) or routable <br> Used for BOSH and Ops manager <br> e.g., 192.168.50.0/24|
|3.2| PKS Services Subnet| Non-routable (NAT) or routable <br> USed for PKS API and Harbor <br> e.g. 192.168.60.0/24|
|3.3| Node IP block| Non-routable IP Block, IP Block to carve out subnets for the dynamically created node networks (where the masters and workers are). The size of the subnet will depend on the number of clusters needed to be deployed (/24 for each cluster). <br> e.g. PKS containers block - 172.14.0.0/16 is at least a /16 as a /24 will be taken for each name space| 
|3.4| Container IP block| Non-routable IP Block, IP Block to carve out subnets for the dynamically created namespace networks. The size of the subnet will depend on the number of containers needed to be deployed. <br> e.g. PKS containers block - 172.15.0.0/16 is at least a /16 as a /24 will be taken for each name space|
|3.5| SNAT/VIP Ip pool| Routable, used in NATed deployments <br> A routable subnet to be used for the NAT addressee and LB VIPs <br> The static route (#1.8) will point to this network through the T0 HA VIP IP (#1.5)<br> e.g. SNAT pool for PKS 10.208.50.0/24
or this network could be part of the T0 network if Proxy ARP is used |

### 4. DNS Records
Required for later deployment of PKS and/or PAS

|#| DNS Record| Attribute|
|-------------|------------|------------|
|4.1|NSX-T manager|The NSX-T manager FQDN pointing to its management IP|
|4.2|PAS Operations manager| DNS record pointing to the PAS operations manager DNAT IP (If routed direct IP)|
|4.3|*.apps.fqdn|The record for the apps wildcard name in PAS pointing to the GoRouters  LB VIP IP |
|4.4|*.sys.fqdn|The record for the system wildcard name in PAS pointing to the GoRouters  LB VIP IP|
|4.5|PKS Operations manager|Record pointing to PKS operations manager DNAT IP (If routed direct IP)|
|4.6|PKS UAA service|Record pointing to PKS UAA DNAT IP e.g. uaa.pks<domain> (If routed direct IP)|
|4.7|PKS API service|Record pointing to PKS API Service DNAT IP e.g. api.pks<domain> (If routed direct IP)|
|-------------|------------|------------|
note - IPs for UAA (4.5) and API (4.6) are the same currently 


