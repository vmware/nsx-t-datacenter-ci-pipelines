import os
import json
import sys
import argparse


def create_tenant_edge_params():
    dns_domain = os.getenv('dns_domain_int')
    edge_specs = os.getenv('tenant_edge_clusters_int')
    # default_edge_ips = os.getenv('edge_ips')
    # default_edge_prefix = os.getenv('edge_transport_node_prefix_int')
    # default_edge_uplink_profile_vlan = os.getenv('edge_uplink_profile_vlan_int')
    tenant_edge_clusters = json.loads(edge_specs)

    with open('tenant_edges', 'w') as edge_output_file:
        if len(tenant_edge_clusters) == 0:
            return
        for idx, edge_cluster in enumerate(tenant_edge_clusters):
            edge_output_file.write('\n[tenant_edge_cluster%s]\n' % idx)
            edge_ips = [e.strip() for e in edge_cluster['edge_ips'].split(',')]
            if len(edge_ips) < 1:
                print("Edge cluster %s has no edge member!" % idx)
                sys.exit(1)
            for i in range(len(edge_ips)):
                item_name = "%s-%s" % (edge_cluster['edge_hostname_prefix'], i+1)
                hostname = item_name + dns_domain
                transport_node_name = "%s-%s" % (edge_cluster['edge_transport_node_prefix'], i+1)
                edge_line = item_name + ' ip=' + edge_ips[i] + ' hostname=' + hostname
                edge_line += ' default_gateway=' + edge_cluster['edge_default_gateway']
                edge_line += ' prefix_length=' + str(edge_cluster['edge_ip_prefix_length'])
                edge_line += ' transport_node_name=' + transport_node_name
                edge_output_file.write(edge_line + '\n')

            edge_output_file.write('\n[tenant_edge_cluster%s:vars]\n' % idx)
            params_to_write = ['edge_cli_password',
                               'edge_root_password',
                               'edge_deployment_size',
                               'edge_uplink_profile_vlan',
                               'edge-uplink_profile_name',
                               'vc_datacenter_for_edge',
                               'vc_cluster_for_edge',
                               'vc_datastore_for_edge',
                               'vc_management_network_for_edge',
                               'vc_overlay_network_for_edge',
                               'vc_uplink_network_for_edge']
            for param in params_to_write:
                edge_output_file.write('%s=%s\n' % (param, edge_cluster[param]))

        cluster_member_spec = []
        # default_edge_count = len(default_edge_ips.split(','))
        # default_edge_members = "default-edge-cls members='["
        # for i in range(default_edge_count):
        #     default_edge_members += "{\"transport_node_name\":\"%s-%s\"}," \
        #                             % (default_edge_prefix, i + 1)
        # default_edge_members = default_edge_members[:-1] + "]'"
        # default_edge_members += " edge_uplink_profile_vlan=%s\n" % default_edge_uplink_profile_vlan
        # cluster_member_spec.append(default_edge_members)

        for idx, edge_cluster in enumerate(tenant_edge_clusters):
            members_line = "edge-cls-%s members='[" % (idx + 1)
            for i in range(len(edge_cluster['edge_ips'].split(','))):
                members_line += "{\"transport_node_name\":\"%s-%s\"}," \
                                % (edge_cluster['edge_transport_node_prefix'], i + 1)
            members_line = members_line[:-1] + "]'"
            members_line += " edge_uplink_profile_vlan=%s" % edge_cluster['edge_uplink_profile_vlan']
            members_line += " edge_uplink_profile_name=%s\n" % edge_cluster['edge_uplink_profile_name']
            cluster_member_spec.append(members_line)

        edge_output_file.write('\n')
        edge_output_file.write('\n[tenant_edge_cluster_members]\n')
        edge_output_file.writelines(cluster_member_spec)


def create_tenant_t0_params():
    t0_specs = os.getenv('tenant_t0s_int')
    tenant_t0s = json.loads(t0_specs)

    with open('tenant_t0s', 'w') as tenant_t0_ouput_file:
        tenant_t0_ouput_file.write('\n[tenant_t0s]\n')
        for idx, t0 in enumerate(tenant_t0s):
            t0_line = 'tenant-%s-t0 ' % idx
            params_to_write = ['tier0_router_name',
                               'uplink_port_ip',
                               'uplink_port_subnet',
                               'uplink_next_hop_ip',
                               'uplink_port_ip_2',
                               'ha_vip',
                               'edge_cluster',
                               'inter_tier0_network_ip',
                               'is_tanent',
                               'BGP_as_number']
            for param in params_to_write:
                t0_line += '%s=%s ' % (param, t0[param])
            tenant_t0_ouput_file.write(t0_line + '\n')


def create_cluster_spec():
    edge_specs = os.getenv('tenant_edge_clusters_int')
    tenant_edge_clusters = json.loads(edge_specs)

    with open('cluster_spec', 'w') as cluster_output_file:
        if len(tenant_edge_clusters) == 0:
            return
        cluster_spec = 'tenant_edge_clusters=['
        for idx, edge_cluster in enumerate(tenant_edge_clusters):
            cluster_spec += '\"{{groups[\'tenant_edge_cluster%s\']}}\",' % idx
        cluster_output_file.write(cluster_spec[:-1] + ']\n')


def get_args():
    parser = argparse.ArgumentParser(
        description='Arguments for which resources to create')

    parser.add_argument('-r', '--resource',
                        required=True,
                        default='edge_t0_spec',
                        action='store')

    args = parser.parse_args()
    return args


def main():
    args = get_args()
    if args.resource == 'edge_t0_spec':
        create_tenant_edge_params()
        create_tenant_t0_params()
    elif args.resource == 'cluster_spec':
        create_cluster_spec()


if __name__ == '__main__':
    main()
