import mock
from nose.tools import set_trace
import library.cl_interface as cl_int
from asserts import assert_equals
from mock import MagicMock
import json


@mock.patch('library.cl_interface.os.path.exists')
@mock.patch('library.cl_interface.replace_config')
@mock.patch('library.cl_interface.config_changed')
@mock.patch('library.cl_interface.build_desired_iface_config')
@mock.patch('library.cl_interface.current_iface_config')
@mock.patch('library.cl_interface.AnsibleModule')
def test_module_args(mock_module,
                     mock_curr_config,
                     mock_desired_config,
                     mock_compare,
                     mock_replace,
                     mock_exists):
    """ cl_interface - test module args """
    mock_exists.return_value = True
    cl_int.main()
    mock_module.assert_called_with(
        required_together=[['virtual_ip', 'virtual_mac'],
                           ['clagd_enable', 'clagd_priority',
                            'clagd_peer_ip', 'clagd_sys_mac'],
                           ['clagd_enable', 'clagd_backup_ip']],
        argument_spec={
            'addr_method': {
                'type': 'str',
                'choices': ['', 'loopback', 'dhcp']},
            'name': {'required': True, 'type': 'str'},
            'mtu': {'type': 'str'},
            'alias_name': {'type': 'str'},
            'ipv4': {'type': 'list'},
            'ipv6': {'type': 'list'},
            'virtual_mac': {'type': 'str'},
            'virtual_ip': {'type': 'str'},
            'vids': {'type': 'list'},
            'pvid': {'type': 'str'},
            'bridge_access': {'type': 'str'},
            'mstpctl_portnetwork': {'type': 'bool', 'choices': [
                'yes', 'on', '1', 'true', 1, 'no', 'off', '0', 'false', 0]},
            'mstpctl_portadminedge': {'type': 'bool', 'choices': [
                'yes', 'on', '1', 'true', 1, 'no', 'off', '0', 'false', 0]},
            'mstpctl_bpduguard': {'type': 'bool', 'choices': [
                'yes', 'on', '1', 'true', 1, 'no', 'off', '0', 'false', 0]},
            'clagd_enable': {'type': 'bool', 'choices': [
                'yes', 'on', '1', 'true', 1, 'no', 'off', '0', 'false', 0]},
            'clagd_peer_ip': {'type': 'str'},
            'clagd_sys_mac': {'type': 'str'},
            'clagd_priority': {'type': 'str'},
            'clagd_args': {'type': 'str'},
            'clagd_backup_ip': {'type': 'str'},
            'location': {'type': 'str',
                         'default': '/etc/network/interfaces.d'},
            'speed': {'type': 'str'}}
    )


@mock.patch('library.cl_interface.os.path.exists')
@mock.patch('library.cl_interface.replace_config')
@mock.patch('library.cl_interface.config_changed')
@mock.patch('library.cl_interface.build_desired_iface_config')
@mock.patch('library.cl_interface.current_iface_config')
@mock.patch('library.cl_interface.AnsibleModule')
def test_main_integration_test(mock_module,
                               mock_curr_config,
                               mock_desired_config,
                               mock_compare,
                               mock_replace, mock_exists):
    """ cl_interface - basic integration test of main """
    mock_exists.return_value = True
    instance = mock_module.return_value
    # if config_changed == false. no change
    instance.params = {'name': 'swp1'}
    mock_compare.return_value = False
    cl_int.main()
    instance.exit_json.assert_called_with(
        msg='interface swp1 config not changed',
        changed=False)
    # if config_changed == true, change
    mock_compare.return_value = True
    cl_int.main()
    instance.exit_json.assert_called_with(
        msg='interface swp1 config updated',
        changed=True)
    # if location does not exist
    instance.params['location'] = '/etc/network/ansible'
    mock_exists.return_value = False
    cl_int.main()
    instance.fail_json.assert_called_with(msg='/etc/network/ansible does not exist.')


