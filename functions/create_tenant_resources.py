import os
import json
import sys
import argparse


def create_tenant_edge_params():
    dns_domain = os.getenv('dns_domain_int')
    edge_specs = os.getenv('tenant_edge_clusters_int')
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
                               'edge_uplink_profile_name',
                               'vc_datacenter_for_edge',
                               'vc_cluster_for_edge',
                               'vc_datastore_for_edge',
                               'vc_management_network_for_edge',
                               'vc_overlay_network_for_edge',
                               'vc_uplink_network_for_edge']
            for param in params_to_write:
                edge_output_file.write('%s=%s\n' % (param, edge_cluster[param]))

        cluster_member_spec = []
        for idx, edge_cluster in enumerate(tenant_edge_clusters):
            members_line = "edge-cls-%s members='[" % (idx + 1)
            for i in range(len(edge_cluster['edge_ips'].split(','))):
                members_line += "{\"transport_node_name\":\"%s-%s\"}," \
                                % (edge_cluster['edge_transport_node_prefix'], i + 1)
            members_line = members_line[:-1] + "]'"
            members_line += " edge_cluster_name=%s" % edge_cluster['edge_cluster_name']
            members_line += " edge_uplink_profile_vlan=%s" % edge_cluster['edge_uplink_profile_vlan']
            members_line += " edge_uplink_profile_name=%s\n" % edge_cluster['edge_uplink_profile_name']
            cluster_member_spec.append(members_line)

        edge_output_file.write('\n')
        edge_output_file.write('\n[tenant_edge_cluster_members]\n')
        edge_output_file.writelines(cluster_member_spec)


def create_tenant_t0_params():
    tenant_t0_specs = os.getenv('tenant_t0s_int')
    tenant_t0s = json.loads(tenant_t0_specs)
    shared_t0_params = ['tier0_router_name', 'edge_cluster_name', 'tier0_uplink_port_ip',
                        'tier0_uplink_port_subnet', 'tier0_uplink_next_hop_ip', 'vlan_logical_switch_name',
                        'tier0_uplink_port_ip_2', 'tier0_ha_vip', 'bgp_as_number',
                        'inter_tier0_network_ip', 'inter_tier0_network_ip_2']

    with open('t0s', 'w') as t0_ouput_file:
        t0_ouput_file.write('\n[tier0_routers]\n')
        shared_t0_line = 'shared-t0 '
        for param in shared_t0_params:
            shared_t0_line += '%s=%s ' % (param, os.getenv(param + '_int'))
        shared_t0_line += 'is_tanent=False'
        t0_ouput_file.write(shared_t0_line + '\n')

        params_to_write = shared_t0_params
        params_to_write.extend(['is_tanent'])
        for idx, t0 in enumerate(tenant_t0s):
            t0_line = 'tenant-%s-t0 ' % idx
            for param in params_to_write:
                t0_line += '%s=%s ' % (param, t0[param])
            t0_ouput_file.write(t0_line + '\n')


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
                        default='edge_spec',
                        action='store')

    args = parser.parse_args()
    return args


def main():
    args = get_args()
    if args.resource == 'edge_spec':
        create_tenant_edge_params()
    elif args.resource == 't0_spec':
        create_tenant_t0_params()
    elif args.resource == 'cluster_spec':
        create_cluster_spec()


if __name__ == '__main__':
    main()
