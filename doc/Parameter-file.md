## Parameter file

The following are the sections of the parameter for the pipeline (if you are running it using the Docker image it will be placed in /home/concourse/nsx_pipeline_config.yml): <br>

### General: <br>

**nsx_t_pipeline_branch: master** <br>
Use 'master' for 2.5.0 and later deployments. <br>
DO NOT specify this parameter if using nsx-t-install docker image <br>
**nsxt_ansible_branch: dev** <br>
Use 'master' for 2.4.0 deployments. use 'v1.0.0' for earlier deployments. <br>
DO NOT specify this parameter if using nsx-t-install docker image <br>
**enable_ansible_debug: false** <br> 
set value to true for verbose output from Ansible

### NSX parameters: 

###### The following configuration is for the vCenter where the NSX Manager and controllers will be deployed <br>
_**vcenter_ip:**_  192.168.110.22                    <br>
_**vcenter_username:**_  administrator@corp.local    <br>
_**vcenter_password:**_  "VMware1!"                  <br>
_**vcenter_datacenter:**_  RegionA01                 <br>
_**vcenter_cluster:**_  RegionA01-MGMT      # management cluster <br>
_**vcenter_datastore:**_  iscsi   <br>

###### Configuration for the NSX manager networking 

_**mgmt_portgroup:**_ 'ESXi-RegionA01-vDS-COMP'     <br>
_**dns_server:**_ 192.168.110.10 <br>
_**dns_domain:**_ corp.local.io  <br>
_**ntp_servers:**_ time.vmware.com <br>
_**default_gateway:**_ 192.168.110.1 <br>
_**netmask:**_ 255.255.255.0 <br>

###### The nsx_image_webserver is where you placed the files. It can either be the auto-deployed nginx by the nsx-t-concourse docker image, or any other web server that you placed the files in. <br>
**nsx_image_webserver:** "http://192.168.110.11:40001"

###### Here you can specify the management components configuration. 
(Note – If resource_reservation_off: is set to false, in case the pipeline failed after deployment of the manager and controllers because of resource constraints the next run will remove the Memory reservations of these VMs. This is useful for lab purposes only)<br>
**nsx_manager_ips:** 192.168.110.33 <br>
**nsx_manager_username:** admin <br>
**nsx_manager_password:** Admin!23Admin # Min 8 chars, upper, lower, number, special digit <br>
**nsx_manager_hostname_prefix:** "nsxt-mgr" <br>
**[OPTIONAL] nsx_manager_root_pwd:** Admin!23Admin <br>
**[OPTIONAL] nsx_manager_cli_pwd:**  Admin!23Admin <br>
**nsx_manager_deployment_size:** small   # small, medium, large <br>
**nsx_manager_deployment_ip_prefix_length:** 23 <br>
**nsx_manager_ssh_enabled:** true <br>
**resource_reservation_off:** true <br>
**nsx_manager_ssh_enabled:** true <br>
**[OPTIONAL] nsx_manager_virtual_ip:** 192.168.110.36 <br>
**[OPTIONAL] nsx_manager_cluster_fqdn:** corp.local.io <br>
FQDN for the manager, will be used to generate cert for VIP. If VIP is set this field is required. <br>
**[OPTIONAL] nsx_license_key:** 12345-12345-12345-12345-12345
<br>

###### Compute manager config serves 2 purposes. For deploying the Edges using the NSX manager API and for auto installation of NSX on the vSphere clusters. The pipeline currently supports two vCenters in the pipeline. 

**compute_manager_username:**  "Administrator@corp.local"<br>
**compute_manager_password:**  "VMware1!" <br>
**[OPTIONAL] compute_manager_2_username:** admin<br>
**[OPTIONAL] compute_manager_2_vcenter_ip:** 192.168.110.99  <br>
**[OPTIONAL] compute_manager_2_password:** Admin!23Admin <br>

