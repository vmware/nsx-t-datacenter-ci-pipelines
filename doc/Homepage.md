## Homepage

Welcome to the NSX-T Concourse CI Pipeline docs! <br>
This repository provides an easy-to-use automation framework that installs and configures NSX-T on vCenter clusters where PKS and/or PAS can be deployed.

### Concourse and NSX-T
Concourse is an Open source CI/CD pipeline tool used by many organizations around the world, especially Pivotal PAS customers use it not only to deliver software in an agile manner but also to perform Day1 and 2 ops on the CNA platform. Sponsored by Pivotal, Concourse is the CICD tool of choice for working with the PCF suite of products PAS, PKS and FAS.<br> 
NSX-T is the next-gen SDN from VMware built ground up for automation, it is supported by a growing number of automation tools that can be used to deploy and manage the platform. <br> The NSX-T Pipeline was created to allow our customers a simple way to deploy NSX-T end to end in a click of a button and to create a repeatable deployment process.<br>
- For more information about Concourse  check out the Concourse tutorial by Stark & Wayne and Pivotal’s Concourse page https://pivotal.io/Concourse <br>
- For more information about NSX-T see  https://blogs.vmware.com/networkvirtualization/2017/08/nsx-t-2-0.html/

__Demo on how to use the pipeline:__ <br>
[![Demo video](https://raw.githubusercontent.com/vmware/nsx-t-datacenter-ci-pipelines/Wiki-files/Wiki%20images/2018-10-22%2009_48_43-(261)%20How%20to%20deploy%20NSX-T%20Datacenter%20CI%20pipeline%20with%20Concourse%20-%20YouTube.jpg)](http://www.youtube.com/watch?v=wU6FW1eC5B8)
 <br>
 For more information on deployment process, go to the [Deployment page](Deployment.md)
 For more information on network prerequisites before running this pipeline, go to the [Network Prerequisites page](Network-prerequisites.md)
 <br>
 

### Pipeline configuration scope

This Concourse pipeline runs a set of tasks and jobs to deploy NSX-T, you can choose to run it on an existing concourse server or you can use the docker image which deploys everything for you including concourse server and the pipeline itself. <br> 
In the Git repository, we also provide a template parameter files to create all the necessary “plumbing” to run Pivotal PAS and PKS using the deployed NSX framework.<br>
This project is utilizing a set of Ansible scripts created by the VMware NSBU (can be found here: https://github.com/vmware/ansible-for-nsxt), the pipeline takes the config parameters defined by the user in the pipeline’s parameter file, and evokes the Ansible scripts accordingly and runs them. <br>
Anyone can use this pipeline, either as is or utilize its code to build for your own needs. The project is open-sourced so feel free to submit issues, feature requests, and contributions to the GIT repo. <br>
The pipeline achieves the following tasks:
- Deploys the VMware NSX-T Manager OVA image, Controller and Edge appliances are deployed using the manager API
- Configures the Controller cluster and register the controllers with NSX manager
- Configures host switches, uplink profiles, transport zones (VLAN and Overlay)
- Configure the Edges and ESXi Hosts as transport nodes
- Creates T0 Router (one per run, in HA VIP mode) with an uplink and static route
- Creates and configures T1 Routers with nested logical switches and ports (sample parameters file has a template for PKS and PAS)
- NAT Rules setup (sample parameters file has a template for PKS and PAS)
- Creates an IP Pools (usually used for the containers) and IP Blocks (usually used for routed IPs)
- Creates and sets up the load balancing
- Self-signed cert generation and registration against NSX-T Manager using FQDN 
- Sets NSX license key
- HA Spoofguard Switching Profile creation

### Unsupported configurations at the moment

The following capabilities are not supported in this version of the Pipeline and are planned for future releases. <br> 
* BGP – This pipeline yet to support BGP configuration and only supports static route deployment. If BGP is a requirement, deploy the pipeline with static route config and manually configure BGP.
* Multi-rack spine leaf configuration – If the edges and clusters are deployed in multiple racks with separate L3 domains the pipeline currently does not support attaching different VTEP uplink profiles to different clusters and edges. To fix after the pipeline is deployed create the additional VTEP pools and uplink profiles and assign them to the clusters
* Concourse is not supported on Redhat due to kernel compatibility. Use Ubuntu or equivalent. 


### Parameter file for the pipeline

Sample configuration parameters file can be found under the [sample_parameters](../sample_parameters) folder. <br>
__NOTE__: __If using the nsx-t-install docker image, you can safely delete all the parameters with [OPTIONAL] tags if those do not apply to your particular deployment.__ The pipeline will fill empty values for those parameters by default, or inferred values as stated in sample parameter files.
__If running the pipeline on existing concourse environment and not using the nsx-t-install image__, all the parameters need to be included, e.g. 'nsx_manager_virtual_ip' and 'nsx_manager_cluster_fqdn'. If you wish to leave those parameters unconfigured, leave the parameter stub empty:
```
...
nsx_manager_username: admin
nsx_manager_virtual_ip:     <-- Leave empty
nsx_manager_cluster_fqdn:   <-- Leave empty
...
nsx_t_lbr_spec:             <-- Leave empty
...
```
Do not delete those lines as Concourse needs to pick up those params even if they are not set.
For more information on the parameter file, go to the [Parameter file page](Parameter-file.md)



