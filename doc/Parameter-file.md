## Parameter file

The following are the sections of the parameter for the pipeline (if you are running it using the Docker image it will be placed in /home/concourse/nsx_pipeline_config.yml): <br>

### General: <br>

**nsx_t_pipeline_branch: master** <br>
Use 'master' for 2.4.0 and later deployments. use 'nsxt_2.3.0' for earlier deployments. <br>
DO NOT specify this parameter if using nsx-t-install docker image <br>
**nsxt_ansible_branch: master** <br>
Use 'master' for 2.4.0 and later deployments. use 'v1.0.0' for earlier deployments. <br>
DO NOT specify this parameter if using nsx-t-install docker image <br>

### NSX parameters: 

The following configuration is for the vCenter where the NSX Manager and controllers will be deployed <br>
_**vcenter_ip: 192.168.110.22                    <br>**_
_**vcenter_username: administrator@corp.local    <br>**_
_**vcenter_password: "VMware1!"                  <br>**_
_**vcenter_datacenter: RegionA01                <br>**_
_**vcenter_cluster: RegionA01-MGMT      #management cluster <br>**_
_**vcenter_datastore: iscsi   <br>**_

<br>
This is the configuration for the NSX manager networking 
<br>

_**mgmt_portgroup: 'ESXi-RegionA01-vDS-COMP'**     <br>_
_**dns_server: 192.168.110.10** <br>_
_**dns_domain: corp.local.io** <br>_
_**ntp_servers: time.vmware.com** <br>_
_**default_gateway: 192.168.110.1** <br>_
_**netmask: 255.255.255.0** <br>_
<br>

The nsx_image_webserver is where you placed the files. It can either be the auto-deployed nginx by the nsx-t-concourse docker image, or any other web server that you placed the files in <br>
**nsx_image_webserver: "http://192.168.110.11:40001"**
 <br>
<br>

Here you can specify the management components configuration. 
(Note – If resource_reservation_off: is set to false, in case the pipeline failed after deployment of the manager and controllers because of resource constraints the next run will remove the Memory reservations of these VMs. This is useful for lab purposes only)<br>
**nsx_manager_ip: 192.168.110.33** <br>
**nsx_manager_username: admin** <br>
**nsx_manager_password: VMware1!** <br>
**nsx_manager_assigned_hostname: "nsxt-man.corp.local" # Set as FQDN, will be used also as certificate common name** <br>
**nsx_manager_root_pwd: VMware1!    # Min 8 chars, upper, lower, number, special digit** <br>
**nsx_manager_deployment_size: small   # small, medium, large** <br>
**resource_reservation_off: true** <br>
**nsx_manager_ssh_enabled: true** <br>
<br>

Compute manager config serves 2 purposes. For deploying the Edges and controllers using the NSX manager API and for auto installation of NSX on the vSphere clusters. <br>
The pipeline currently supports two vCenters in the pipeline. <br>
**compute_manager_username: "Administrator@corp.local"** <br>
**compute_manager_password: "VMware1!"** <br>
**compute_manager_2_username:** <br>
**compute_manager_2_vcenter_ip:** <br>
**compute_manager_2_password:** <br>
<br>
<br>

Do not configure the following parameters if you plan to use the cluster auto install. This section is used with per ESXi server/edge installation.  <br>
**# For outbound uplink connection used by Edge, usually keep as 0** <br>
**edge_uplink_profile_vlan: 0** <br>
**# For internal overlay connection used by ESXi hosts, usually transport VLAN ID** <br>
**esxi_uplink_profile_vlan: 0** 
<br>
<br>

This is the configuration of the VTEP pool to be used by the ESXi servers and edges. <br>
**vtep_ip_pool_name: tep-ip-pool** <br>
**vtep_ip_pool_cidr: 192.168.213.0/24** <br>
**vtep_ip_pool_gateway: 192.168.213.1** <br>
**vtep_ip_pool_start: 192.168.213.10** <br>
**vtep_ip_pool_end: 192.168.213.200** <br>
<br>
<br>

Tier 0 configuration. Note only the HA VIP and static route is currently supported by the pipeline <br>
**tier0_router_name: DefaultT0Router** <br>
**tier0_uplink_port_ip: 192.168.100.4** <br>
**tier0_uplink_port_subnet: 24** <br>
**tier0_uplink_next_hop_ip: 192.168.100.1** <br>
**tier0_uplink_port_ip_2: 192.168.100.5** <br>
**tier0_ha_vip: 192.168.100.3** <br>
<br>

