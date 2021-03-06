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

import mock
import unittest2

from bareon import errors
from bareon import objects


class TestMultipleDevice(unittest2.TestCase):
    def setUp(self):
        super(self.__class__, self).setUp()
        self.md = objects.MultipleDevice(name='name', level='level')

    def test_add_device_ok(self):
        self.assertEqual(0, len(self.md.devices))
        self.md.add_device('device')
        self.assertEqual(1, len(self.md.devices))
        self.assertEqual('device', self.md.devices[0])

    def test_add_device_in_spares_fail(self):
        self.assertEqual(0, len(self.md.devices))
        self.assertEqual(0, len(self.md.spares))
        self.md.add_spare('device')
        self.assertRaises(errors.MDDeviceDuplicationError, self.md.add_device,
                          'device')

    def test_add_device_in_devices_fail(self):
        self.assertEqual(0, len(self.md.devices))
        self.assertEqual(0, len(self.md.spares))
        self.md.add_device('device')
        self.assertRaises(errors.MDDeviceDuplicationError, self.md.add_device,
                          'device')

    def test_add_spare_in_spares_fail(self):
        self.assertEqual(0, len(self.md.devices))
        self.assertEqual(0, len(self.md.spares))
        self.md.add_spare('device')
        self.assertRaises(errors.MDDeviceDuplicationError, self.md.add_spare,
                          'device')

    def test_add_spare_in_devices_fail(self):
        self.assertEqual(0, len(self.md.devices))
        self.assertEqual(0, len(self.md.spares))
        self.md.add_device('device')
        self.assertRaises(errors.MDDeviceDuplicationError, self.md.add_spare,
                          'device')

    def test_conversion(self):
        self.md.add_device('device_a')
        self.md.add_spare('device_b')
        serialized = self.md.to_dict()
        assert serialized == {
            'name': 'name',
            'level': 'level',
            'devices': ['device_a', ],
            'spares': ['device_b', ],
            'metadata': 'default',
            'keep_data': False,
        }
        new_md = objects.MultipleDevice.from_dict(serialized)
        assert serialized == new_md.to_dict()


class TestPartition(unittest2.TestCase):
    def setUp(self):
        super(TestPartition, self).setUp()
        self.pt = objects.Partition('name', 'count', 'device', 'begin',
                                    'end', 'partition_type')

    def test_set_flag(self):
        self.assertEqual(0, len(self.pt.flags))
        self.pt.set_flag('fake_flag')
        self.assertEqual(1, len(self.pt.flags))
        self.assertIn('fake_flag', self.pt.flags)

    def test_conversion(self):
        self.pt.flags.append('some_flag')
        self.pt.guid = 'some_guid'
        serialized = self.pt.to_dict()
        assert serialized == {
            'begin': 'begin',
            'configdrive': False,
            'count': 'count',
            'device': 'device',
            'end': 'end',
            'flags': ['some_flag', ],
            'guid': 'some_guid',
            'name': 'name',
            'partition_type': 'partition_type',
            'keep_data': False,
        }
        new_pt = objects.Partition.from_dict(serialized)
        assert serialized == new_pt.to_dict()


