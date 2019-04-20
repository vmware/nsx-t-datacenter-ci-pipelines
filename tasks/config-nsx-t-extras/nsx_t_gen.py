import argparse
import os
import json
import yaml
from pprint import pprint
from operator import itemgetter

import client

DEBUG = True

API_VERSION = '/api/v1'

EDGE_CLUSTERS_ENDPOINT       = '%s%s' % (API_VERSION, '/edge-clusters')
TRANSPORT_ZONES_ENDPOINT     = '%s%s' % (API_VERSION, '/transport-zones')
ROUTERS_ENDPOINT             = '%s%s' % (API_VERSION, '/logical-routers')
ROUTER_PORTS_ENDPOINT        = '%s%s' % (API_VERSION, '/logical-router-ports')
SWITCHES_ENDPOINT            = '%s%s' % (API_VERSION, '/logical-switches')
SWITCH_PORTS_ENDPOINT        = '%s%s' % (API_VERSION, '/logical-ports')
SWITCHING_PROFILE_ENDPOINT   = '%s%s' % (API_VERSION, '/switching-profiles')
IP_SET_ENDPOINT              = '%s%s' % (API_VERSION, '/ip-sets')
FIREWALL_SECTION_ENDPOINT    = '%s%s' % (API_VERSION, '/firewall/sections')
CONTAINER_IP_BLOCKS_ENDPOINT = '%s%s' % (API_VERSION, '/pools/ip-blocks')
EXTERNAL_IP_POOL_ENDPOINT    = '%s%s' % (API_VERSION, '/pools/ip-pools')
TRUST_MGMT_CSRS_ENDPOINT     = '%s%s' % (API_VERSION, '/trust-management/csrs')
TRUST_MGMT_CRLS_ENDPOINT     = '%s%s' % (API_VERSION, '/trust-management/crls')
TRUST_MGMT_SELF_SIGN_CERT    = '%s%s' % (API_VERSION, '/trust-management/csrs/')
TRUST_MGMT_UPDATE_CERT       = '%s%s' % (API_VERSION, '/node/services/http?action=apply_certificate')
LBR_SERVICES_ENDPOINT        = '%s%s' % (API_VERSION, '/loadbalancer/services')
LBR_VIRTUAL_SERVER_ENDPOINT  = '%s%s' % (API_VERSION, '/loadbalancer/virtual-servers')
LBR_POOLS_ENDPOINT           = '%s%s' % (API_VERSION, '/loadbalancer/pools')
LBR_MONITORS_ENDPOINT        = '%s%s' % (API_VERSION, '/loadbalancer/monitors')

LBR_APPLICATION_PROFILE_ENDPOINT = '%s%s' % (API_VERSION, '/loadbalancer/application-profiles')
LBR_PERSISTENCE_PROFILE_ENDPOINT = '%s%s' % (API_VERSION, '/loadbalancer/persistence-profiles')

global_id_map = {}
cache = {}
t0_facts = {}

TIER1          = 'TIER1'
TIER0          = 'TIER0'
IP_BLOCK       = 'IpBlock'
IP_POOL        = 'IpPool'
IP_SET         = 'IPSet'
IP_PREFIX      = 'IPPrefixList'
EDGE_CLUSTER   = 'EdgeCluster'
TZ             = 'TransportZone'
SP             = 'SpoofGuardSwitchingProfile'
ROUTER         = 'LogicalRouter'
ROUTER_PORT    = 'LogicalRouterPort'
LS             = 'LogicalSwitch'
LSP            = 'LogicalSwitchPort'


def init():
    nsx_mgr_ip   = os.getenv('nsx_manager_ips_int').split(',')[0].strip()
    nsx_mgr_user = os.getenv('nsx_manager_username_int', 'admin')
    nsx_mgr_pwd  = os.getenv('nsx_manager_password_int')

    nsx_mgr_context = {
        'admin_user': nsx_mgr_user,
        'url': 'https://' + nsx_mgr_ip,
        'admin_passwd': nsx_mgr_pwd
    }
    # TODO: the value of transport zone name is current static, and hidden from user.
    # see vars.yml
    global_id_map['DEFAULT_TRANSPORT_ZONE_NAME'] = 'overlay-tz'

    client.set_context(nsx_mgr_context)


##############################
# Utility functions
##############################

def print_global_ip_map():
    print '-----------------------------------------------'
    for key in global_id_map:
        print(" {} : {}".format(key, global_id_map[key]))
    print '-----------------------------------------------'


def nested_sort(item):
    if type(item) is dict:
        for k, v in item.items():
            item[k] = nested_sort(v)
        return item
    elif type(item) is list:
        item = sorted(item)
        item = [nested_sort(v) for v in item]
        return item
    return item


def deep_eq(v1, v2):
    return True if nested_sort(v1) == nested_sort(v2) else False


def load_ip_blocks():
    resp = client.get(CONTAINER_IP_BLOCKS_ENDPOINT)
    for result in resp.json()['results']:
        ip_block_name = result['display_name']
        ip_block_key = '%s:%s' % (IP_BLOCK, ip_block_name)
        global_id_map[ip_block_key] = result['id']
        cache[ip_block_key] = result


def load_ip_pools():
    resp = client.get(EXTERNAL_IP_POOL_ENDPOINT)
    for result in resp.json()['results']:
        ip_pool_name = result['display_name']
        ip_pool_key = '%s:%s' % (IP_POOL, ip_pool_name)
        global_id_map[ip_pool_key] = result['id']
        cache[ip_pool_key] = result


def load_edge_clusters():
    api_endpoint = EDGE_CLUSTERS_ENDPOINT
    resp = client.get(api_endpoint)
    for result in resp.json()['results']:
        edge_cluster_name = result['display_name']
        edge_cluster_id = result['id']
        key = '%s:%s' % (EDGE_CLUSTER, edge_cluster_name)
        global_id_map[key] = edge_cluster_id
        if global_id_map.get('DEFAULT_EDGE_CLUSTER_NAME') is None:
            global_id_map['DEFAULT_EDGE_CLUSTER_NAME'] = edge_cluster_name


def get_edge_cluster():
    edge_cluster_name = global_id_map.get('DEFAULT_EDGE_CLUSTER_NAME')
    if edge_cluster_name is None:
        load_edge_clusters()
    return global_id_map['DEFAULT_EDGE_CLUSTER_NAME']


def get_edge_cluster_id():
    default_edge_cluster_name = get_edge_cluster()
    key = '%s:%s' % (EDGE_CLUSTER, default_edge_cluster_name)
    return global_id_map[key]


def load_transport_zones():
    api_endpoint = TRANSPORT_ZONES_ENDPOINT

    resp = client.get(api_endpoint)
    for result in resp.json()['results']:
        transport_zone_name = result['display_name']
        transport_zone_id = result['id']
        key = '%s:%s' % (TZ, transport_zone_name)
        global_id_map[key] = transport_zone_id


def get_transport_zone():
    load_transport_zones()
    return global_id_map['DEFAULT_TRANSPORT_ZONE_NAME']


def get_transport_zone_id(transport_zone):
    default_transport_zone = get_transport_zone()
    key = '%s:%s' % (TZ, default_transport_zone)
    transport_zone_id = global_id_map.get(key)
    if transport_zone_id is None:
        return global_id_map[key]
    return transport_zone_id


def update_tag(api_endpoint, tag_map):
    tags = []
    resp = client.get(api_endpoint)
    updated_payload = resp.json()

    for key in tag_map:
        entry = {'scope': key, 'tag': tag_map[key]}
        tags.append(entry)
    updated_payload['tags'] = tags

    resp = client.put(api_endpoint, updated_payload)


def check_switching_profile(switching_profile_name):
    api_endpoint = SWITCHING_PROFILE_ENDPOINT

    resp = client.get(api_endpoint)

    switching_profile_id = None
    for result in resp.json()['results']:
        key = '%s:%s' % (SP, result['display_name'])
        global_id_map[key] = result['id']
        if result['display_name'] == switching_profile_name:
            switching_profile_id = result['id']

    return switching_profile_id


def build_router_key(router_type, router_name):
    return '{}:{}:{}'.format(ROUTER, router_type, router_name)


def load_logical_routers():
    api_endpoint = ROUTERS_ENDPOINT
    resp = client.get(api_endpoint)
    for result in resp.json()['results']:
        router_name = result['display_name']
        router_id = result['id']
        router_type = result['router_type']
        router_key = build_router_key(router_type, router_name)
        global_id_map[router_key] = router_id
        cache[router_key] = result