NSX controller configuration. <br> 
Note, if specifying more than 1 IPs in controller_ips the pipeline will deploy multiple controllers. Supported configurations are 1 or 3 controllers. <br>
**controller_ips: 192.168.110.34        #comma separated based in number of required controllers** <br>
**controller_default_gateway: 192.168.110.1** <br>
**controller_ip_prefix_length: 24** <br>
**controller_hostname_prefix: controller # no spaces, Generated name: controller_1.corp.local.io** <br>
**controller_vmname_prefix: controller-vm # Generated edge host name would be "NSX-T controller-vm_1"** <br>
**controller_cli_password: "VMware1!" # Min 8 chars, upper, lower, num, special char** <br>
**controller_root_password: "VMware1!"** <br>
**controller_deployment_size: SMALL** <br>

**vc_datacenter_for_controller: RegionA01** <br>
**vc_cluster_for_controller: RegionA01-MGMT** <br>
**vc_datastore_for_controller: iscsi** <br>
**vc_management_network_for_controller: "ESXi-RegionA01-vDS-COMP"** <br>
**controller_shared_secret: "VMware1!VMware1!"** <br>
<br>

Edge nodes <br>
**edge_ips: 192.168.110.37, 192.168.110.38    #comma separated based in number of required edges** <br>
**edge_default_gateway: 192.168.110.1** <br>
**edge_ip_prefix_length: 24** <br>
**edge_hostname_prefix: nsx-t-edge** <br>
**edge_fabric_name_prefix: EdgeNode** <br>
**edge_transport_node_prefix: edge-transp-node** <br>
**edge_cli_password: "VMware1!"** <br>
**edge_root_password: "VMware1!"** <br>
**edge_deployment_size: "large"   #Large recommended for PKS deployments** <br>

**vc_datacenter_for_edge: RegionA01** <br>
**vc_cluster_for_edge: RegionA01-MGMT** <br>
**vc_datastore_for_edge: iscsi** <br>
**vc_uplink_network_for_edge: "ESXi-RegionA01-vDS-COMP"** <br>
**vc_overlay_network_for_edge: "VM-RegionA01-vDS-COMP"** <br>
**vc_management_network_for_edge: "ESXi-RegionA01-vDS-COMP"** <br>
Note, if specifying more than 1 IP in edge_ips the pipeline will deploy multiple edges. <br>
<br>
 

This configuration is to install NSX on vSphere clusters automatically. Specify comma-separated list of clusters to install NSX on and the VLANs they will use. <br>
**clusters_to_install_nsx: RegionA01-MGMT, RegionA01-K8s    #Comma separated** <br>
**per_cluster_vlans: 0, 0** <br>
Note – We yet to support multiple uplink profile assignment <br>
<br>
<br>


Per ESX Installation, If you are not using the “auto cluster install” or if additional ESXi are needed,  specify them here. Otherwise leave the "esx_ips" empty <br>
**esx_ips:** <br>
**esx_os_version: "6.5.0"** <br>
**esx_root_password: "VMware1!"** <br>
**esx_hostname_prefix: "esx-host"** <br>
 <br>

Here specify which physical NICs will be claimed on the ESXi servers. Comma-separated list will work. Note that this applies to both auto installed clusters and individual ESXi hosts <br>
**esx_available_vmnic: "vmnic1"**<br>
<br>





Logical parameters 

The following sections of the parameter file can be customized for your deployment. You can set your configuration according to your requirements, whether PAS, PKS, VMs or anything else. The example below is for both PAS and PKS <br>

Tier-1 distributed routers and switches configuration.  
**nsx_t_t1router_logical_switches_spec: |** <br>
  **t1_routers:** <br>
  **# Add additional T1 Routers or collapse switches into same T1 Router as needed** <br>
  **# Remove unneeded T1 routers** <br>
 <br>
  **- name: T1-Router-PAS-Infra** <br>
    **switches:** <br>
    **- name: PAS-Infra** <br>
      **logical_switch_gw: 192.168.10.1 # Last octet should be 1 rather than 0** <br>
      **subnet_mask: 24** <br>
 <br>
  **- name: T1-Router-PAS-ERT** <br>
    **switches:** <br>
    **- name: PAS-ERT** <br>
      **logical_switch_gw: 192.168.20.1 # Last octet should be 1 rather than 0** <br>
      **subnet_mask: 24** <br>
    **edge_cluster: true** <br>

  **- name: T1-Router-PAS-Services** <br>
    **switches:** <br>
    **- name: PAS-Services** <br>
      **logical_switch_gw: 192.168.30.1 # Last octet should be 1 rather than 0** <br>
      **subnet_mask: 24** <br>
 <br>
  **# Comment off the following T1 Routers if there is no PKS** <br>
  **- name: T1-Router-PKS-Infra** <br>
    **switches:** <br>
    **- name: PKS-Infra** <br>
      **logical_switch_gw: 192.168.50.1 # Last octet should be 1 rather than 0** <br>
      **subnet_mask: 24** <br>
 <br>
  **- name: T1Router-PKS-Services** <br>
    **switches:** <br>
    **- name: PKS-Services** <br>
      **logical_switch_gw: 192.168.60.1 # Last octet should be 1 rather than 0** <br>
      **subnet_mask: 24** <br>
 <br>
 <br>