###### Do not configure the following parameters if you plan to use the cluster auto install. This section is used with per ESXi server/edge installation.  <br>
**edge_uplink_profile_vlan:** 0 <br>
For outbound uplink connection used by Edge, usually keep as 0 <br>
**esxi_uplink_profile_vlan:** 0  <br>
For internal overlay connection used by ESXi hosts, usually transport VLAN ID 

###### Configuration of the VTEP pool to be used by the ESXi servers and edges. <br>
**vtep_ip_pool_name:** tep-ip-pool <br>
**vtep_ip_pool_cidr:** 192.168.213.0/24 <br>
**vtep_ip_pool_gateway:** 192.168.213.1 <br>
**vtep_ip_pool_start:** 192.168.213.10 <br>
**vtep_ip_pool_end:** 192.168.213.200 <br>

###### Tier 0 configuration. Note only the HA VIP and static route is currently supported by the pipeline <br>
**tier0_router_name:** DefaultT0Router <br>
**tier0_uplink_port_ip:** 192.168.100.4 <br>
**tier0_uplink_port_subnet:** 24 <br>
**tier0_uplink_next_hop_ip:** 192.168.100.1 <br>
**tier0_uplink_port_ip_2:** 192.168.100.5 <br>
**tier0_ha_vip:** 192.168.100.3 <br>

###### Edge nodes 
**edge_ips:** 192.168.110.37, 192.168.110.38    
Comma separated based in number of required edges <br>
Note, if specifying more than 1 IP in edge_ips the pipeline will deploy multiple edges.<br>
**edge_default_gateway:** 192.168.110.1 <br>
**edge_ip_prefix_length:** 24 <br>
**edge_hostname_prefix:** nsx-t-edge <br>
**edge_fabric_name_prefix:** EdgeNode <br>
**edge_transport_node_prefix:** edge-transp-node<br>
**edge_cli_password:** "VMware1!" <br>
**edge_root_password:** "VMware1!" <br>
**edge_deployment_size:** "large"   
Large recommended for PKS deployments <br>
**vc_datacenter_for_edge:** RegionA01 <br>
**vc_cluster_for_edge:** RegionA01-MGMT <br>
**vc_datastore_for_edge:** iscsi <br>
**vc_uplink_network_for_edge:** "ESXi-RegionA01-vDS-COMP" <br>
**vc_overlay_network_for_edge:** "VM-RegionA01-vDS-COMP" <br>
**vc_management_network_for_edge:** "ESXi-RegionA01-vDS-COMP" <br>

###### This configuration is to install NSX on vSphere clusters automatically. Specify comma-separated list of clusters to install NSX on and the VLANs they will use. <br>
**clusters_to_install_nsx:** RegionA01-MGMT, RegionA01-K8s  #Comma separated <br>
**per_cluster_vlans:** 0, 0 <br>
Note – We yet to support multiple uplink profile assignment
<br>

###### Per ESX Installation, If you are not using the “auto cluster install” or if additional ESXi are needed, specify them here. Otherwise leave the "esx_ips" empty <br>
**[OPTIONAL] esx_ips:** <br>
**[OPTIONAL] esx_os_version:** "6.5.0" <br>
**[OPTIONAL] esx_root_password:** "VMware1!" <br>
**[OPTIONAL] esx_hostname_prefix:** "esx-host" <br>

###### Here specify which physical NICs will be claimed on the ESXi servers. Comma-separated list will work. Note that this applies to both auto installed clusters and individual ESXi hosts <br>
**esx_available_vmnic: "vmnic1"**<br>





Logical parameters 