@mock.patch('library.cl_interface.os.path.exists')
@mock.patch('library.cl_interface.AnsibleModule')
def test_current_iface_config(mock_module, mock_exists):
    """
    cl_interface - test getting current iface config
    """
    mock_module.params = {'name': 'swp1', 'location': '/etc/network/ansible'}
    mock_exists.return_value = True
    mock_module.run_command = MagicMock()
    # mock AnsibleModule.run_command
    json_output = open('tests/ifquery.json').read()
    mock_module.run_command.return_value = \
        (0, json_output, None)
    mock_module.from_json.return_value = json.loads(json_output)
    cl_int.current_iface_config(mock_module)
    current_config = mock_module.custom_current_config.get('config')
    assert_equals(current_config.get('address'), '10.152.5.10/24')
    mock_exists.assert_called_with('/etc/network/ansible/swp1')
    mock_module.run_command.assert_called_with('/sbin/ifquery -o json swp1')


@mock.patch('library.cl_interface.AnsibleModule')
def test_vrr(mock_module):
    """
    cl_interface: - test build vrr config
    """
    mock_module.custom_desired_config = {'config': {}}
    mock_module.params = {'virtual_ip': '192.168.1.1/24',
                          'virtual_mac': '00:00:5e:00:01:01'}
    cl_int.build_vrr(mock_module)
    assert_equals(mock_module.custom_desired_config,
                  {'config': {
                      'address-virtual':
                      '00:00:5e:00:01:01 192.168.1.1/24'}})

    # if virtual_ip/mac is blank
    mock_module.custom_desired_config = {'config': {}}
    mock_module.params = {}
    cl_int.build_vrr(mock_module)
    assert_equals(mock_module.custom_desired_config,
                  {'config': {}})


@mock.patch('library.cl_interface.AnsibleModule')
def test_build_address(mock_module):
    """
    cl_interface: - test building desired address config
    """
    mock_module.custom_desired_config = {'config': {}}
    mock_module.params = {'ipv4': ['1.1.1.1/24'], 'ipv6': ['2001:db8:abcd::/48']}
    cl_int.build_address(mock_module)
    assert_equals(mock_module.custom_desired_config,
                  {'config': {'address': ['1.1.1.1/24', '2001:db8:abcd::/48']}})


@mock.patch('library.cl_interface.AnsibleModule')
def test_build_addr_method(mock_module):
    """
    cl_interface - test building desired addr_method
    """
    mock_module.custom_desired_config = {'config': {}}
    mock_module.params = {'addr_method': 'loopback'}
    cl_int.build_addr_method(mock_module)
    assert_equals(mock_module.custom_desired_config.get('addr_family'),
                  'inet')
    assert_equals(mock_module.custom_desired_config.get('addr_method'),
                  'loopback')


@mock.patch('library.cl_interface.AnsibleModule')
def test_build_vids(mock_module):
    """
    cl_interface - test building desired vids config
    """
    mock_module.custom_desired_config = {'config': {}}
    mock_module.params = {'vids': ['1', '10-40']}
    cl_int.build_vids(mock_module)
    assert_equals(mock_module.custom_desired_config,
                  {'config': {'bridge-vids': '1 10-40'}})


@mock.patch('library.cl_interface.AnsibleModule')
def test_build_pvid(mock_module):
    """
    cl_interface - test building desired pvid
    """
    mock_module.custom_desired_config = {'config': {}}
    mock_module.params = {'pvid': 2}
    cl_int.build_pvid(mock_module)
    assert_equals(mock_module.custom_desired_config,
                  {'config': {'bridge-pvid': '2'}})


@mock.patch('library.cl_interface.AnsibleModule')
def test_build_bridge_access(mock_module):
    """
    cl_interface - test building desired bridge_access
    """
    mock_module.custom_desired_config = {'config': {}}
    mock_module.params = {'bridge_access': 2}
    cl_int.build_bridge_access(mock_module)
    assert_equals(mock_module.custom_desired_config,
                  {'config': {'bridge_access': '2'}})


@mock.patch('library.cl_interface.AnsibleModule')
def test_build_speed(mock_module):
    """
    cl_interface - test building speed config
    """
    mock_module.custom_desired_config = {'config': {}}
    mock_module.params = {'speed': 1000}
    cl_int.build_speed(mock_module)
    assert_equals(mock_module.custom_desired_config,
                  {'config': {
                      'link-speed': '1000',
                      'link-duplex': 'full'}})