This configuration creates an HA switching profile (required by PAS) <br>
If you don’t require the creation of this setting comment off from “-name” onwards <br>
**nsx_t_ha_switching_profile_spec: |** <br>
  **ha_switching_profiles:** <br>
  **- name: HASwitchingProfile** <br>
    **tags:** <br>
<br>
<br>

This configuration is for the IPAM IP blocks <br>
**nsx_t_container_ip_block_spec: |** <br>
  **container_ip_blocks:** <br>
  **- name: PAS-container-ip-block** <br>
    **cidr: 10.4.0.0/16** <br>
    **tags:** <br>
 **- name: PKS-node-ip-block** <br>
    **cidr: 11.4.0.0/16** <br>
  **- name: PKS-pod-ip-block** <br>
    **cidr: 12.4.0.0/16** <br>
<br>

The following configuration is for the IP pools. As seen in the example we created 2 SNAT/VIP pools for PKS and PAS. Also if additional TEP pool are required, you can create them here <br> 
**nsx_t_external_ip_pool_spec: |** <br>
  **external_ip_pools:**  <br>
  **- name: snat-vip-pool-for-pas**  <br>
    **cidr: 10.208.40.0/24**  <br>
    **start: 10.208.40.10 # Should not include gateway**  <br>
    **end: 10.208.40.200  # Should not include gateway** <br>
   
  **- name: snat-vip-pool-for-pks** <br>
    **cidr: 10.208.50.0/24** <br>
    **start: 10.208.50.10 # Should not include gateway** <br>
    **end: 10.208.50.200  # Should not include gateway** <br>
  <br>