def check_logical_router(router_name):
    api_endpoint = ROUTERS_ENDPOINT

    resp = client.get(api_endpoint)

    logical_router_id = None
    for result in resp.json()['results']:
        router_key = build_router_key(result['router_type'], result['display_name'])
        global_id_map[router_key] = result['id']

        if result['display_name'] == router_name:
            logical_router_id = result['id']

    return logical_router_id


def check_logical_router_port(router_id):
    api_endpoint = ROUTER_PORTS_ENDPOINT

    resp = client.get(api_endpoint)

    logical_router_port_id = None
    for result in resp.json()['results']:
        key = '%s:%s' % (ROUTER_PORT, result['display_name'])
        global_id_map[key] = result['id']
        if result['logical_router_id'] == router_id:
            logical_router_port_id = result['id']

    return logical_router_port_id


def create_t0_logical_router(t0_router):
    api_endpoint = ROUTERS_ENDPOINT

    router_type = 'TIER0'
    edge_cluster_id = get_edge_cluster_id()

    router_name = t0_router['name']
    t0_router_id = check_logical_router(router_name)
    if t0_router_id is not None:
        return t0_router_id

    payload = {
        'resource_type': 'LogicalRouter',
        'description': "Logical router of type {}, created by nsx-t-gen!!".format(router_type),
        'display_name': router_name,
        'edge_cluster_id': edge_cluster_id,
        'router_type': router_type,
        'high_availability_mode': t0_router['ha_mode'],
    }
    resp = client.post(api_endpoint, payload)

    router_id = resp.json()['id']
    print("Created Logical Router '{}' of type '{}'".format(router_name, router_type))
    router_key = build_router_key(TIER0, router_name)
    global_id_map[router_key] = router_id
    return router_id


def create_t0_logical_router_and_port(t0_router):
    api_endpoint = ROUTER_PORTS_ENDPOINT
    router_name = t0_router['name']
    subnet = t0_router['subnet']

    router_id = create_t0_logical_router(router_name)
    logical_router_port_id = check_logical_router_port(router_id)
    if logical_router_port_id is not None:
        return router_id

    name = "LogicalRouterUplinkPortFor%s" % (router_name)
    descp = "Uplink Port created for %s router" % (router_name)
    target_display_name = "LogicalRouterUplinkFor%s" % (router_name)

    network = subnet.split('/')[0]
    cidr = subnet.split('/')[1]

    payload1 = {
        'resource_type': 'LogicalRouterUpLinkPort',
        'description': descp,
        'display_name': name,
        'logical_router_id': router_id,
        # 'edge_cluster_member_index' : [ t0_router['edge_index'] ],
        'subnets': [{
            'ip_addresses': [network],
            'prefix_length': cidr
        }]
    }

    resp = client.post(api_endpoint, payload1)
    target_id = resp.json()['id']

    print("Created Logical Router Uplink Port for T0Router: '{}'".format(router_name))
    logical_router_port_id = resp.json()['id']
    return router_id


def create_t1_logical_router(router_name, edge_cluster=False):
    api_endpoint = ROUTERS_ENDPOINT

    router_type = 'TIER1'

    t1_router_id = check_logical_router(router_name)
    if t1_router_id is not None:
        return t1_router_id

    payload = {
        'resource_type': 'LogicalRouter',
        'description': "Logical router of type {}, created by nsx-t-gen!!".format(router_type),
        'display_name': router_name,
        'router_type': router_type
    }

    if edge_cluster:
        payload['edge_cluster_id'] = get_edge_cluster_id()

    resp = client.post(api_endpoint, payload)

    router_id = resp.json()['id']
    router_key = build_router_key(TIER1, router_name)
    global_id_map[router_key] = router_id
    print("Created Logical Router '{}' of type '{}'".format(router_name, router_type))
    return router_id


def create_t1_logical_router_and_port(t0_router, t1_router):
    t1_router_name = t1_router['name']
    edge_cluster = True if t1_router.get('edge_cluster') in ['true', True] else False
    api_endpoint = ROUTER_PORTS_ENDPOINT

    t0_router_id = t0_router['id']
    t0_router_name = t0_router['display_name']
    t1_router_id = create_t1_logical_router(t1_router_name, edge_cluster=edge_cluster)

    name = "LogicalRouterLinkPortFrom%sTo%s" % (t0_router_name, t1_router_name)
    descp = "Port created on %s router for %s" % (t0_router_name, t1_router_name)
    target_display_name = "LinkedPort_%sTo%s" % (t0_router_name, t1_router_name)

    payload1 = {
        'resource_type': 'LogicalRouterLinkPortOnTIER0',
        'description': descp,
        'display_name': name,
        'logical_router_id': t0_router_id
    }

    resp = client.post(api_endpoint, payload1)
    target_id = resp.json()['id']

    name = "LogicalRouterLinkPortFrom%sTo%s" % (t1_router_name, t0_router_name)
    descp = "Port created on %s router for %s" % (t1_router_name, t0_router_name)
    target_display_name = "LinkedPort_%sTo%s" % (t1_router_name, t0_router_name)

    payload2 = {
        'resource_type': 'LogicalRouterLinkPortOnTIER1',
        'description': descp,
        'display_name': name,
        'logical_router_id': t1_router_id,
        'linked_logical_router_port_id': {
            'target_display_name': target_display_name,
            'target_type': 'LogicalRouterLinkPortOnTIER0',
            'target_id': target_id
        }
    }

    resp = client.post(api_endpoint, payload2)
    print(
        "Created Logical Router Port between T0Router: '{}' and T1Router: '{}'".format(t0_router_name, t1_router_name))
    logical_router_port_id = resp.json()['id']
    return t1_router_id


def enable_route_advertisement(router_id, advertise_lb_vip=False):
    route_adv = 'routing/advertisement'
    route_adv_endpoint = '%s/%s/%s' % (ROUTERS_ENDPOINT, router_id, route_adv)

    route_adv_resp = client.get(route_adv_endpoint).json()

    payload = {
        "enabled": True,
        "resource_type": "AdvertisementConfig",
        "advertise_nsx_connected_routes": True,
    }
    if advertise_lb_vip:
        payload['advertise_lb_vip'] = True

    route_adv_resp.update(payload)

    resp = client.put(route_adv_endpoint, route_adv_resp)
    adv_lb_vip_msg = 'and LB' if advertise_lb_vip else ''
    print("Enabled route advertisements {}on T1 Router: {}".format(adv_lb_vip_msg, router_id))
    # TODO: check response code


def check_logical_switch(logical_switch):
    api_endpoint = SWITCHES_ENDPOINT

    resp = client.get(api_endpoint)

    logical_switch_id = None
    for result in resp.json()['results']:
        key = '%s:%s' % (LS, result['display_name'])
        global_id_map[key] = result['id']
        if result['display_name'] == logical_switch:
            logical_switch_id = result['id']

    return logical_switch_id


def create_logical_switch(logical_switch_name):
    api_endpoint = SWITCHES_ENDPOINT
    transport_zone_id = get_transport_zone_id(None)

    payload = {'transport_zone_id': transport_zone_id,
               'display_name': logical_switch_name,
               'admin_state': 'UP',
               'replication_mode': 'MTEP'
               }

    resp = client.post(api_endpoint, payload)

    logical_switch_id = resp.json()['id']
    print("Created Logical Switch '{}'".format(logical_switch_name))
    key = '%s:%s' % (LS, logical_switch_name)
    global_id_map[key] = logical_switch_id
    return logical_switch_id


def create_logical_switch_port(logical_switch_name, logical_switch_id):
    api_endpoint = SWITCH_PORTS_ENDPOINT
    switch_port_name = logical_switch_name + 'RouterPortSwitchPort'

    payload = {
        'logical_switch_id': logical_switch_id,
        'display_name': switch_port_name,
        'admin_state': 'UP'
    }

    resp = client.post(api_endpoint, payload)

    logical_switch_port_id = resp.json()['id']
    key = '%s:%s' % (LSP, switch_port_name)
    global_id_map[key] = logical_switch_port_id

    return logical_switch_port_id


