import fileinput

PARAMS_FILE = "nsx_pipeline_config.yml"
INTERNAL_CONFIG_FILE = "pipeline_config_internal.yml"
DEFAULT_SECTION = "Params generated with default values"
MGR_PWD = 'nsx_manager_password'
VC_USER = 'vcenter_username'
VC_PW = 'vcenter_password'


def add_default_params_if_necessary():
    optional_params = {
        'nsx_manager_virtual_ip': '',
        'nsx_manager_cluster_fqdn': '',
        'nsx_license_key': '',
        'nsx_manager_root_pwd': 'Admin!23Admin',
        'nsx_manager_cli_pwd': 'Admin!23Admin',
        'appliance_ready_wait': '2',
        'compute_manager_username': 'Administrator@vsphere.local',
        'compute_manager_password': 'Admin!23',
        'compute_manager_2_vcenter_ip': '',
        'compute_manager_2_username': '',
        'compute_manager_2_password': '',
        'tier0_uplink_port_ip_2': '',
        'tier0_ha_vip': '',
        'esx_ips': '',
        'esx_os_version': '',
        'esx_root_password': '',
        'esx_hostname_prefix': '',
        'nsx_t_t1router_logical_switches_spec': '',
        'nsx_t_ha_switching_profile_spec': '',
        'nsx_t_external_ip_pool_spec': '',
        'nsx_t_container_ip_block_spec': '',
        'nsx_t_nat_rules_spec': '',
        'nsx_t_csr_request_spec': '',
        'nsx_t_lbr_spec': ''
    }
    params_to_add = sorted(optional_params.keys())

    with open(PARAMS_FILE, 'r') as params_file:
        for line in params_file:
            for param in params_to_add:
                if param in line:
                    params_to_add.remove(param)
            default_infered = line.split(':')[-1].strip()
            if MGR_PWD in line:
                optional_params['nsx_manager_root_pwd'] = default_infered
                optional_params['nsx_manager_cli_pwd'] = default_infered
            elif VC_USER in line:
                optional_params['compute_manager_username'] = default_infered
            elif VC_PW in line:
                optional_params['compute_manager_password'] = default_infered

    has_default_section = False
    fin = fileinput.input(INTERNAL_CONFIG_FILE, inplace=1)
    for line in fin:
        if has_default_section:
            next(fin, None)
            continue
        if line.strip() == "### %s" % DEFAULT_SECTION:
            has_default_section = True
        print line,
        # Python 3 use the following line
        # print(line, end='')

    if params_to_add:
        with open(INTERNAL_CONFIG_FILE, 'a') as internal_params_file:
            if not has_default_section:
                internal_params_file.writelines('\n### %s\n' % DEFAULT_SECTION)
            for param_to_add in params_to_add:
                internal_params_file.writelines(
                    '%s: %s\n' % (param_to_add, optional_params[param_to_add]))


if __name__ == "__main__":
    add_default_params_if_necessary()