NAT rules (can be pre-configured if IPs are known
**nsx_t_nat_rules_spec: |** <br>
  **nat_rules:** <br>
  **# Sample entry for allowing inbound to PAS Ops manager** <br>
  **- t0_router: DefaultT0Router** <br>
    **nat_type: dnat** <br>
    **destination_network: 10.208.40.2   # External IP address for PAS opsmanager** <br>
    **translated_network: 192.168.10.2     # Internal IP of PAS Ops manager** <br>
    **rule_priority: 1024                  # Higher priority** <br>
  
  **# Sample entry for allowing outbound from PAS Ops Mgr to external** <br>
  **- t0_router: DefaultT0Router** <br>
    **nat_type: snat** <br>
    **source_network: 192.168.10.2         # Internal IP of PAS opsmanager** <br>
    **translated_network: 10.208.40.2      # External IP address for PAS opsmanager** <br>
    **rule_priority: 1024                  # Higher priority** <br>
  
  **# Sample entry for PAS Infra network SNAT** <br>
  **- t0_router: DefaultT0Router** <br>
    **nat_type: snat** <br>
    **source_network: 192.168.10.0/24      # PAS Infra network cidr** <br>
    **translated_network: 10.208.40.3      # SNAT External Address for PAS networks** <br>
    **rule_priority: 8000                  # Lower priority** <br>

  **# Sample entry for PAS ERT network SNAT** <br>
  **- t0_router: DefaultT0Router** <br>
    **nat_type: snat** <br>
    **source_network: 192.168.20.0/24      # PAS ERT network cidr** <br>
    **translated_network: 10.208.40.3      # SNAT External Address for PAS networks** <br>
    **rule_priority: 8000                  # Lower priority** <br>

  **# Sample entry for PAS Services network SNAT** <br>
  **- t0_router: DefaultT0Router** <br>
    **nat_type: snat** <br>
    **source_network: 192.168.30.0/24      # PAS Services network cidr** <br>
    **translated_network: 10.208.40.3      # SNAT External Address for PAS networks** <br>
    **rule_priority: 8001                  # Lower priority** <br>

  
  **# Sample entry for PKS-Services network** <br>
  **- t0_router: DefaultT0Router** <br>
    **nat_type: snat** <br>
    **source_network: 192.168.60.0/24      # PKS Clusters network cidr** <br>
    **translated_network: 10.208.50.3      # SNAT External Address for PKS networks** <br>
    **rule_priority: 8001                  # Lower priority** <br>

  **# Sample entry for  PKS-Infra network** <br>
  **- t0_router: DefaultT0Router** <br>
    **nat_type: snat** <br>
    **source_network: 192.168.50.0/24      # PKS Infra network cidr** <br>
    **translated_network: 10.208.50.3      # SNAT External Address for PKS networks** <br>
    **rule_priority: 8001                  # Lower priority** <br>

  **# Sample entry for allowing inbound to PKS Ops manager** <br>
  **- t0_router: DefaultT0Router** <br>
    **nat_type: dnat** <br>
    **destination_network: 10.208.50.2     # External IP address for PKS opsmanager** <br>
    **translated_network: 192.168.50.2     # Internal IP of PKS Ops manager** <br>
    **rule_priority: 1024                  # Higher priority** <br>

  **# Sample entry for allowing outbound from PKS Ops Mgr to external** <br>
  **- t0_router: DefaultT0Router** <br>
    **nat_type: snat** <br>
    **source_network: 192.168.50.2        # Internal IP of PAS opsmanager** <br>
    **translated_network: 10.208.50.2      # External IP address for PAS opsmanager** <br>
    **rule_priority: 1024                  # Higher priority** <br>

  **# Sample entry for allowing inbound to PKS Controller** <br>
  **- t0_router: DefaultT0Router** <br>
    **nat_type: dnat** <br>
    **destination_network: 10.208.50.4     # External IP address for PKS opsmanager** <br>
    **translated_network: 192.168.60.2     # Internal IP of PKS Ops Controller** <br>
    **rule_priority: 1024                  # Higher priority** <br>

  **# Sample entry for allowing outbound from PKS Controller to external** <br>
  **- t0_router: DefaultT0Router** <br>
    **nat_type: snat** <br>
    **source_network: 192.168.60.2        # Internal IP of PKS controller** <br>
    **translated_network: 10.208.50.4      # External IP address for PKS controller** <br>
    **rule_priority: 1024                  # Higher priority** <br>

Here we specify the self-signed certificate config for NSX-T. <br>
**nsx_t_csr_request_spec: |**  <br>
  **csr_request:** <br>
    **#common_name not required - would use nsx_t_manager_host_name** <br>
    **org_name: Company            # EDIT** <br>
    **org_unit: net-integ          # EDIT** <br>
    **country: US                  # EDIT** <br>
    **state: CA                    # EDIT** <br>
    **city: SF                     # EDIT** <br>
    **key_size: 2048               # Valid values: 2048 or 3072** <br>
    **algorithm: RSA** <br>
 <br>

Load balancing config. Required only for PAS. If deploying PKS comment out from -name down 
**nsx_t_lbr_spec: |** <br>
  **loadbalancers:** <br>
  **# Sample entry for creating LBR for PAS ERT** <br>
  **- name: PAS-ERT-LBR** <br>
    **t1_router: T1-Router-PAS-ERT # Should match a previously declared T1 Router** <br>
    **size: small                  # Allowed sizes: small, medium, large** <br>
    **virtual_servers:** <br>
    **- name: goRouter443         # Name that signifies function being exposed**  <br>
      **vip: 10.208.40.4         # Exposed VIP for LBR to listen on** <br>
      **port: 443** <br>
      **members:** <br>
      **- ip: 192.168.20.11       # Internal ip of GoRouter instance 1** <br>
        **port: 443** <br>
    **- name: goRouter80** <br>
      **vip: 10.208.40.4**
      **port: 80**
      **members:**
      **- ip: 192.168.20.31       # Internal ip of GoRouter instance 1**
        **port: 80**
      **- ip: 192.168.20.32       # Internal ip of GoRouter instance 2**
        **port: 80**
    **- name: sshProxy            # SSH Proxy exposed to outside**
      **vip: 10.208.40.5**
      **port: 2222                # Port 2222 for ssh proxy**
      **members:**
      **- ip: 192.168.20.41       # Internal ip of Diego Brain where ssh proxy runs**
        **port: 2222**
 






   