class TestPartitionScheme(unittest2.TestCase):
    def setUp(self):
        super(TestPartitionScheme, self).setUp()
        self.p_scheme = objects.PartitionScheme()

    def test_root_device_not_found(self):
        self.assertRaises(errors.WrongPartitionSchemeError,
                          self.p_scheme.root_device)

    def test_fs_by_device(self):
        expected_fs = objects.FileSystem('device')
        self.p_scheme.fss.append(expected_fs)
        self.p_scheme.fss.append(objects.FileSystem('wrong_device'))
        actual_fs = self.p_scheme.fs_by_device('device')
        self.assertEqual(expected_fs, actual_fs)

    def test_fs_by_mount(self):
        expected_fs = objects.FileSystem('d', mount='mount')
        self.p_scheme.fss.append(expected_fs)
        self.p_scheme.fss.append(objects.FileSystem('w_d',
                                                    mount='wrong_mount'))
        actual_fs = self.p_scheme.fs_by_mount('mount')
        self.assertEqual(expected_fs, actual_fs)

    def test_pv_by_name(self):
        expected_pv = objects.PhysicalVolume('pv')
        self.p_scheme.pvs.append(expected_pv)
        self.p_scheme.pvs.append(objects.PhysicalVolume('wrong_pv'))
        actual_pv = self.p_scheme.pv_by_name('pv')
        self.assertEqual(expected_pv, actual_pv)

    def test_vg_by_name(self):
        expected_vg = objects.VolumeGroup('vg')
        self.p_scheme.vgs.append(expected_vg)
        self.p_scheme.vgs.append(objects.VolumeGroup('wrong_vg'))
        actual_vg = self.p_scheme.vg_by_name('vg')
        self.assertEqual(expected_vg, actual_vg)

    def test_vg_attach_by_name(self):
        self.p_scheme.vg_attach_by_name('pvname', 'vgname')
        self.assertEqual(1, len(self.p_scheme.pvs))
        self.assertEqual(1, len(self.p_scheme.vgs))
        self.assertIn('pvname', self.p_scheme.vgs[0].pvnames)
        self.assertIn('vgname', self.p_scheme.vgs[0].name)

    def test_md_next_name_ok(self):
        expected_name = '/dev/md0'
        self.assertEqual(expected_name, self.p_scheme.md_next_name())

    def test_md_next_name_fail(self):
        self.p_scheme.mds = [
            objects.MultipleDevice('/dev/md%s' % x, 'level')
            for x in range(0, 128)
        ]
        self.assertRaises(errors.MDAlreadyExistsError,
                          self.p_scheme.md_next_name)

    def test_partition_by_name(self):
        parted_1 = self.p_scheme.add_parted(name='name_1', label='label_1')
        parted_1.add_partition(size=1)

        parted_2 = self.p_scheme.add_parted(name='name_2', label='label_2')
        expected_prt = parted_2.add_partition(size=1)

        actual_prt = self.p_scheme.partition_by_name(expected_prt.name)
        self.assertEqual(expected_prt, actual_prt)

    def test_md_by_name(self):
        self.assertEqual(0, len(self.p_scheme.mds))
        expected_md = objects.MultipleDevice('name', 'level')
        self.p_scheme.mds.append(expected_md)
        self.p_scheme.mds.append(objects.MultipleDevice('wrong_name', 'level'))
        self.assertEqual(expected_md, self.p_scheme.md_by_name('name'))

    def test_md_by_mount(self):
        self.assertEqual(0, len(self.p_scheme.mds))
        self.assertEqual(0, len(self.p_scheme.fss))
        expected_md = objects.MultipleDevice('name', 'level')
        expected_fs = objects.FileSystem('name', mount='mount')
        self.p_scheme.mds.append(expected_md)
        self.p_scheme.fss.append(expected_fs)
        self.p_scheme.fss.append(objects.FileSystem('wrong_name',
                                 mount='wrong_mount'))
        self.assertEqual(expected_md, self.p_scheme.md_by_mount('mount'))

    def test_md_attach_by_mount_md_exists(self):
        self.assertEqual(0, len(self.p_scheme.mds))
        self.assertEqual(0, len(self.p_scheme.fss))
        expected_md = objects.MultipleDevice('name', 'level')
        expected_fs = objects.FileSystem('name', mount='mount')
        self.p_scheme.mds.append(expected_md)
        self.p_scheme.fss.append(expected_fs)
        actual_md = self.p_scheme.md_attach_by_mount('device', 'mount')
        self.assertIn('device', actual_md.devices)
        self.assertEqual(expected_md, actual_md)

    def test_md_attach_by_mount_no_md(self):
        self.assertEqual(0, len(self.p_scheme.mds))
        self.assertEqual(0, len(self.p_scheme.fss))
        actual_md = self.p_scheme.md_attach_by_mount(
            'device', 'mount', fs_type='fs_type', fs_options='-F',
            fs_label='fs_label', name='name', level='level')
        self.assertIn('device', actual_md.devices)
        self.assertEqual(1, len(self.p_scheme.fss))
        self.assertEqual('name', self.p_scheme.fss[0].device)
        self.assertEqual('mount', self.p_scheme.fss[0].mount)
        self.assertEqual('fs_type', self.p_scheme.fss[0].type)
        self.assertEqual('fs_label', self.p_scheme.fss[0].label)
        self.assertEqual('-F', self.p_scheme.fss[0].options)

    def test_elevate_keep_data(self):
        self.assertEqual(0, len(self.p_scheme.vgs))
        self.assertEqual(0, len(self.p_scheme.lvs))
        self.assertEqual(0, len(self.p_scheme.fss))
        parted = self.p_scheme.add_parted(name='fake_name', label='fake_label')
        prt = parted.add_partition(size=1, keep_data=True)

        self.p_scheme.vg_attach_by_name(prt.name, 'fake_vg')
        vg = self.p_scheme.vgs[0]

        self.p_scheme.add_lv(name='fake_lv', vgname=vg.name, size=1)
        lv = self.p_scheme.lvs[0]

        self.p_scheme.add_fs(device=lv.device_name, mount='fake_mount',
                             fs_type='xfs', fs_label='fake_label')
        fs = self.p_scheme.fss[0]

        self.p_scheme.elevate_keep_data()

        self.assertTrue(fs.keep_data)
        self.assertFalse(lv.keep_data)
        self.assertFalse(vg.keep_data)
        self.assertFalse(prt.keep_data)