def associate_logical_switch_port(t1_router_name, logical_switch_name, subnet):
    api_endpoint = ROUTER_PORTS_ENDPOINT

    network = subnet.split('/')[0]
    cidr = subnet.split('/')[1]

    t1_router_id = check_logical_router(t1_router_name)
    logical_switch_id = check_logical_switch(logical_switch_name)
    logical_switch_port = create_logical_switch_port(logical_switch_name, logical_switch_id)

    name = logical_switch_name + 'RouterPort'
    switch_port_name = logical_switch_name + 'RouterPortSwitchPort'

    payload = {
        'resource_type': 'LogicalRouterDownLinkPort',
        'display_name': name,
        'logical_router_id': t1_router_id,
        'linked_logical_switch_port_id': {
            'target_display_name': switch_port_name,
            'target_type': 'LogicalPort',
            'target_id': logical_switch_port
        },
        'subnets': [{
            'ip_addresses': [network],
            'prefix_length': cidr
        }]
    }

    resp = client.post(api_endpoint, payload)

    logical_router_port_id = resp.json()['id']
    print("Created Logical Switch Port from Logical Switch {} with name: {} "
          + "to T1Router: {}".format(logical_switch_name, switch_port_name, t1_router_name))
    key = '%s:%s' % (ROUTER_PORT, name)
    global_id_map[key] = logical_router_port_id
    return logical_router_port_id


def create_container_ip_block(ip_block_name, cidr, tags):
    api_endpoint = CONTAINER_IP_BLOCKS_ENDPOINT

    payload = {
        'resource_type': 'IpBlock',
        'display_name': ip_block_name,
        'cidr': cidr
    }

    if tags:
        effective_tags = []
        for key in tags:
            entry = {
                'scope': key, 'tag': tags[key]
            }
            effective_tags.append(entry)
        payload['tags'] = effective_tags

    resp = client.post(api_endpoint, payload)

    ip_block_id = resp.json()['id']
    print("Created Container IP Block '{}' with cidr: {}".format(ip_block_name, cidr))

    ip_block_key = '%s:%s' % (IP_BLOCK, ip_block_name)
    global_id_map[ip_block_key] = ip_block_id
    cache[ip_block_key] = resp.json()
    return ip_block_id


def create_external_ip_pool(ip_pool_name, cidr, gateway, start_ip, end_ip, tags):
    api_endpoint = EXTERNAL_IP_POOL_ENDPOINT

    payload = {
        'resource_type': 'IpPool',
        'display_name': ip_pool_name,
        'subnets': [{
            'allocation_ranges': [{
                'start': start_ip,
                'end': end_ip
            }],
            'cidr': cidr,
            'gateway_ip': gateway,
            'dns_nameservers': []
        }],
    }

    if tags:
        effective_tags = []
        for key in tags:
            entry = {'scope': key, 'tag': tags[key]}
            effective_tags.append(entry)
        effective_tags.append({'scope': 'ncp/external', 'tag': 'true'})

        payload['tags'] = effective_tags

    resp = client.post(api_endpoint, payload)
    if not resp.ok:
        print "Error: IP pool not created for %s" % ip_pool_name
        print resp.json()
        return

    ip_pool_id = resp.json()['id']
    print("Created External IP Pool '{}' with cidr: {}, gateway: {}, start: {}, end: {}".format(ip_pool_name, cidr,
                                                                                                gateway, start_ip,
                                                                                                end_ip))
    ip_pool_key = '%s:%s' % (IP_POOL, ip_pool_name)
    global_id_map[ip_pool_key] = ip_pool_id
    cache[ip_pool_key] = resp.json()
    return ip_pool_id


def create_pas_tags():
    pas_tag_name = os.getenv('NSX_T_PAS_NCP_CLUSTER_TAG')
    if pas_tag_name is None:
        return {}

    pas_tags = {
        'ncp/cluster': pas_tag_name,
        'ncp/shared_resource': 'true'
    }
    return pas_tags


##############################
# IP sets / blocks / pools
##############################

def load_ip_sets():
    ip_sets = client.get(IP_SET_ENDPOINT).json()['results']
    for ip_set in ip_sets:
        key = '%s:%s' % (IP_SET, ip_set['display_name'])
        global_id_map[key] = ip_set['id']


def check_for_existing_ip_set(exisiting_ip_sets, new_ip_set):
    for exisiting_ip_set in exisiting_ip_sets:
        if exisiting_ip_set['display_name'] == new_ip_set['display_name']:
            if deep_eq(exisiting_ip_sets['ip_addresses'], new_ip_set['ip_addresses']):
                exisiting_ip_set.update({'stat': 'duplicate'})
                return exisiting_ip_set
            else:
                exisiting_ip_set.update({'stat': 'update'})
                return exisiting_ip_set
    return None


def create_ip_sets():
    ip_set_specs = os.getenv('nsx_t_ip_set_spec_int', '').strip()
    if ip_set_specs == '' or ip_set_specs == 'null':
        print('No yaml payload set for the NSX_T_IP_SET_SPEC!')
        return

    ip_sets = yaml.load(ip_set_specs)['ip_sets']
    if ip_sets is None or len(ip_sets) <= 0:
        print('No ip set entries in the NSX_T_IP_SET_SPEC, nothing to add/update!')
        return

    changes_detected = False
    api_endpoint = IP_SET_ENDPOINT
    existing_ip_sets = client.get(api_endpoint).json()['results']
    for ip_set in ip_sets:
        ip_set_payload = {
            'display_name': ip_set['display_name'],
            'ip_addresses': ip_set['ip_addresses']
        }
        existing_ip_set = check_for_existing_ip_set(existing_ip_sets, ip_set_payload)
        if not existing_ip_set:
            changes_detected = True
            print('Adding new set: {}'.format(ip_set_payload))
            client.post(api_endpoint, ip_set_payload)

        elif existing_ip_set['stat'] == 'update':
            changes_detected = True
            print('Updating IP set with name {}: {}'.format(ip_set_payload['display_name'], ip_set_payload))
            update_api_endpint = '%s%s%s' % (api_endpoint, '/', existing_ip_set['id'])
            ip_set_payload.update({'_revision:': existing_ip_set['_revision']})
            client.put(update_api_endpint, ip_set_payload)
        else:
            print('Same IP set already defined with name {}!'.format(existing_ip_set['display_name']))

    load_ip_sets()
    if changes_detected:
        print('Done adding/updating ip sets!!\n')
    else:
        print('Detected no change with ip sets!!\n')


def create_container_ip_blocks():
    ip_blocks_defn = os.getenv('nsx_t_container_ip_block_spec_int', '').strip()
    if ip_blocks_defn == '' or ip_blocks_defn == 'null':
        print('No yaml payload set for the nsx_t_container_ip_block_spec_int, ignoring Container IP Block section!')
        return

    ip_blocks = yaml.load(ip_blocks_defn)
    for ip_block in ip_blocks['container_ip_blocks']:
        ip_block_key = '%s:%s' % (IP_BLOCK, ip_block['name'])
        if ip_block_key in cache:
            print "IP block %s already exists, skip creation" % ip_block['name']
            continue
        create_container_ip_block(ip_block['name'], ip_block['cidr'], ip_block.get('tags'))


def create_external_ip_pools():
    ip_pools_defn = os.getenv('nsx_t_external_ip_pool_spec_int', '').strip()
    if ip_pools_defn == '' or ip_pools_defn == 'null':
        print('No yaml payload set for the NSX_T_EXTERNAL_IP_POOL_SPEC, ignoring External IP Pool section!')
        return

    ip_pools = yaml.load(ip_pools_defn)
    for ip_pool in ip_pools['external_ip_pools']:
        ip_pool_key = '%s:%s' % (IP_POOL, ip_pool['name'])
        if ip_pool_key in cache:
            print "IP pool %s already exists, skip creation" % ip_pool['name']
            continue
        create_external_ip_pool(
            ip_pool['name'], ip_pool['cidr'], ip_pool.get('gateway'),
            ip_pool['start'], ip_pool['end'], ip_pool.get('tags'))