##### The following sections of the parameter file can be customized for your deployment. You can set your configuration according to your requirements, whether PAS, PKS, VMs or anything else. The example below is for both PAS and PKS. As mentioned above, if using nsx-t-install docker image, simple delete the sections that does not apply to your deployment. For existing concourse servers, leave the parameter spec names. 
###### Tier-1 distributed routers and switches configuration  
```
nsx_t_t1router_logical_switches_spec: | 
  t1_routers: 
  # Add additional T1 Routers or collapse switches into same T1 Router as needed 
  # Remove unneeded T1 routers 
 
  - name: T1-Router-PAS-Infra 
    switches: 
    - name: PAS-Infra 
      logical_switch_gw: 192.168.10.1 # Last octet should be 1 rather than 0 
      subnet_mask: 24 
 
  - name: T1-Router-PAS-ERT 
    switches: 
    - name: PAS-ERT 
      logical_switch_gw: 192.168.20.1 # Last octet should be 1 rather than 0 
      subnet_mask: 24 
    edge_cluster: true 

  - name: T1-Router-PAS-Services 
    switches: 
    - name: PAS-Services 
      logical_switch_gw: 192.168.30.1 # Last octet should be 1 rather than 0 
      subnet_mask: 24 
 
  # Comment off the following T1 Routers if there is no PKS 
  - name: T1-Router-PKS-Infra 
    switches: 
    - name: PKS-Infra 
      logical_switch_gw: 192.168.50.1 # Last octet should be 1 rather than 0 
      subnet_mask: 24 
 
  - name: T1Router-PKS-Services 
    switches: 
    - name: PKS-Services 
      logical_switch_gw: 192.168.60.1 # Last octet should be 1 rather than 0 
      subnet_mask: 24 
```

###### This configuration creates an HA switching profile (required by PAS).  
```
nsx_t_ha_switching_profile_spec: | 
  ha_switching_profiles: 
  - name: HASwitchingProfile 
    tags: 
```

###### This configuration is for the IPAM IP blocks 
```
nsx_t_container_ip_block_spec: | 
  container_ip_blocks: 
  - name: PAS-container-ip-block 
    cidr: 10.4.0.0/16 
    tags: 
 - name: PKS-node-ip-block 
    cidr: 11.4.0.0/16 
  - name: PKS-pod-ip-block 
    cidr: 12.4.0.0/16 
```

###### The following configuration is for the IP pools. As seen in the example we created 2 SNAT/VIP pools for PKS and PAS. Also if additional TEP pool are required, you can create them here  
```
nsx_t_external_ip_pool_spec: | 
  external_ip_pools:  
  - name: snat-vip-pool-for-pas  
    cidr: 10.208.40.0/24  
    start: 10.208.40.10 # Should not include gateway  
    end: 10.208.40.200  # Should not include gateway 
   
  - name: snat-vip-pool-for-pks 
    cidr: 10.208.50.0/24 
    start: 10.208.50.10 # Should not include gateway 
    end: 10.208.50.200  # Should not include gateway 
```