class TestParted(unittest2.TestCase):
    def setUp(self):
        super(TestParted, self).setUp()
        self.prtd = objects.Parted('name', 'label')

    @mock.patch.object(objects.Parted, 'next_count')
    @mock.patch.object(objects.Parted, 'next_type')
    def test_next_name_none(self, nt_mock, nc_mock):
        nc_mock.return_value = 1
        nt_mock.return_value = 'extended'
        self.assertEqual(None, self.prtd.next_name())

    @mock.patch.object(objects.Parted, 'next_count')
    @mock.patch.object(objects.Parted, 'next_type')
    def test_next_name_no_separator(self, nt_mock, nc_mock):
        nc_mock.return_value = 1
        nt_mock.return_value = 'not_extended'
        expected_name = '%s%s' % (self.prtd.name, 1)
        self.assertEqual(expected_name, self.prtd.next_name())

    @mock.patch.object(objects.Parted, 'next_count')
    @mock.patch.object(objects.Parted, 'next_type')
    def test_next_name_with_separator(self, nt_mock, nc_mock):
        nc_mock.return_value = 1
        nt_mock.return_value = 'not_extended'
        for self.prtd.name in ('/dev/cciss/c0d0', '/dev/loop123',
                               '/dev/nvme0n1', '/dev/md127'):
            expected_name = '%sp%s' % (self.prtd.name, 1)
            self.assertEqual(expected_name, self.prtd.next_name())

    def test_next_begin_empty_partitions(self):
        self.assertEqual(1, self.prtd.next_begin())

    def test_next_begin_last_extended_partition(self):
        self.prtd.partitions.append(
            objects.Partition('name', 'count', 'device', 'begin', 'end',
                              'extended'))
        self.assertEqual('begin', self.prtd.next_begin())

    def test_next_begin_no_last_extended_partition(self):
        self.prtd.partitions.append(
            objects.Partition('name', 'count', 'device', 'begin', 'end',
                              'primary'))
        self.assertEqual('end', self.prtd.next_begin())

    def test_next_count_no_logical(self):
        self.assertEqual(1, self.prtd.next_count('primary'))

    def test_next_count_has_logical(self):
        self.prtd.partitions.append(
            objects.Partition('name', 'count', 'device', 'begin', 'end',
                              'logical'))
        self.assertEqual(6, self.prtd.next_count('logical'))

    def test_next_type_gpt(self):
        self.prtd.label = 'gpt'
        self.assertEqual('primary', self.prtd.next_type())

    def test_next_type_no_extended(self):
        self.prtd.label = 'msdos'
        self.assertEqual('primary', self.prtd.next_type())
        self.prtd.partitions.extend(
            3 * [objects.Partition('name', 'count', 'device', 'begin',
                                   'end', 'primary')])
        self.assertEqual('extended', self.prtd.next_type())

    def test_next_type_has_extended(self):
        self.prtd.label = 'msdos'
        self.prtd.partitions.append(
            objects.Partition('name', 'count', 'device', 'begin', 'end',
                              'extended'))
        self.assertEqual('logical', self.prtd.next_type())

    def test_primary(self):
        expected_partitions = [objects.Partition('name', 'count', 'device',
                                                 'begin', 'end', 'primary')]
        self.prtd.partitions.extend(expected_partitions)
        self.assertEqual(expected_partitions, self.prtd.primary)

    def test_partition_by_name(self):
        self.prtd.add_partition(size=1)
        self.prtd.add_partition(size=1)
        expected_prt = self.prtd.add_partition(size=1)

        actual_prt = self.prtd.partition_by_name(expected_prt.name)
        self.assertEqual(expected_prt, actual_prt)

    def test_conversion(self):
        prt = objects.Partition(
            name='name',
            count='count',
            device='device',
            begin='begin',
            end='end',
            partition_type='primary',
            keep_data=True
        )
        self.prtd.partitions.append(prt)
        serialized = self.prtd.to_dict()
        assert serialized == {
            'label': 'label',
            'name': 'name',
            'disk_size': None,
            'partitions': [
                prt.to_dict(),
            ],
            'install_bootloader': False,
        }
        new_prtd = objects.Parted.from_dict(serialized)
        assert serialized == new_prtd.to_dict()