def create_ha_switching_profile():
    ha_switching_profiles_defn = os.getenv('nsx_t_ha_switching_profile_spec_int', '').strip()
    if ha_switching_profiles_defn == '' or ha_switching_profiles_defn == 'null':
        print('No yaml payload set for the NSX_T_HA_SWITCHING_PROFILE_SPEC, ignoring HASpoofguard profile section!')
        return

    ha_switching_profiles = yaml.load(ha_switching_profiles_defn)['ha_switching_profiles']
    if ha_switching_profiles is None:
        print(
            'No valid yaml payload set for the NSX_T_HA_SWITCHING_PROFILE_SPEC, ignoring HASpoofguard profile section!')
        return

    api_endpoint = SWITCHING_PROFILE_ENDPOINT

    for ha_switching_profile in ha_switching_profiles:
        switching_profile_name = ha_switching_profile['name']
        switching_profile_id = check_switching_profile(ha_switching_profile['name'])
        if switching_profile_id is None:
            payload = {
                'resource_type': 'SpoofGuardSwitchingProfile',
                'description': 'Spoofguard switching profile for ncp-cluster-ha, created by nsx-t-gen!!',
                'display_name': switching_profile_name,
                'white_list_providers': ['LSWITCH_BINDINGS']
            }
            resp = client.post(api_endpoint, payload)
            switching_profile_id = resp.json()['id']
        key = '%s:%s' % (SP, switching_profile_name)
        global_id_map[key] = switching_profile_id
        switching_profile_tags = {
            'ncp/shared_resource': 'true',
            'ncp/ha': 'true'
        }
        update_tag(SWITCHING_PROFILE_ENDPOINT + '/' + switching_profile_id, switching_profile_tags)
    print('Done creating HASwitchingProfiles\n')


##############################
# Certificates
##############################

def list_certs():
    csr_request_spec = os.getenv('nsx_t_csr_request_spec_int', '').strip()
    if csr_request_spec == '' or csr_request_spec == 'null':
        return

    csr_request = yaml.load(csr_request_spec)['csr_request']

    api_endpoint = TRUST_MGMT_CSRS_ENDPOINT
    existing_csrs_response = client.get(api_endpoint).json()
    if existing_csrs_response['result_count'] > 0:
        for csr_entry in existing_csrs_response['results']:
            print('CSR Entry: {}'.format(csr_entry))
    print('Done listing CSRs\n')


def generate_self_signed_cert():
    nsx_t_manager_fqdn = '{}-1.{}'.format(
        os.getenv('nsx_manager_hostname_prefix_int'),
        os.getenv('dns_domain_int'))

    if nsx_t_manager_fqdn is None or nsx_t_manager_fqdn is '':
        print('Value not set for the NSX_T_MANAGER_HOST_NAME, cannot create self-signed cert')
        return

    csr_request_spec = os.getenv('nsx_t_csr_request_spec_int', '').strip()
    if csr_request_spec == '' or csr_request_spec == 'null':
        return

    csr_request = yaml.load(csr_request_spec)['csr_request']
    if csr_request is None:
        print('No valid yaml payload set for the NSX_T_CSR_REQUEST_SPEC, ignoring CSR self-signed cert section!')
        return

    api_endpoint = TRUST_MGMT_CSRS_ENDPOINT
    existing_csrs_response = client.get(api_endpoint).json()

    def does_comman_name_match(attr_list):
        for attr in attr_list:
            if attr.get('key') == 'CN' and attr.get('value') == nsx_t_manager_fqdn:
                return True
        return False

    for csr_resource in existing_csrs_response.get('results', []):
        attr_list = csr_resource.get('subject', {}).get('attributes', [])
        if does_comman_name_match(attr_list):
            print('CSR with NSX manager FQDN %s already exists' % nsx_t_manager_fqdn)
            return

    tokens = nsx_t_manager_fqdn.split('.')
    if len(tokens) < 3:
        raise Exception('Error!! CSR common name is not a full qualified domain name (provided as nsx mgr FQDN): {}!!'
                        .format(nsx_t_manager_fqdn))

    payload = {
        'subject': {
            'attributes': [
                {'key': 'CN', 'value': nsx_t_manager_fqdn},
                {'key': 'O', 'value': csr_request['org_name']},
                {'key': 'OU', 'value': csr_request['org_unit']},
                {'key': 'C', 'value': csr_request['country']},
                {'key': 'ST', 'value': csr_request['state']},
                {'key': 'L', 'value': csr_request['city']}
            ]
        },
        'key_size': csr_request['key_size'],
        'algorithm': csr_request['algorithm']
    }

    resp = client.post(api_endpoint, payload)
    csr_id = resp.json()['id']

    self_sign_cert_api_endpint = TRUST_MGMT_SELF_SIGN_CERT
    self_sign_cert_url = '%s%s%s' % (self_sign_cert_api_endpint, csr_id, '?action=self_sign')
    self_sign_csr_response = client.post(self_sign_cert_url, '').json()

    self_sign_csr_id = self_sign_csr_response['id']

    update_api_endpint = '%s%s%s' % (TRUST_MGMT_UPDATE_CERT, '&certificate_id=', self_sign_csr_id)
    update_csr_response = client.post(update_api_endpint, '')

    print('NSX Mgr updated to use newly generated CSR!!'
          + '\n    Update response code:{}'.format(update_csr_response.status_code))


##############################
# T0 Route redistribution
##############################

def set_t0_route_redistribution():
    for key in global_id_map:
        if key.startswith('%s:%s' % (ROUTER, TIER0)):
            t0_router_id = global_id_map[key]
            api_endpoint = '%s/%s/%s' % (ROUTERS_ENDPOINT, t0_router_id, 'routing/redistribution')

            cur_redistribution_resp = client.get(api_endpoint).json()
            payload = {
                'resource_type': 'RedistributionConfig',
                'logical_router_id': t0_router_id,
                'bgp_enabled': True,
                '_revision': cur_redistribution_resp['_revision']
            }
            client.put(api_endpoint, payload)
    print('Done enabling route redistribution for T0Routers\n')


def check_for_existing_redistribution_rules(existing_rules, new_rule):
    if len(existing_rules) == 0:
        return None
    rule_identifiers = ['display_name', 'destination', 'sources']
    ex_rules_filtered = []
    for ex_rule in existing_rules:
        ex_rules_filtered.append(dict((idf, ex_rule[idf])
                                      for idf in rule_identifiers
                                      if idf in ex_rule))
    if deep_eq(ex_rules_filtered, new_rule['rules']):
        return existing_rules
    return None


def add_redistribution_rules(rules, t0_router_id, t0_router_name):
    changes_detected = False
    api_endpoint = '%s/%s/%s' % (ROUTERS_ENDPOINT, t0_router_id, 'routing/redistribution/rules')
    existing_rules_spec = client.get(api_endpoint).json()
    rules_spec_revision = existing_rules_spec['_revision']
    for rule in rules:
        rule_payload = {
            '_revision': rules_spec_revision,
            'rules': [{
                'display_name': rule['rule_name'],
                'destination': 'BGP',
                'sources': rule['sources']
            }]
        }
        existing_rule = check_for_existing_redistribution_rules(existing_rules_spec['rules'], rule_payload)
        if existing_rule is None:
            changes_detected = True
            print('Adding new BGP redistribution rule for T0 router{}: {}'.format(t0_router_name, rule_payload))
            client.put(api_endpoint, rule_payload)
        else:
            print('BGP redistribution rule already up to date!')
    return changes_detected


##############################
# T0 NAT Rules
##############################

def print_t0_route_nat_rules():
    for key in global_id_map:
        if key.startswith('%s:%s' % (ROUTER, TIER0)):
            t0_router_id = global_id_map[key]
            api_endpoint = '%s/%s/%s' % (ROUTERS_ENDPOINT, t0_router_id, 'nat/rules')
            resp = client.get(api_endpoint).json()
            print('NAT Rules for T0 Router: {}\n{}'.format(t0_router_id, resp))


def reset_t0_route_nat_rules():
    for key in global_id_map:
        if key.startswith('%s:%s' % (ROUTER, TIER0)):
            t0_router_id = global_id_map[key]
            api_endpoint = '%s/%s/%s' % (ROUTERS_ENDPOINT, t0_router_id, 'nat/rules')
            resp = client.get(api_endpoint).json()
            nat_rules = resp['results']
            for nat_rule in nat_rules:
                delete_api_endpint = '%s%s%s' % (api_endpoint, '/', nat_rule['id'])
                resp = client.delete(delete_api_endpint)


def check_for_existing_rule(existing_nat_rules, new_nat_rule):
    if len(existing_nat_rules) == 0:
        return None

    for existing_nat_rule in existing_nat_rules:
        if (
                existing_nat_rule['translated_network'] == new_nat_rule['translated_network']
                and existing_nat_rule['action'] == new_nat_rule['action']
                and existing_nat_rule.get('match_destination_network') == new_nat_rule.get('match_destination_network')
                and existing_nat_rule.get('match_source_network') == new_nat_rule.get('match_source_network')
        ):
            return existing_nat_rule
    return None


