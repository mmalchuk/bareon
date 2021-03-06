# Copyright 2014 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import unittest2

from bareon import errors
from bareon.objects import configdrive
from bareon.objects import User


class TestConfigDriveScheme(unittest2.TestCase):

    def setUp(self):
        super(TestConfigDriveScheme, self).setUp()
        self.cd_scheme = configdrive.ConfigDriveScheme()

    def test_templates_default(self):
        self.assertEqual({}, self.cd_scheme.templates)

    def test_set_cloud_init_templates(self):
        cloud_init_templates = {
            'boothook': 'boothook.jinja2',
            'cloud_config': 'cloud_config.jinja2',
            'meta-data': 'meta-data.jinja2',
        }
        self.cd_scheme.set_cloud_init_templates(cloud_init_templates)
        self.assertEqual(cloud_init_templates, self.cd_scheme.templates)

    def test_template_names(self):
        self.cd_scheme.set_cloud_init_templates(
            {'what': 'what_fuel_1.2.3_os.jinja2'})
        self.cd_scheme._profile = 'pro_fi-le'
        actual = self.cd_scheme.template_names('what')
        expected = [
            'what_fuel_1.2.3_os.jinja2',
            'what_pro_fi-le.jinja2',
            'what_pro.jinja2',
            'what_pro_fi.jinja2',
            'what.jinja2'
        ]
        self.assertEqual(expected, actual)

    def test_template_data_no_common(self):
        self.assertRaises(errors.WrongConfigDriveDataError,
                          self.cd_scheme.template_data)

    def test_template_data_ok(self):
        cd_common = configdrive.ConfigDriveCommon(
            ['auth_key1', 'auth_key2'], 'hostname', 'fqdn', 'name_servers',
            'search_domain', 'master_ip', 'master_url', 'udevrules',
            'admin_mac', 'admin_ip', 'admin_mask', 'admin_iface_name',
            'timezone', {'repo1': 'repo1_url', 'repo2': 'repo2_url'}, 'gw')
        cd_puppet = configdrive.ConfigDrivePuppet('master', 0)
        cd_mcollective = configdrive.ConfigDriveMcollective(
            'pskey', 'vhost', 'host', 'user', 'password', 'connector', 1, -1)
        cd_user_accounts = []
        cd_user_accounts.append(User('fuel', 'fuel', '/var/lib/fuel',
                                     ['ALL=(ALL) NOPASSWD: ALL']))
        cd_user_accounts.append(User('test', 'test', '/home/test',
                                     ['SUDO'], ['KEY']))
        self.cd_scheme.common = cd_common
        self.cd_scheme.puppet = cd_puppet
        self.cd_scheme.mcollective = cd_mcollective
        self.cd_scheme.user_accounts = cd_user_accounts
        template_data = self.cd_scheme.template_data()
        self.assertEqual(cd_common, template_data['common'])
        self.assertEqual(cd_puppet, template_data['puppet'])
        self.assertEqual(cd_mcollective, template_data['mcollective'])
        self.assertEqual(cd_user_accounts, template_data['user_accounts'])
