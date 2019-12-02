import fileinput
import os

TOPOLOGY_FILE = "basic_topology.yml"
DNS_SERVER = "hostvars['localhost'].dns_server"
PREFIX_LENGTH = "hostvars[item].prefix_length"
DATA_NETWORKS = "data_networks:"
MANAGEMENT_NETWORK = "management_network: \"{{hostvars[item]"
COMPUTE = "compute: \"{{hostvars[item].vc_cluster_for_edge"
STORAGE = "storage: \"{{hostvars[item].vc_datastore_for_edge"


def add_dns_server_option():
    dns_servers_spec = os.getenv('dns_server_int')
    for line in fileinput.FileInput(TOPOLOGY_FILE, inplace=1):
        if DNS_SERVER in line and ',' in dns_servers_spec:
            leading_spaces = len(line) - len(line.lstrip())
            dns_line = ' ' * leading_spaces + "dns_server: %s\n" % dns_servers_spec.split(',')[0]
            line = line.replace(line, dns_line)
        elif PREFIX_LENGTH in line:
            leading_spaces = len(line) - len(line.lstrip()) - 2
            dns_line = ' ' * leading_spaces
            if ',' not in dns_servers_spec:
                dns_line += "dns_servers: [\"{{hostvars['localhost'].dns_server}}\"]"
            else:
                dns_servers = [s.strip() for s in dns_servers_spec.split(',')]
                dns_line += "dns_servers:"
                for server in dns_servers:
                    dns_line += '\n' + ' ' * leading_spaces + "- %s" % server
            line = line.replace(line, line + dns_line + '\n')
        print line,
        # For Python3 use following line instead
        # print(line, end='')


def add_ids_in_param_if_necessary():

    def add_id_to_param(matched_line):
        items = matched_line.split(' ')
        newline = items[0][:-1] + "_id: " + items[1]
        return newline

    ansible_branch = os.getenv('nsxt_ansible_branch_int').strip()
    if ansible_branch and ansible_branch == 'master':
        for line in fileinput.FileInput(TOPOLOGY_FILE, inplace=1):
            if "data_networks:" in line:
                leading_spaces = len(line) - len(line.lstrip())
                line_with_id = ' ' * leading_spaces + "data_network_ids:"
                line = line.replace(line, line_with_id)
            elif MANAGEMENT_NETWORK in line or COMPUTE in line or STORAGE in line:
                line_with_id = add_id_to_param(line)
                line = line.replace(line, line_with_id)
            print line,
            # For Python3 use following line instead
            # print(line, end='')


if __name__ == "__main__":
    add_dns_server_option()
    add_ids_in_param_if_necessary()