@mock.patch('library.cl_interface.AnsibleModule')
def test_build_generic_attr(mock_module):
    """
    cl_interface - adding values from module parameters that match
    the ones provided by ifupdown2 json output.
    """
    # test integer
    mock_module.custom_desired_config = {'config': {}}
    mock_module.params = {'mtu': 1000}
    cl_int.build_generic_attr(mock_module, 'mtu')
    assert_equals(mock_module.custom_desired_config,
                  {'config': {
                      'mtu': '1000'}})
    # test bool
    mock_module.custom_desired_config = {'config': {}}
    mock_module.params = {'clagd_enable': True}
    cl_int.build_generic_attr(mock_module, 'clagd_enable')
    assert_equals(mock_module.custom_desired_config,
                  {'config': {
                      'clagd-enable': 'yes'}})


@mock.patch('library.cl_interface.AnsibleModule')
def test_config_dict_changed(mock_module):
    mock_module.custom_desired_config = {'config': {'address': '10.1.1.1/24'}}
    mock_module.custom_current_config = {}
    assert_equals(cl_int.config_dict_changed(mock_module), True)


@mock.patch('library.cl_interface.AnsibleModule')
def test_config_changed(mock_module):
    """
    cl_interface - test config change
    """
    # no change
    mock_module.custom_desired_config = {
        'name': 'swp1',
        'addr_method': None,
        'config':
        {'address': '10.1.1.1/24',
         'mtu': '9000'}
    }
    mock_module.custom_current_config = {
        'name': 'swp1',
        'addr_method': None,
        'config':
        {'address': '10.1.1.1/24',
         'mtu': '9000'}
    }
    assert_equals(cl_int.config_changed(mock_module), False)
    # change
    mock_module.custom_desired_config = {
        'name': 'swp1',
        'addr_method': None,
        'config':
        {'address': '10.1.1.2/24',
         'mtu': '9000'}
    }
    mock_module.custom_current_config = {
        'name': 'swp1',
        'addr_method': None,
        'config':
        {'address': '10.1.1.1/24',
         'mtu': '9000'}
    }
    assert_equals(cl_int.config_changed(mock_module), True)
    # config hash has no changed, but  addr_method has changed
    mock_module.custom_desired_config = {
        'name': 'swp1',
        'addr_method': 'dhcp',
        'config':
        {'mtu': '9000'}
    }
    mock_module.custom_current_config = {
        'name': 'swp1',
        'addr_method': None,
        'config':
        {'mtu': '9000'}
    }
    assert_equals(cl_int.config_changed(mock_module), True)


@mock.patch('library.cl_interface.AnsibleModule')
@mock.patch('library.cl_interface.run_cmd')
def test_replace_config_ifquery_not_outputting_text(mock_run_cmd, mock_module):
    mock_module.params = {'location': './tests/',
                          'name': 'swp1'
                          }
    mock_module.custom_desired_config = {
        'name': 'swp1',
        'addr_method': None,
        'config':
        {'address': '10.1.1.2/24',
         'mtu': '9000'}
    }
    mock_run_cmd.return_value = ''
    mock_module.jsonify = MagicMock(
        return_value=json.dumps([mock_module.custom_desired_config]))
    cl_int.replace_config(mock_module)
    _msg='desired_config not copied into ifupdown2 text format. Not writing config to file'
    mock_module.fail_json.assert_called_with(msg=_msg)

@mock.patch('library.cl_interface.AnsibleModule')
@mock.patch('library.cl_interface.run_cmd')
def test_replace_config_ifquery_not_outputting_text(mock_run_cmd, mock_module):
    mock_module.params = {'location': './tests/',
                          'name': 'swp1'
                          }
    mock_module.custom_desired_config = {
        'name': 'swp1',
        'addr_method': None,
        'config':
        {'address': '10.1.1.2/24',
         'mtu': '9000'}
    }
    mock_run_cmd.return_value = 'ifupdown did something'
    mock_module.jsonify = MagicMock(
        return_value=json.dumps([mock_module.custom_desired_config]))
    cl_int.replace_config(mock_module)
    assert_equals(mock_module.fail_json.call_count, 0)