###### NAT rules (can be pre-configured if IPs are known
```
nsx_t_nat_rules_spec: | 
  nat_rules: 
  # Sample entry for allowing inbound to PAS Ops manager 
  - t0_router: DefaultT0Router 
    nat_type: dnat 
    destination_network: 10.208.40.2   # External IP address for PAS opsmanager 
    translated_network: 192.168.10.2     # Internal IP of PAS Ops manager 
    rule_priority: 1024                  # Higher priority 
  
  # Sample entry for allowing outbound from PAS Ops Mgr to external 
  - t0_router: DefaultT0Router 
    nat_type: snat 
    source_network: 192.168.10.2         # Internal IP of PAS opsmanager 
    translated_network: 10.208.40.2      # External IP address for PAS opsmanager 
    rule_priority: 1024                  # Higher priority 
  
  # Sample entry for PAS Infra network SNAT 
  - t0_router: DefaultT0Router 
    nat_type: snat 
    source_network: 192.168.10.0/24      # PAS Infra network cidr 
    translated_network: 10.208.40.3      # SNAT External Address for PAS networks 
    rule_priority: 8000                  # Lower priority 

  # Sample entry for PAS ERT network SNAT 
  - t0_router: DefaultT0Router 
    nat_type: snat 
    source_network: 192.168.20.0/24      # PAS ERT network cidr 
    translated_network: 10.208.40.3      # SNAT External Address for PAS networks 
    rule_priority: 8000                  # Lower priority 

  # Sample entry for PAS Services network SNAT 
  - t0_router: DefaultT0Router 
    nat_type: snat 
    source_network: 192.168.30.0/24      # PAS Services network cidr 
    translated_network: 10.208.40.3      # SNAT External Address for PAS networks 
    rule_priority: 8001                  # Lower priority 

  
  # Sample entry for PKS-Services network 
  - t0_router: DefaultT0Router 
    nat_type: snat 
    source_network: 192.168.60.0/24      # PKS Clusters network cidr 
    translated_network: 10.208.50.3      # SNAT External Address for PKS networks 
    rule_priority: 8001                  # Lower priority 

  # Sample entry for  PKS-Infra network 
  - t0_router: DefaultT0Router 
    nat_type: snat 
    source_network: 192.168.50.0/24      # PKS Infra network cidr 
    translated_network: 10.208.50.3      # SNAT External Address for PKS networks 
    rule_priority: 8001                  # Lower priority 

  # Sample entry for allowing inbound to PKS Ops manager 
  - t0_router: DefaultT0Router 
    nat_type: dnat 
    destination_network: 10.208.50.2     # External IP address for PKS opsmanager 
    translated_network: 192.168.50.2     # Internal IP of PKS Ops manager 
    rule_priority: 1024                  # Higher priority 

  # Sample entry for allowing outbound from PKS Ops Mgr to external 
  - t0_router: DefaultT0Router 
    nat_type: snat 
    source_network: 192.168.50.2        # Internal IP of PAS opsmanager 
    translated_network: 10.208.50.2      # External IP address for PAS opsmanager 
    rule_priority: 1024                  # Higher priority 

  # Sample entry for allowing inbound to PKS Controller 
  - t0_router: DefaultT0Router 
    nat_type: dnat 
    destination_network: 10.208.50.4     # External IP address for PKS opsmanager 
    translated_network: 192.168.60.2     # Internal IP of PKS Ops Controller 
    rule_priority: 1024                  # Higher priority 

  # Sample entry for allowing outbound from PKS Controller to external 
  - t0_router: DefaultT0Router 
    nat_type: snat 
    source_network: 192.168.60.2        # Internal IP of PKS controller 
    translated_network: 10.208.50.4      # External IP address for PKS controller 
    rule_priority: 1024                  # Higher priority 
```

###### Specify the self-signed certificate config for NSX-T. 
```
nsx_t_csr_request_spec: |  
  csr_request: 
    #common_name not required - would use nsx_t_manager_host_name 
    org_name: Company            # EDIT 
    org_unit: net-integ          # EDIT 
    country: US                  # EDIT 
    state: CA                    # EDIT 
    city: SF                     # EDIT 
    key_size: 2048               # Valid values: 2048 or 3072 
    algorithm: RSA 
```

###### Load balancing config. Required only for PAS. If deploying PKS comment out from -name down 
```
nsx_t_lbr_spec: | 
  loadbalancers: 
  # Sample entry for creating LBR for PAS ERT 
  - name: PAS-ERT-LBR 
    t1_router: T1-Router-PAS-ERT # Should match a previously declared T1 Router 
    size: small                  # Allowed sizes: small, medium, large 
    virtual_servers: 
    - name: goRouter443         # Name that signifies function being exposed  
      vip: 10.208.40.4         # Exposed VIP for LBR to listen on 
      port: 443 
      members: 
      - ip: 192.168.20.11       # Internal ip of GoRouter instance 1 
        port: 443 
    - name: goRouter80 
      vip: 10.208.40.4
      port: 80
      members:
      - ip: 192.168.20.31       # Internal ip of GoRouter instance 1
        port: 80
      - ip: 192.168.20.32       # Internal ip of GoRouter instance 2
        port: 80
    - name: sshProxy            # SSH Proxy exposed to outside
      vip: 10.208.40.5
      port: 2222                # Port 2222 for ssh proxy
      members:
      - ip: 192.168.20.41       # Internal ip of Diego Brain where ssh proxy runs
        port: 2222
```
 






   

