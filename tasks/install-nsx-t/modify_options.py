from tempfile import mkstemp
from shutil import move, copymode
import os
from os import fdopen, remove

TOPOLOGY_FILE = "basic_topology.yml"
DNS_SERVER = "hostvars['localhost'].dns_server"
PREFIX_LENGTH = "hostvars[item].prefix_length"
DATA_NETWORKS = "data_networks:"
MANAGEMENT_NETWORK = "management_network: \"{{hostvars[item]"
COMPUTE = "compute: \"{{hostvars[item].vc_cluster_for_edge"
STORAGE = "storage: \"{{hostvars[item].vc_datastore_for_edge"
NODE_SETTINGS = "node_settings"

def add_new_line_if_absent(line):
    if line.endswith('\n'):
        return line
    return line + '\n'


def replace_file(tmp_file_path):
    # Copy the file permissions from the old file to the new file
    copymode(TOPOLOGY_FILE, tmp_file_path)
    # Remove original file
    remove(TOPOLOGY_FILE)
    # Move new file
    move(tmp_file_path, "basic_topology.yml")


def add_dns_server_option():
    dns_servers_spec = os.getenv('dns_server_int')
    fh, abs_path = mkstemp()
    with fdopen(fh, 'w') as new_file:
        with open(TOPOLOGY_FILE) as old_file:
            for line in old_file:
                if DNS_SERVER in line and ',' in dns_servers_spec:
                    leading_spaces = len(line) - len(line.lstrip())
                    dns_line = ' ' * leading_spaces + ("dns_server: %s\n"
                                                       % dns_servers_spec.split(',')[0])
                    line = line.replace(line, dns_line)
                elif NODE_SETTINGS in line:
                    leading_spaces = len(line) - len(line.lstrip()) + 2
                    dns_line = ' ' * leading_spaces

                    dns_servers = [s.strip() for s in dns_servers_spec.split(',')]
                    dns_line += "dns_servers:"
                    for server in dns_servers:
                        dns_line += '\n' + ' ' * leading_spaces + "- %s" % server
                    line = line.replace(line, line + dns_line)
                new_file.write(add_new_line_if_absent(line))
    replace_file(abs_path)


def add_ids_in_param_if_necessary():

    def add_id_to_param(matched_line):
        leading_spaces = len(line) - len(line.lstrip())
        items = matched_line.lstrip().split(' ')
        newline = ' ' * leading_spaces + items[0][:-1] + "_id: " + items[1]
        return newline

    ansible_branch = os.getenv('nsxt_ansible_branch_int').strip()
    if ansible_branch and ansible_branch == 'master':
        fh, abs_path = mkstemp()
        with fdopen(fh, 'w') as new_file:
            with open(TOPOLOGY_FILE) as old_file:
                for line in old_file:
                    if "data_networks:" in line:
                        leading_spaces = len(line) - len(line.lstrip())
                        line_with_id = ' ' * leading_spaces + "data_network_ids:"
                        line = line.replace(line, line_with_id)
                    elif MANAGEMENT_NETWORK in line or COMPUTE in line or STORAGE in line:
                        line = line.replace(line,  add_id_to_param(line))
                    new_file.write(add_new_line_if_absent(line))
        replace_file(abs_path)


if __name__ == "__main__":
    add_dns_server_option()
    add_ids_in_param_if_necessary()