def add_t0_route_nat_rules():
    nat_rules_defn = os.getenv('nsx_t_nat_rules_spec_int', '').strip()
    if nat_rules_defn == '' or nat_rules_defn == 'null':
        print('No yaml payload set for the NSX_T_NAT_RULES_SPEC, ignoring nat rules section!')
        return

    nat_rules_defns = yaml.load(nat_rules_defn)['nat_rules']
    if nat_rules_defns is None or len(nat_rules_defns) <= 0:
        print('No nat rule entries in the NSX_T_NAT_RULES_SPEC, nothing to add/update!')
        return

    changes_detected = False
    for nat_rule in nat_rules_defns:

        t0_router_id = global_id_map[build_router_key(TIER0, nat_rule['t0_router'])]
        if t0_router_id is None:
            raise Exception('Error!! No T0Router found with name: {}'.format(nat_rule['t0_router']))

        api_endpoint = '%s/%s/%s' % (ROUTERS_ENDPOINT, t0_router_id, 'nat/rules')
        existing_nat_rules = client.get(api_endpoint).json()['results']
        rule_payload = {
            'resource_type': 'NatRule',
            'enabled': True,
            'rule_priority': nat_rule['rule_priority'],
            'translated_network': nat_rule['translated_network']
        }

        if nat_rule['nat_type'] == 'dnat':
            rule_payload['action'] = 'DNAT'
            rule_payload['match_destination_network'] = nat_rule['destination_network']
        else:
            rule_payload['action'] = 'SNAT'
            rule_payload['match_source_network'] = nat_rule['source_network']

        existing_nat_rule = check_for_existing_rule(existing_nat_rules, rule_payload)
        if existing_nat_rule is None:
            changes_detected = True
            print('Adding new Nat rule: {}'.format(rule_payload))
            resp = client.post(api_endpoint, rule_payload)
        else:
            rule_payload['id'] = existing_nat_rule['id']
            rule_payload['display_name'] = existing_nat_rule['display_name']
            rule_payload['_revision'] = existing_nat_rule['_revision']
            if rule_payload['rule_priority'] != existing_nat_rule['rule_priority']:
                changes_detected = True
                print('Updating just the priority of existing nat rule: {}'.format(rule_payload))
                update_api_endpint = '%s%s%s' % (api_endpoint, '/', existing_nat_rule['id'])
                resp = client.put(update_api_endpint, rule_payload)

    if changes_detected:
        print('Done adding/updating nat rules for T0Routers!!\n')
    else:
        print('Detected no change with nat rules for T0Routers!!\n')


##############################
# IP prefix lists
##############################
def load_ip_prefixes():
    ip_prefix_dict = {}
    for display_name, uid in global_id_map.iteritems():
        if display_name.startswith(ROUTER):
            api_endpoint = '%s/%s/%s' % (ROUTERS_ENDPOINT, uid, 'routing/ip-prefix-lists')
            ip_prefix_lists = client.get(api_endpoint).json()['results']
            for prefix in ip_prefix_lists:
                key = '%s:%s' % (IP_PREFIX, prefix['display_name'])
                ip_prefix_dict[key] = prefix['id']
    global_id_map.update(ip_prefix_dict)


def check_for_existing_prefix(existing_ip_prefix_lists, new_ip_prefix_list):
    if len(existing_ip_prefix_lists) == 0:
        return None

    for existing_ip_prefix in existing_ip_prefix_lists:
        if deep_eq(existing_ip_prefix['prefixes'], new_ip_prefix_list['prefixes']):
            existing_ip_prefix.update({'stat': 'duplicate'})
            return existing_ip_prefix
        elif existing_ip_prefix['display_name'] == new_ip_prefix_list['display_name']:
            existing_ip_prefix.update({'stat': 'update'})
            return existing_ip_prefix
    return None


def add_ip_prefix_lists():
    ip_prefix_specs = os.getenv('nsx_t_ip_prefix_spec_int', '').strip()
    if ip_prefix_specs == '' or ip_prefix_specs == 'null':
        print('No yaml payload set for the NSX_T_IP_PREFIX_SPEC, ignoring bgp section!')
        return

    ip_prefix_lists = yaml.load(ip_prefix_specs)['ip_prefix_lists']
    if ip_prefix_lists is None or len(ip_prefix_lists) <= 0:
        print('No prefix list entries in the NSX_T_IP_PREFIX_SPEC, nothing to add/update!')
        return

    changes_detected = False
    for prefix_list in ip_prefix_lists:
        t0_router = prefix_list['t0_router']
        t0_router_id = global_id_map[build_router_key(TIER0, t0_router)]
        if t0_router_id is None:
            raise Exception('Error!! No T0Router found with name: {}'.format(t0_router))

        api_endpoint = '%s/%s/%s' % (ROUTERS_ENDPOINT, t0_router_id, 'routing/ip-prefix-lists')
        existing_ip_prefix_lists = client.get(api_endpoint).json()['results']
        payload = {
            'resource_type': 'IPPrefixList',
            'display_name': prefix_list['display_name'],
            'prefixes': prefix_list['prefixes']
        }
        existing_ip_prefix = check_for_existing_prefix(existing_ip_prefix_lists, payload)
        if existing_ip_prefix is None:
            changes_detected = True
            print('Adding new IP prefix list: {}'.format(payload))
            client.post(api_endpoint, payload)

        elif existing_ip_prefix['stat'] == 'update':
            changes_detected = True
            print('Updating IP prefix list with name {}: {}'.format(payload['display_name'], payload))
            update_api_endpint = '%s%s%s' % (api_endpoint, '/', existing_ip_prefix['id'])
            payload.update({'_revision:': existing_ip_prefix['_revision']})
            client.put(update_api_endpint, payload)
        else:
            print('Same IP prefix lists already defined with name {}!'.format(existing_ip_prefix['display_name']))
    if changes_detected:
        print('Done adding/updating ip prefix lists for T0Routers!!\n')
    else:
        print('Detected no change with ip prefix lists for T0Routers!!\n')


##############################
# BGP configs
##############################

def construct_t0_facts():
    shared_t0_name = os.getenv('tier0_router_name_int', '')
    shared_t0_as_num = os.getenv('bgp_as_number_int', '')
    shared_t0_inter_network_addr = os.getenv('inter_tier0_network_ip_int', '')
    shared_t0_inter_network_addr2 = os.getenv('inter_tier0_network_ip_2_int', '')
    t0_facts.update({shared_t0_name: {'as_num': shared_t0_as_num,
                                      'inter_t0_addr': shared_t0_inter_network_addr,
                                      'inter_t0_addr2': shared_t0_inter_network_addr2}})

    tanent_t0_specs = os.getenv('tenant_t0s_int')
    tenant_t0s = yaml.load(tanent_t0_specs)
    if len(tenant_t0s) > 0:
        for t0 in tenant_t0s:
            t0_facts.update({
                t0['tier0_router_name']:
                    {'as_num': t0['bgp_as_number'],
                     'inter_t0_addr': t0['inter_tier0_network_ip'],
                     'inter_t0_addr2': t0['inter_tier0_network_ip_2']}})


def check_for_existing_bgp_configs(existing_bgp_config, new_bgp_config):
    if existing_bgp_config['display_name'] == new_bgp_config['display_name']:
        if str(existing_bgp_config['as_num']) == str(new_bgp_config['as_num']):
            return existing_bgp_config
    return None


def check_for_existing_bgp_communities(existing_community_lists, new_community_list):
    if len(existing_community_lists) == 0:
        return None
    for existing_community_list in existing_community_lists:
        if existing_community_list['display_name'] == new_community_list['display_name']:
            return existing_community_list
    return None


def add_bgp_community_list_configs(community_lists, t0_router_id, t0_router_name):
    changes_detected = False
    api_endpoint = '%s/%s/%s' % (ROUTERS_ENDPOINT, t0_router_id, 'routing/bgp/community-lists')
    existing_community_lists = client.get(api_endpoint).json()['results']
    for community_list in community_lists:
        payload = {
            'display_name': community_list['display_name'],
            'community_type': 'NormalBGPCommunity',
            'communities': community_list['communities']
        }
        existing_community_list = check_for_existing_bgp_communities(existing_community_lists, payload)
        if existing_community_list is None:
            changes_detected = True
            print('Adding new BGP community list for T0 router{}: {}'.format(t0_router_name, payload))
            client.post(api_endpoint, payload)
        else:
            if deep_eq(existing_community_list['communities'], payload['communities']):
                changes_detected = True
                print('Updating BGP community list for T0 router{}: {}'.format(t0_router_name, payload))
                payload.update({'_revision': existing_community_list['_revision']})
                client.put(api_endpoint, payload)
    return changes_detected


