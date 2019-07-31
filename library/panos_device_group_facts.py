#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Christopher Juhlin <christopher.juhlin@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: panos_device_group_facts
short_description: Retrieve facts about device group objects on PAN-OS devices.
description:
    - Retrieves tag information device group objects on PAN-OS devices.
author: "Christopher Juhlin (@nebi)"
version_added: "2.9"
requirements:
    - pan-python can be obtained from PyPI U(https://pypi.python.org/pypi/pan-python)
    - pandevice can be obtained from PyPI U(https://pypi.python.org/pypi/pandevice)
notes:
    - Panorama is supported.
    - Check mode is not supported.
    - Firewall is not supported.
extends_documentation_fragment:
    - panos.transitional_provider
options:
    name:
        description:
            - Name of device group to retrieve.
            - Mutually exclusive with I(name_regex).
    name_regex:
        description:
            - A python regex for an device group's name to retrieve.
            - Mutually exclusive with I(name).
    tag:
        description:
            - Name of tag to retrieve.
            - Mutually exclusive with I(tag_regex).
    tag_regex:
        description:
            - A python regex for an device group's tag to retrieve.
            - Mutually exclusive with I(tag).
'''

EXAMPLES = '''
- name: Retrieve device group object 'Prod'
  panos_device_group_facts:
    provider: '{{ provider }}'
    name: 'Prod'
  register: result

- name: Retrieve device group's that have tag 'Prod-Services'
  panos_device_group_facts:
    provider: '{{ provider }}'
    tag: 'Prod-Services'
  register: result

- name: Find all device groups with "Prod" in the name
  panos_device_group_facts:
    provider: '{{ provider }}'
    name_regex: '.*Prod.*'
  register: result
'''

RETURN = '''
results:
    description: Dict containing object attributes.  Empty if object is not found.
    returned: when "name" is specified
    type: dict
objects:
    description: List of object dicts.
    returned: always
    type: list
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.panos.panos import get_connection


try:
    from pandevice import objects
    from pandevice.errors import PanDeviceError
    from pandevice.panorama import Panorama
except ImportError:
    pass

COLORS = {
    'color1': 'red',
    'color2': 'green',
    'color3': 'blue',
    'color4': 'yellow',
    'color5': 'copper',
    'color6': 'orange',
    'color7': 'purple',
    'color8': 'gray',
    'color9': 'light green',
    'color10': 'cyan',
    'color11': 'light gray',
    'color12': 'blue gray',
    'color13': 'lime',
    'color14': 'black',
    'color15': 'gold',
    'color16': 'brown',
}


def colorize(obj, object_type):
    ans = obj.about()
    if object_type == 'tag':
        # Fail gracefully if the color is unknown.
        ans['color'] = COLORS.get(obj.color, obj.color)

    return ans


def main():
    name_params = ['name', 'name_regex', 'tag', 'tag_regex']
    helper = get_connection(
        vsys=True,
        firewall_error='This module is for panorama only',
        device_group=True,
        with_classic_provider_spec=True,
        required_one_of=[name_params, ],
        argument_spec=dict(
            name=dict(),
            name_regex=dict(),
            tag=dict(),
            tag_regex=dict(),
        ),
    )
    module = AnsibleModule(
        argument_spec=helper.argument_spec,
        supports_check_mode=False,
        required_one_of=helper.required_one_of,
        mutually_exclusive=[name_params, ],
    )

    parent = helper.get_pandevice_parent(module)

    try:
        obj_listing = Panorama.refresh_devices(parent)
    except PanDeviceError as e:
        module.fail_json(msg='Failed {0} refresh: {1}'.format("Device group", e))

    results = {}
    ans_objects = []
    DeviceGroupList = []

    if module.params['name'] is not None:
        for obj in obj_listing:
            try:
                if obj.uid == module.params['name']:
                    DeviceObject = obj.about()
                    DeviceGroupList.append(
                        {
                            'name': obj.uid,
                            'tag': DeviceObject['tag']
                        }
                    )
                    ans_objects.append(DeviceGroupList)
            except BaseException:
                pass
    elif module.params['tag'] is not None:
        for obj in obj_listing:
            DeviceObject = obj.about()
            try:
                for x in DeviceGroupObject['tag']:
                    if x == module.params['tag']:
                        DeviceGroupList.append(
                            {
                                'name': obj.uid,
                                'tag': DeviceObject['tag']
                            }
                        )
                        ans_objects.append(DeviceGroupList)
            except BaseException:
                pass
    elif module.params['tag_regex'] is not None:
        try:
            matcher = re.compile(module.params['tag_regex'])
        except Exception as e:
            module.fail_json(msg='Invalid regex: {0}'.format(e))

        for obj in obj_listing:
            try:
                DeviceObject = obj.about()
                for y in DeviceObject['tag']:
                    if matcher.search(y) is not None:
                        DeviceGroupList.append(
                            {
                                'name': obj.uid,
                                'tag': DeviceObject['tag']
                            }
                        )
                        ans_objects.append(DeviceGroupList)
            except BaseException:
                pass
    else:
        try:
            matcher = re.compile(module.params['name_regex'])
        except Exception as e:
            module.fail_json(msg='Invalid regex: {0}'.format(e))

        for obj in obj_listing:
            if matcher.search(obj.uid) is not None:
                ans_objects.append(colorize(obj, "device_group"))

    module.exit_json(changed=False, results=results, objects=ans_objects)


if __name__ == '__main__':
    main()
