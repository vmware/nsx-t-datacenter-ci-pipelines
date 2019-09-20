#!/bin/bash

function create_manager_host {
  # Outer parenthesis converts string to an array
  nsx_manager_ips=($(echo "$nsx_manager_ips_int" | sed -e 's/,/ /g'))
  manager_ip=${nsx_manager_ips[0]}
  manager_hostname="${nsx_manager_hostname_prefix_int}-1"
  # The following need to be placed under [localhost:vars] section
  cat >> manager_host <<-EOF

nsx_manager_ip="$manager_ip"
nsx_manager_username="$nsx_manager_username_int"
nsx_manager_password="$nsx_manager_password_int"
nsx_manager_assigned_hostname="$manager_hostname"
nsx_manager_root_pwd="$nsx_manager_root_pwd_int"
nsx_manager_cli_pwd="$nsx_manager_cli_pwd_int"
nsx_manager_deployment_size="$nsx_manager_deployment_size_int"
EOF
}

function create_controller_hosts {
  nsx_manager_ips=($(echo "$nsx_manager_ips_int" | sed -e 's/,/ /g'))
  num_controllers=${#nsx_manager_ips[@]}
  if [[ $num_controllers -lt 2 ]]; then
    echo "No additional controller-manager specified."
    return
  fi

#  ip_mask_fields=($(echo "$netmask_int" | sed -e 's/\./ /g'))
#  prefix_length=0
#  for ip_mask_field in ${ip_mask_fields[*]}; do
#    prefix_length=$(( prefix_length + $(echo "obase=2;${ip_mask_field}" | bc | tr -cd '1' | wc -c) ))
#  done

  echo "[controllers]" > ctrl_vms
  for ((i=1;i<$num_controllers;++i)); do
    controller_ip=${nsx_manager_ips[i]}
    count=$((i+1))
    hostname="${nsx_manager_hostname_prefix_int}-${count}.${dns_domain_int}"
    controller_host="controller-${count} ip=${controller_ip} hostname=${hostname}"
    echo "$controller_host" >> ctrl_vms
  done

    cat >> ctrl_vms <<-EOF
[controllers:vars]
prefix_length="${nsx_manager_deployment_ip_prefix_length_int}"
default_gateway="${default_gateway_int}"
EOF

}

# TODO: update this with params from https://github.com/yasensim/nsxt-ansible/blob/master/answerfile.yml
function create_edge_hosts {
  echo "[edge_nodes]" > edge_vms
  edge_ips_int=($(echo "$edge_ips_int" | sed -e 's/,/ /g'))
  per_edge_params=("edge_deployment_size_int" "vc_datacenter_for_edge_int" "vc_cluster_for_edge_int" "vc_datastore_for_edge_int" "vc_uplink_network_for_edge_int" "vc_overlay_network_for_edge_int" "vc_management_network_for_edge_int")

  num_edges=${#edge_ips_int[@]}

  for ((i=0;i<$num_edges;++i)); do
    edge_ip=${edge_ips_int[i]}
    count=$((i+1))
    hostname="${edge_hostname_prefix_int}-${count}.${dns_domain_int}"
    edge_host="edge-${count} ip=$edge_ip hostname=${hostname} default_gateway=$edge_default_gateway_int prefix_length=$edge_ip_prefix_length_int transport_node_name=${edge_transport_node_prefix_int}-${count}"
    # for param in "${per_edge_params[@]}"; do
    #   # test if a single value is provided or a list is
    #   param_val=($(echo "${!param}" | sed -e 's/,/ /g'))
    #   if [[ ${#param_val[@]} -gt 1 && ${#param_val[@]} -eq ${#edge_ips_int[@]} ]]; then
    #     edge_host="${edge_host} ${param::-4}=${param_val[i]}"
    #   fi
    # done
    echo "$edge_host" >> edge_vms
  done

  cat >> edge_vms <<-EOF
[edge_nodes:vars]
edge_cli_password="$edge_cli_password_int"
edge_root_password="$edge_root_password_int"
EOF

  for param in "${per_edge_params[@]}"; do
    # param_val=($(echo "${!param}" | sed -e 's/,/ /g'))
    param_val="${!param}"
    # if [[ ${#param_val[@]} -eq 1 ]]; then
    echo "${param::-4}=${param_val}" >> edge_vms
    # fi
  done
}

function create_esx_hosts {
  count=1
  echo "[esx_hosts]" > esx_hosts
  for esx_ip in $(echo "$esx_ips_int" | sed -e 's/,/ /g')
  do
    hostname="${esx_hostname_prefix_int}-${count}.${dns_domain_int}"
    cat >> esx_hosts <<-EOF
esx-host-${count} ansible_host=$esx_ip ansible_user=root ansible_ssh_pass=$esx_root_password_int ip=$esx_ip fabric_node_name=esx-fabric-${count} transport_node_name=esx-transp-${count} hostname=${hostname}
EOF
    (( count++ ))
  done

  cat >> esx_hosts <<-EOF
[esx_hosts:vars]
esx_os_version=${esx_os_version_int}
EOF
}

function set_list_var_and_strip_whitespaces {
  list_var_value=${!1}
  if [[ $list_var_value == "" || $list_var_value == "null" ]]; then
    return
  fi
  list_var_value=$(echo $list_var_value | sed '
    s/^ *//     # remove leading whitespace
    s/ *$//     # remove trailing whitespace
    s/ *,/,/g   # remove whitespace before commas
    s/, */,/g   # remove whitespace after commas
    s/,/","/g   # put quotes around
    s/.*/["&"]/ # bracket & quotes around everything')
  echo "${1::-4}=$list_var_value" >> $2
}

function create_hosts {

# TODO: set nsx manager fqdn
export NSX_T_MANAGER_SHORT_HOSTNAME=$(echo "$NSX_T_MANAGER_FQDN" | awk -F '\.' '{print $1}')
#apt -qq install bc

cat > hosts <<-EOF
[localhost]
localhost       ansible_connection=local

[localhost:vars]
vcenter_ip="$vcenter_ip_int"
vcenter_username="$vcenter_username_int"
vcenter_password="$vcenter_password_int"
vcenter_datacenter="$vcenter_datacenter_int"
vcenter_cluster="$vcenter_cluster_int"
vcenter_datastore="$vcenter_datastore_int"
mgmt_portgroup="$mgmt_portgroup_int"

vc_datacenter_for_deployment="$vcenter_datacenter_int"
vc_cluster_for_deployment="$vcenter_cluster_int"
vc_datastore_for_deployment="$vcenter_datastore_int"
vc_management_network_for_deployment="$mgmt_portgroup_int"

dns_server="$dns_server_int"
dns_domain="$dns_domain_int"
ntp_servers="$ntp_servers_int"
default_gateway="$default_gateway_int"
netmask="$netmask_int"
nsx_image_webserver="$nsx_image_webserver_int"
ova_file_name="$ova_file_name_int"

compute_manager_username="$compute_manager_username_int"
compute_manager_password="$compute_manager_password_int"
edge_uplink_profile_vlan="$edge_uplink_profile_vlan_int"
esxi_uplink_profile_vlan="$esxi_uplink_profile_vlan_int"
vtep_ip_pool_cidr="$vtep_ip_pool_cidr_int"
vtep_ip_pool_gateway="$vtep_ip_pool_gateway_int"
vtep_ip_pool_start="$vtep_ip_pool_start_int"
vtep_ip_pool_end="$vtep_ip_pool_end_int"

tier0_router_name="$tier0_router_name_int"
tier0_uplink_port_ip="$tier0_uplink_port_ip_int"
tier0_uplink_port_subnet="$tier0_uplink_port_subnet_int"
tier0_uplink_next_hop_ip="$tier0_uplink_next_hop_ip_int"

resource_reservation_off="$resource_reservation_off_int"
nsx_manager_ssh_enabled="$nsx_manager_ssh_enabled_int"
unified_appliance="$unified_appliance_int"
EOF

  if [[ $unified_appliance_int == "true" ]]; then
    echo "nsx_manager_role=NSX Manager" >> hosts
  else
    echo "nsx_manager_role=nsx-manager" >> hosts
  fi

  create_manager_host
  cat manager_host >> hosts

  set_list_var_and_strip_whitespaces esx_available_vmnic_int hosts
  set_list_var_and_strip_whitespaces clusters_to_install_nsx_int hosts
  set_list_var_and_strip_whitespaces per_cluster_vlans_int hosts

  optional_params=("tier0_ha_vip_int" "tier0_uplink_port_ip_2_int" "compute_manager_2_username_int" "compute_manager_2_password_int" "compute_manager_2_vcenter_ip_int")
  for param in "${optional_params[@]}"; do
    param_val="${!param}"
    if [[ $param_val != "" && $param_val != "null" ]]; then
      echo "${param::-4}=${param_val}" >> hosts
    fi
  done

  create_edge_hosts
  create_controller_hosts

  if [[ -f ctrl_vms ]]; then
    cat ctrl_vms >> hosts
    echo "" >> hosts
    rm ctrl_vms
  fi
  cat edge_vms >> hosts

  rm manager_host edge_vms

  if [[ $esx_ips_int != ""  &&  $esx_ips_int != "null" ]]; then
    create_esx_hosts
    echo "" >> hosts
    cat esx_hosts >> hosts
    rm esx_hosts
  fi

}