def add_filter_options(config, neighbor):
    out_prefix_id = None
    in_prefix_id = None
    prefix_detected = False

    load_ip_prefixes()
    if 'out_filter_ip_prefix' in config:
        global_map_name = '%s:%s' % (IP_PREFIX, config['out_filter_ip_prefix'])
        if global_map_name in global_id_map:
            prefix_detected = True
            out_prefix_id = global_id_map[global_map_name]
        else:
            raise Exception('Error!! No ip prefix list found with name: {}'.format(config['out_filter_ip_prefix']))
    if 'in_filter_ip_prefix' in config:
        global_map_name = '%s:%s' % (IP_PREFIX, config['in_filter_ip_prefix'])
        if global_map_name in global_id_map:
            prefix_detected = True
            in_prefix_id = global_id_map[global_map_name]
        else:
            raise Exception('Error!! No ip prefix list found with name: {}'.format(config['in_filter_ip_prefix']))
    if prefix_detected:
        neighbor.update({'address_families': [{'type': 'IPV4_UNICAST', 'enabled': True}]})
        if out_prefix_id:
            neighbor['address_families'][0].update({'out_filter_ipprefixlist_id': out_prefix_id})
        if in_prefix_id:
            neighbor['address_families'][0].update({'in_filter_ipprefixlist_id': in_prefix_id})


def parse_bgp_neighbor(config):
    if config['type'] == 't0_router':
        t0_router = config['t0_router_name']
        if t0_router in t0_facts:
            neighbor = {'display_name': t0_router,
                        'neighbor_address': t0_facts[t0_router]['inter_t0_addr'],
                        'remote_as_num': t0_facts[t0_router]['as_num']}
            add_filter_options(config, neighbor)
            addr_2 = t0_facts[t0_router]['inter_t0_addr2']
            if addr_2 is not None and addr_2 != "null":
                neighbor2 = {'display_name': t0_router + '_ha',
                             'neighbor_address': addr_2,
                             'remote_as_num': t0_facts[t0_router]['as_num']}
                add_filter_options(config, neighbor2)
                return [neighbor, neighbor2]
            else:
                return [neighbor]
        else:
            raise Exception('Error!! No T0Router found with name: {}'.format(t0_router))
    elif config['type'] == 'address':
        neighbor = config.pop('type')
        return [neighbor]


def check_for_existing_bgp_neighbors(existing_neighbors, new_neighbor):
    if len(existing_neighbors) == 0:
        return None
    for existing_neighbor in existing_neighbors:
        if existing_neighbor['neighbor_address'] == new_neighbor['neighbor_address']:
            return existing_neighbor
    return None


def add_bgp_neighbors(neighbors, t0_router_id, t0_router_name):
    changes_detected = False
    api_endpoint = '%s/%s/%s' % (ROUTERS_ENDPOINT, t0_router_id, 'routing/bgp/neighbors')
    existing_neighbors = client.get(api_endpoint).json()['results']
    for neighbor in neighbors:
        neighbor_payloads = parse_bgp_neighbor(neighbor)
        for neighbor_payload in neighbor_payloads:
            existing_neighbor = check_for_existing_bgp_neighbors(existing_neighbors, neighbor_payload)
            if existing_neighbor is None:
                changes_detected = True
                print('Adding new BGP neighbor for T0 router{}: {}'.format(t0_router_name, neighbor_payload))
                client.post(api_endpoint, neighbor_payload)
            else:
                if not deep_eq(existing_neighbor.get('address_families'),
                               neighbor_payload.get('address_families')):
                    changes_detected = True
                    neighbor_payload.update({'_revision': existing_neighbor['_revision']})
                    print('Updating BGP neighbor for T0 router{}: {}'.format(t0_router_name, neighbor_payload))
                    api_endpoint += '/%s' % existing_neighbor['id']
                    client.put(api_endpoint, neighbor_payload)
    if not changes_detected:
        print("No changes detected for BGP neighbor configs!")
    return changes_detected


def add_bgp_configs():
    bgp_specs = os.getenv('nsx_t_t0_bgp_spec_int', '').strip()
    if bgp_specs == '' or bgp_specs == 'null':
        print('No yaml payload set for the NSX_T_BGP_SPEC, ignoring bgp section!')
        return

    bgp_configs = yaml.load(bgp_specs)['bgp_configs']
    if bgp_configs is None or len(bgp_configs) <= 0:
        print('No BGP config entries in the NSX_T_BGP_SPEC, nothing to add/update!')
        return

    construct_t0_facts()
    changes_detected = False
    for bgp_config in bgp_configs:
        if bgp_config['t0_router'] in t0_facts:
            t0_router_id = global_id_map[build_router_key(TIER0, bgp_config['t0_router'])]
            if t0_router_id is None:
                raise Exception('Error!! No T0Router found with name: {}'.format(bgp_config['t0_router']))

            api_endpoint = '%s/%s/%s' % (ROUTERS_ENDPOINT, t0_router_id, 'routing/bgp')
            current_bgp_config = client.get(api_endpoint).json()
            bgp_payload = {
                'resource_type': 'BgpConfig',
                'enabled': True,
                'description': '%s, created by nsx-t-gen!' % bgp_config['display_name'],
                'display_name': bgp_config['display_name'],
                'as_num': t0_facts[bgp_config['t0_router']]['as_num'],
                '_revision': current_bgp_config['_revision']
            }

            existing_bgp_config = check_for_existing_bgp_configs(current_bgp_config, bgp_payload)
            if existing_bgp_config is None:
                changes_detected = True
                print('Updating BGP config for T0 router{}: {}'.format(bgp_config['t0_router'], bgp_payload))
                client.put(api_endpoint, bgp_payload)

            if 'community_lists' in bgp_config:
                community_list_updated = add_bgp_community_list_configs(bgp_config['community_lists'],
                                                                        t0_router_id, bgp_config['t0_router'])
                changes_detected = True if community_list_updated else changes_detected

            if 'neighbors' in bgp_config:
                neighbor_updated = add_bgp_neighbors(bgp_config['neighbors'],
                                                     t0_router_id, bgp_config['t0_router'])
                changes_detected = True if neighbor_updated else changes_detected

            if 'redistribution_configs' in bgp_config:
                redistribution_updated = add_redistribution_rules(bgp_config['redistribution_configs'],
                                                                  t0_router_id, bgp_config['t0_router'])
                changes_detected = True if redistribution_updated else changes_detected
        else:
            print("Detected t0 routers that are not specified in previous sections! skipping BGP setup for this router")
    if changes_detected:
        print('Done adding/updating BGP configs for T0Routers!!\n')
    else:
        print('Detected no change with BGP configs for T0Routers!!\n')


##############################
# Edge firewall rules
##############################

def check_existing_firewall_sections(existing_sections, new_section):
    if len(existing_sections) == 0:
        return None
    for existing_section in existing_sections:
        if existing_section['display_name'] == new_section['display_name']:
            section_update, rule_update = False, False
            if (
                    existing_section['section_type'] != new_section['section_type'] or
                    existing_section['stateful'] != new_section['stateful'] or
                    not deep_eq(existing_section.get('applied_tos'), new_section.get('applied_tos'))
            ):
                section_update = True
            if 'rules' in new_section:
                api_endpoint = '%s/%s/%s' % (FIREWALL_SECTION_ENDPOINT, existing_section['id'], 'rules')
                existing_rules = client.get(api_endpoint).json()['results']
                rule_identifiers = ['display_name', 'action', 'direction', 'sources', 'destinations']
                ex_rules_filtered = []
                for ex_rule in existing_rules:
                    ex_rules_filtered.append(dict((idf, ex_rule[idf])
                                                  for idf in rule_identifiers
                                                  if idf in ex_rule))
                if not deep_eq(ex_rules_filtered, new_section['rules']):
                    rule_update = True
            existing_section.update({'section_update': section_update, 'rule_update': rule_update})
            return existing_section
    return None


