# To run:
# python get_mo_ref_id.py --host 10.40.1.206 --user administrator@vsphere.local --password 'Admin!23'

from pyVmomi import vim

from pyVim.connect import SmartConnectNoSSL, Disconnect

import argparse
import atexit
import getpass
import json
import sys

import pdb

CLUSTER = 'cluster'
NETWORK = 'network'
DATASTORE = 'datastore'

HOST_ID_FIELDS = [
    'vc_datacenter_for_edge', 'vc_cluster_for_edge',
    'vc_datastore_for_edge', 'vc_uplink_network_for_edge',
    'vc_overlay_network_for_edge', 'vc_management_network_for_edge',
    'vc_datacenter_for_deployment', 'vc_cluster_for_deployment',
    'vc_datastore_for_deployment', 'vc_management_network_for_deployment'
]

class NoMoRefIdFoundError(Exception):
    pass

def get_args():
    parser = argparse.ArgumentParser(
        description='Arguments for talking to vCenter')

    parser.add_argument('-s', '--host',
                        required=True,
                        action='store',
                        help='vSpehre service to connect to')

    parser.add_argument('-o', '--port',
                        type=int,
                        default=443,
                        action='store',
                        help='Port to connect on')

    parser.add_argument('-u', '--user',
                        required=True,
                        action='store',
                        help='User name to use')

    parser.add_argument('-p', '--password',
                        required=True,
                        action='store',
                        help='Password to use')

    args = parser.parse_args()
    return args

class MoRefIdRetriever(object):

    def __init__(self):
        self.content = self._get_content()
        self.vim_resource_types = [vim.Datacenter,
                                   vim.Network, vim.Datastore]
        # stores {
        #     'network': {
        #         'VM network': <mo_id>
        #     }
        # }
        self.mapping = {}
        self.mo_id_set = set()
        self.vc_objects = self._get_container_view_for_datacenter()

    def _get_content(self):
        args = get_args()
        si = SmartConnectNoSSL(host=args.host, user=args.user,
                               pwd=args.password, port=args.port)
        if not si:
            print("Could not connect to the specified host using specified "
                  "username and password")
            return -1

        atexit.register(Disconnect, si)

        content = si.RetrieveContent()
        return content

    def parse_mo_ref_id_from_obj(self, vc_object):
        return str(vc_object).strip(" \"'").split(':')[1]

    def build_mapping_for_vc_obj_type(self, vc_object_list, mapping):
        for vc_object in vc_object_list:
            mo_id = self.parse_mo_ref_id_from_obj(vc_object)
            mapping[vc_object.name] = mo_id

    def _get_container_view_for_datacenter(self):
        # content = get_content()
        objview = self.content.viewManager.CreateContainerView(
            self.content.rootFolder, [vim.Datacenter], True)
        vc_objects = objview.view
        objview.Destroy()
        return vc_objects

    def build_mapping(self):
        for vc_object in self.vc_objects:
            try:
                # pdb.set_trace()
                datacenter_name = vc_object.name
                datacenter_mapping = {
                    CLUSTER: {},
                    NETWORK: {},
                    DATASTORE: {}
                }
                self.mapping[datacenter_name] = datacenter_mapping

                # get clusters
                clusters = vc_object.hostFolder.childEntity
                cluster_mapping = datacenter_mapping[CLUSTER]
                self.build_mapping_for_vc_obj_type(clusters, cluster_mapping)

                # get network
                networks = vc_object.network
                network_mapping = datacenter_mapping[NETWORK]
                self.build_mapping_for_vc_obj_type(networks, network_mapping)

                # storage
                datastores = vc_object.datastore
                datastore_mapping = datacenter_mapping[DATASTORE]
                self.build_mapping_for_vc_obj_type(datastores, datastore_mapping)

                # if vc_object.name not in mapping:
                #     mapping[vc_object.name] = mo_id
                #     self.mo_id_set.add(mo_id)
                # else:
                #     pass
            except Exception as e:
                print e
                print 'vc_object %s not written into cache' % vc_object.name

        from pprint import pprint
        print 'dumping cache:'
        pprint(self.mapping)

    def get_mo_id(self, vc_datacenter, vc_object_type, vc_object_name):
        if vc_object_name in self.mo_id_set:
            # if this is already a MoRefId
            return vc_object_name
        try:
            if 'folder' in vc_datacenter:
                vc_datacenter = vc_datacenter.split('/')[1]
            print 'trying to lookup %s %s %s' % (vc_datacenter, vc_object_type, vc_object_name)
            return self.mapping[vc_datacenter][vc_object_type][vc_object_name]
        except KeyError:
            print 'ERROR: no moRefId found for %s of type %s in datacenter %s' % (
                vc_object_name, vc_object_type, vc_datacenter)
            raise NoMoRefIdFoundError()


class HostsFileWriter(object):

    def __init__(self, mo_id_retriever, in_file, out_file):
        self.in_file = in_file
        self.out_file = out_file
        self.ids_to_replace = HOST_ID_FIELDS
        self.mo_id_retriever = mo_id_retriever
        self.current_datacenter = None

    def modify_line_if_matched(self, line):
        try:
            id_var_name = next(id_var_name for id_var_name in
                               self.ids_to_replace if id_var_name in line)
            print "found variable %s that needs to be converted to moRefId" % id_var_name
        except StopIteration:
            return line

        id_value = line.split('=')[-1].strip(" \"'")
        if id_var_name.startswith('vc_datacenter_'):
            self.current_datacenter = id_value
            print "found datacenter specified as %s" % id_value
            return

        vc_object_type = id_var_name.split('_')[-3]
        # pdb.set_trace()
        mo_id = self.mo_id_retriever.get_mo_id(self.current_datacenter, vc_object_type, id_value)
        new_line = '%s=%s' % (id_var_name, mo_id)
        return new_line

    def modify_ssh_enabled_if_matched(self, line):
        new_line = line
        if line and 'ssh_enabled' in line:
            value = line.split('=')[-1].strip(" \"'")
            var_name = line.split('=')[0]
            if value in ['true', 'false']:
                value = value[0].upper() + value[1:]
                new_line = '%s=%s' % (var_name, value)
        return new_line

    def process_hosts_file(self):
        lines = []
        with open(self.in_file, 'r') as f:
            for line in f:
                new_line = self.modify_line_if_matched(line.strip())
                new_line = self.modify_ssh_enabled_if_matched(new_line)
                if new_line:
                    lines.append('%s\n' % new_line)

        with open(self.out_file, 'w') as f:
            f.writelines(lines)


if __name__ == "__main__":
    mr = MoRefIdRetriever()
    mr.build_mapping()
    w = HostsFileWriter(mr, 'hosts', 'hosts.out')
    try:
        w. process_hosts_file()
    except NoMoRefIdFoundError:
        print 'One or more vcenter entity not found, exiting'
        sys.exit(1)
