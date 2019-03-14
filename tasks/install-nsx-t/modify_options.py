import fileinput
import os

TOPOLOGY_FILE = "basic_topology.yml"


def add_dns_server_option():
    dns_servers_spec = os.getenv('dns_server_int')
    for line in fileinput.FileInput(TOPOLOGY_FILE, inplace=1):
        if "hostvars[item].prefix_length" in line:
            leading_spaces = len(line) - len(line.lstrip()) - 2
            dns_line = ' ' * leading_spaces
            if ',' not in dns_servers_spec:
                dns_line += "dns_servers: \"{{hostvars['localhost'].dns_server}}\""
            else:
                dns_servers = dns_servers_spec.split(', ')
                dns_line += "dns_servers:"
                for server in dns_servers:
                    dns_line += '\n' + ' ' * leading_spaces + "- %s" % server
            line = line.replace(line, line + dns_line + '\n')
        print line,
        # For Python3 use following line instead
        # print(line, end='')


if __name__ == "__main__":
    add_dns_server_option()