class TestLogicalVolume(unittest2.TestCase):

    def test_conversion(self):
        lv = objects.LogicalVolume(
            name='lv-name',
            vgname='vg-name',
            size=1234
        )
        serialized = lv.to_dict()
        assert serialized == {
            'name': 'lv-name',
            'vgname': 'vg-name',
            'size': 1234,
            'keep_data': False,
        }
        new_lv = objects.LogicalVolume.from_dict(serialized)
        assert serialized == new_lv.to_dict()


class TestPhysicalVolume(unittest2.TestCase):

    def test_conversion(self):
        pv = objects.PhysicalVolume(
            name='pv-name',
            metadatasize=987,
            metadatacopies=112,
        )
        serialized = pv.to_dict()
        assert serialized == {
            'name': 'pv-name',
            'metadatasize': 987,
            'metadatacopies': 112,
            'keep_data': False,
        }
        new_pv = objects.PhysicalVolume.from_dict(serialized)
        assert serialized == new_pv.to_dict()


class TestVolumesGroup(unittest2.TestCase):

    def test_conversion(self):
        vg = objects.VolumeGroup(
            name='vg-name',
            pvnames=['pv-name-a', ]
        )
        serialized = vg.to_dict()
        assert serialized == {
            'name': 'vg-name',
            'pvnames': ['pv-name-a', ],
            'keep_data': False,
        }
        new_vg = objects.VolumeGroup.from_dict(serialized)
        assert serialized == new_vg.to_dict()


class TestFileSystem(unittest2.TestCase):

    def test_conversion(self):
        fs = objects.FileSystem(
            device='some-device',
            mount='/mount',
            fs_type='type',
            fs_options='some-option',
            fs_label='some-label',
        )
        serialized = fs.to_dict()
        assert serialized == {
            'device': 'some-device',
            'mount': '/mount',
            'fs_type': 'type',
            'fs_options': 'some-option',
            'fs_label': 'some-label',
            'keep_data': False,
            'fstab_enabled': True,
            'fstab_options': 'defaults',
            'os_id': []
        }
        new_fs = objects.FileSystem.from_dict(serialized)
        assert serialized == new_fs.to_dict()