def add_firewall_sections_and_rules():

    def add_id_to_resources(resources):
        resource_list_with_id = []
        for resource in resources:
            key = '%s:%s' % (resource['target_type'], resource['target_display_name'])
            if key in global_id_map:
                resource.update({'target_id': global_id_map[key], 'is_valid': True})
                resource_list_with_id.append(resource)
            else:
                raise Exception('No %s of name %s found!' % (resource['target_type'], resource['target_display_name']))
        return resource_list_with_id

    def construct_rule_payload(spec):
        rule_payload = {
            'display_name': spec['display_name'],
            'action': spec['action'],
            'direction': spec['direction']
        }
        if 'sources' in spec:
            rule_payload.update({
                'sources': add_id_to_resources(spec['sources'])
            })
        if 'destinations' in spec:
            rule_payload.update({
                'destinations': add_id_to_resources(spec['destinations'])
            })
        return rule_payload

    firewall_section_specs = os.getenv('nsx_t_firewall_sections_spec_int', '').strip()
    if firewall_section_specs == '' or firewall_section_specs == 'null':
        print('No yaml payload set for the NSX_T_FIREWALL_SECTION_SPEC, ignoring firewall sections!')
        return

    firewall_sections = yaml.load(firewall_section_specs)['firewall_sections']
    if firewall_sections is None or len(firewall_sections) == 0:
        print('No firewall section config entries in NSX_T_FIREWALL_SECTION_SPEC, nothing to add/update!')
        return

    changes_detected = False
    for firewall_section in firewall_sections:
        api_endpoint = FIREWALL_SECTION_ENDPOINT
        existing_sections = client.get(api_endpoint).json()['results']
        payload = {
            'display_name': firewall_section['display_name'],
            'section_type': firewall_section['section_type'],
            'stateful': firewall_section['stateful']
        }
        if 'applied_tos' in firewall_section:
            resource_list = add_id_to_resources(firewall_section['applied_tos'])
            payload.update({'applied_tos': resource_list})

        if 'rules' in firewall_section:
            api_endpoint = '%s%s' % (FIREWALL_SECTION_ENDPOINT, '?action=create_with_rules')

            firewall_rule_specs = os.getenv('nsx_t_edge_firewall_rules_spec_int', '').strip()
            if firewall_rule_specs == '' or firewall_section_specs == 'null':
                raise Exception('Rules need to be created in nsx_t_edge_firewall_rules_spec section!')

            firewall_rules = yaml.load(firewall_rule_specs)['edge_firewall_rules']
            if firewall_rules is None or len(firewall_rules) == 0:
                raise Exception('Rules need to be created in nsx_t_edge_firewall_rules_spec section!')

            rules_payload = []
            for firewall_rule_name in firewall_section['rules']:
                rule_spec = next((rule for rule in firewall_rules
                                  if rule['display_name'] == firewall_rule_name), None)
                if rule_spec is None:
                    raise Exception('No rule with name %s is defined!' % firewall_rule_name)
                rules_payload.append(construct_rule_payload(rule_spec))
            payload.update({'rules': rules_payload})

        existing_section = check_existing_firewall_sections(existing_sections, payload)
        if existing_section is None:
            changes_detected = True
            print('Adding new firewall section {}'.format(payload))
            client.post(api_endpoint, payload)
        else:
            if existing_section['section_update']:
                changes_detected = True
                print('Updating the firewall section {} itself'.format(existing_section['display_name']))
                api_endpoint = '%s/%s' % (FIREWALL_SECTION_ENDPOINT, existing_section['id'])
                payload.update({'_revision': existing_section['_revision']})
                client.put(api_endpoint, payload)
            if existing_section['rule_update']:
                changes_detected = True
                print('Updating the rules of firewall section {}: {}'
                      .format(existing_section['display_name'], payload['rules']))
                api_endpoint = '%s/%s%s' % (FIREWALL_SECTION_ENDPOINT,
                                            existing_section['id'],
                                            '?action=update_with_rules')
                client.post(api_endpoint, payload)
    if changes_detected:
        print('Done adding/updating firewall sections and rules!!\n')
    else:
        print('Detected no change with firewall sections and rules!!\n')


##############################
# Load balancers
##############################

def load_loadbalancer_monitors():
    api_endpoint = LBR_MONITORS_ENDPOINT
    resp = client.get(api_endpoint).json()
    for monitor in resp['results']:
        monitor_name = monitor['display_name']
        monitor_id = monitor['id']
        global_id_map['MONITOR:' + monitor_name] = monitor_id


def load_loadbalancer_app_profiles():
    api_endpoint = LBR_APPLICATION_PROFILE_ENDPOINT
    resp = client.get(api_endpoint).json()
    for app_profile in resp['results']:
        app_profile_name = app_profile['display_name']
        app_profile_id = app_profile['id']
        global_id_map['APP_PROFILE:' + app_profile_name] = app_profile_id


def load_loadbalancer_persistence_profiles():
    api_endpoint = LBR_PERSISTENCE_PROFILE_ENDPOINT
    resp = client.get(api_endpoint).json()
    for persistence_profile in resp['results']:
        persistence_profile_name = persistence_profile['display_name']
        persistence_profile_id = persistence_profile['id']
        global_id_map['PERSISTENCE_PROFILE:' + persistence_profile_name] = persistence_profile_id


def check_for_existing_lbr(existing_lbr_name):
    api_endpoint = LBR_SERVICES_ENDPOINT
    resp = client.get(api_endpoint).json()
    if resp is None or resp['result_count'] == 0:
        return None

    for lbr_member in resp['results']:
        if lbr_member['display_name'] == existing_lbr_name:
            return lbr_member

    return None


def check_for_existing_lbr_virtual_server(existing_lbr_vs_name):
    api_endpoint = LBR_VIRTUAL_SERVER_ENDPOINT
    resp = client.get(api_endpoint).json()
    if resp is None or resp['result_count'] == 0:
        return None

    for vs_member in resp['results']:
        if vs_member['display_name'] == existing_lbr_vs_name:
            return vs_member

    return None


def check_for_existing_lbr_pool(existing_lbr_pool_name):
    api_endpoint = LBR_POOLS_ENDPOINT
    resp = client.get(api_endpoint).json()
    if resp is None or resp['result_count'] == 0:
        return None

    for lbr_pool_member in resp['results']:
        if lbr_pool_member['display_name'] == existing_lbr_pool_name:
            return lbr_pool_member

    return None


def add_lbr_pool(virtual_server_defn):
    virtual_server_name = virtual_server_defn['name']

    existing_pool = check_for_existing_lbr_pool('%s%s' % (virtual_server_name, 'ServerPool'))

    pool_api_endpoint = LBR_POOLS_ENDPOINT
    lbActiveTcpMonitor = global_id_map['MONITOR:nsx-default-tcp-monitor']
    lbPassiveMonitor = global_id_map['MONITOR:nsx-default-passive-monitor']

    index = 1
    members = []

    pool_payload = {
        'resource_type': 'LbPool',
        'display_name': ('%s%s' % (virtual_server_name, 'ServerPool')),
        'tcp_multiplexing_number': 6,
        'min_active_members': 1,
        'tcp_multiplexing_enabled': False,
        'passive_monitor_id': lbPassiveMonitor,
        'active_monitor_ids': [lbActiveTcpMonitor],
        'snat_translation': {
            'port_overload': 1,
            'type': 'LbSnatAutoMap'
        }, 'algorithm': 'ROUND_ROBIN'}

    for member in virtual_server_defn['members']:
        member_name = ('%s-%s-%d' % (virtual_server_name, 'member', index))
        member = {
            'max_concurrent_connections': 10000,
            'port': member['port'],
            'weight': 1,
            'admin_state': 'ENABLED',
            'ip_address': member['ip'],
            'display_name': member_name,
            'backup_member': False
        }
        members.append(member)
        index += 1
    pool_payload['members'] = members

    print 'Payload for Server Pool: {}'.format(pool_payload)

    if existing_pool is None:
        resp = client.post(pool_api_endpoint, pool_payload).json()
        print 'Created Server Pool: {}'.format(virtual_server_name)
        print ''
        return resp['id']

    # Update existing server pool
    pool_payload['_revision'] = existing_pool['_revision']
    pool_payload['id'] = existing_pool['id']
    pool_update_api_endpoint = '%s/%s' % (pool_api_endpoint, existing_pool['id'])
    resp = client.put(pool_update_api_endpoint, pool_payload, check=False)
    print 'Updated Server Pool: {}'.format(virtual_server_name)
    print ''
    return existing_pool['id']


def add_lbr_virtual_server(virtual_server_defn):
    virtual_server_name = virtual_server_defn['name']

    existing_vip_name = ('%s%s' % (virtual_server_defn['name'], 'Vip'))
    existing_virtual_server = check_for_existing_lbr_virtual_server(existing_vip_name)

    virtual_server_api_endpoint = LBR_VIRTUAL_SERVER_ENDPOINT
    pool_id = add_lbr_pool(virtual_server_defn)

    # Go with TCP App profile and source-ip persistence profile
    lbFastTcpAppProfile = global_id_map['APP_PROFILE:nsx-default-lb-fast-tcp-profile']
    lbSourceIpPersistenceProfile = global_id_map['PERSISTENCE_PROFILE:nsx-default-source-ip-persistence-profile']

    vs_payload = {
        'resource_type': 'LbVirtualServer',
        'display_name': ('%s%s' % (virtual_server_defn['name'], 'Vip')),
        'max_concurrent_connections': 10000,
        'max_new_connection_rate': 1000,
        'persistence_profile_id': lbSourceIpPersistenceProfile,
        'application_profile_id': lbFastTcpAppProfile,
        'ip_address': virtual_server_defn['vip'],
        'pool_id': pool_id,
        'enabled': True,
        'ip_protocol': 'TCP',
        'port': virtual_server_defn['port']
    }

    if existing_virtual_server is None:
        resp = client.post(virtual_server_api_endpoint, vs_payload).json()
        print 'Created Virtual Server: {}'.format(virtual_server_name)
        return resp['id']

    # Update existing virtual server
    vs_payload['_revision'] = existing_virtual_server['_revision']
    vs_payload['id'] = existing_virtual_server['id']
    vs_update_api_endpoint = '%s/%s' % (virtual_server_api_endpoint, existing_virtual_server['id'])

    resp = client.put(vs_update_api_endpoint, vs_payload, check=False)
    print 'Updated Virtual Server: {}'.format(virtual_server_name)
    print ''
    return existing_virtual_server['id']


def add_loadbalancers():
    lbr_spec_defn = os.getenv('nsx_t_lbr_spec_int', '').strip()
    if lbr_spec_defn == '' or lbr_spec_defn == 'null':
        print('No yaml payload set for the NSX_T_LBR_SPEC, ignoring loadbalancer section!')
        return

    lbrs_defn = yaml.load(lbr_spec_defn)['loadbalancers']
    if lbrs_defn is None or len(lbrs_defn) <= 0:
        print('No valid yaml passed in the NSX_T_LBR_SPEC, nothing to add/update for LBR!')
        return

    for lbr in lbrs_defn:
        t1_router_id = global_id_map[build_router_key(TIER1, lbr['t1_router'])]
        if t1_router_id is None:
            raise Exception('Error!! No T1Router found with name: {} referred against LBR: {}'
                            .format(lbr['t1_router'], lbr['name']))

        lbr_api_endpoint = LBR_SERVICES_ENDPOINT
        lbr_service_payload = {
            'resource_type': 'LbService',
            'size': lbr['size'].upper(),
            'error_log_level': 'INFO',
            'display_name': lbr['name'],
            'attachment': {
                'target_display_name': lbr['t1_router'],
                'target_type': 'LogicalRouter',
                'target_id': t1_router_id
            }
        }

        virtual_servers = []
        for virtual_server_defn in lbr['virtual_servers']:
            virtual_server_id = add_lbr_virtual_server(virtual_server_defn)
            virtual_servers.append(virtual_server_id)

        lbr_service_payload['virtual_server_ids'] = virtual_servers

        existing_lbr = check_for_existing_lbr(lbr['name'])
        if existing_lbr is None:
            resp = client.post(lbr_api_endpoint, lbr_service_payload).json()
            print 'Created LBR: {}'.format(lbr['name'])
            print resp
            # TODO: error handling
        else:
            # Update existing LBR
            lbr_id = existing_lbr['id']

            lbr_service_payload['_revision'] = existing_lbr['_revision']
            lbr_service_payload['id'] = existing_lbr['id']

            lbr_update_api_endpoint = '%s/%s' % (lbr_api_endpoint, lbr_id)
            resp = client.put(lbr_update_api_endpoint, lbr_service_payload, check=False)
            print 'Updated LBR: {}'.format(lbr['name'])
            print resp


def create_all_t1_routers():
    # t0_router_content  = os.getenv('nsx_t_t0router_spec_int').strip()
    # t0_router         = yaml.load(t0_router_content)['t0_router']
    # if t0_router is None:
    #   print 'No valid T0Router content NSX_T_T0ROUTER_SPEC passed'
    #   return
    nat_rules_defn = os.getenv('nsx_t_nat_rules_spec_int', '').strip()
    nat_rules_defns = yaml.load(nat_rules_defn)['nat_rules']
    if nat_rules_defns is None or len(nat_rules_defns) <= 0:
        print('No nat rule entries in the NSX_T_NAT_RULES_SPEC, nothing to add/update!')
        return
    t0_router_name = nat_rules_defns[0]['t0_router']
    t0_router_key = build_router_key(TIER0, t0_router_name)
    t0_router_id = global_id_map[t0_router_key]
    t0_router = cache[t0_router_key]

    t1_router_content = os.getenv('nsx_t_t1router_logical_switches_spec_int')
    t1_routers = yaml.load(t1_router_content)['t1_routers']
    if t1_routers is None:
        print 'No valid T1Router content NSX_T_T1ROUTER_LOGICAL_SWITCHES_SPEC passed'
        return

    pas_tags = create_pas_tags()
    update_tag(ROUTERS_ENDPOINT + '/' + t0_router_id, pas_tags)

    # create_container_ip_blocks()
    # create_external_ip_pools()

    for t1_router in t1_routers:
        t1_router_name = t1_router['name']
        # check if it already exists
        t1_router_key = build_router_key(TIER1, t1_router_name)
        if t1_router_key not in global_id_map:
            t1_router_id = create_t1_logical_router_and_port(t0_router, t1_router)
            logical_switches = t1_router['switches']
            for logical_switch_entry in logical_switches:
                logical_switch_name = logical_switch_entry['name']
                logical_switch_subnet = '%s/%s' % (
                    logical_switch_entry['logical_switch_gw'],
                    logical_switch_entry['subnet_mask'])
                create_logical_switch(logical_switch_name)
                associate_logical_switch_port(t1_router_name, logical_switch_name, logical_switch_subnet)
        else:
            print "T1 router %s already exists, skip creating router for it" % t1_router_name
            t1_router_id = global_id_map[t1_router_key]

        advertise_lb_vip = True if t1_router.get('advertise_lb_vip') in ['true', True] else False
        enable_route_advertisement(t1_router_id, advertise_lb_vip=advertise_lb_vip)


def get_args():
    parser = argparse.ArgumentParser(
        description='Arguments for NSX resource config')

    parser.add_argument('-r', '--router_config',
                        required=True,
                        default='false',
                        action='store',
                        help='Whether to perform NSX router/IPAM/LB config')

    parser.add_argument('-c', '--generate_cert',
                        required=True,
                        default='false',
                        action='store',
                        help='Whether to generate NSX cert')

    args = parser.parse_args()
    return args


def main():
    args = get_args()
    init()

    if args.router_config.lower() == 'true':
        load_edge_clusters()
        load_transport_zones()
        load_logical_routers()
        load_loadbalancer_monitors()
        load_loadbalancer_app_profiles()
        load_loadbalancer_persistence_profiles()
        load_ip_blocks()
        load_ip_pools()

        # No support for switching profile in the ansible script yet
        # So create directly
        create_ha_switching_profile()

        # Set the route redistribution
        set_t0_route_redistribution()

        # print_t0_route_nat_rules()
        add_t0_route_nat_rules()

        # Apply BGP configs for t0 routers
        create_ip_sets()
        add_ip_prefix_lists()
        add_bgp_configs()
        add_firewall_sections_and_rules()

        create_all_t1_routers()

        create_container_ip_blocks()
        create_external_ip_pools()

        # Add Loadbalancers, update if already existing
        add_loadbalancers()

    if args.generate_cert.lower() == 'true':
        # Push this to the last step as the login gets kicked off
        # Generate self-signed cert
        generate_self_signed_cert()


if __name__ == '__main__':
    main()
