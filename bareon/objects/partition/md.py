# -*- coding: utf-8 -*-

#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from bareon import errors
from bareon.objects import base


class MultipleDevice(base.Serializable):

    def __init__(self, name, level,
                 devices=None, spares=None, keep_data=False,
                 metadata='default'):
        self.keep_data = keep_data
        self.name = name
        self.level = level
        self.devices = devices or []
        self.spares = spares or []
        self.metadata = metadata

    def add_device(self, device):
        if device in self.devices or device in self.spares:
            raise errors.MDDeviceDuplicationError(
                'Error while attaching device to md: '
                'device %s is already attached' % device)
        self.devices.append(device)

    def add_spare(self, device):
        if device in self.devices or device in self.spares:
            raise errors.MDDeviceDuplicationError(
                'Error while attaching device to md: '
                'device %s is already attached' % device)
        self.spares.append(device)

    def to_dict(self):
        return {
            'name': self.name,
            'level': self.level,
            'devices': self.devices,
            'spares': self.spares,
            'keep_data': self.keep_data,
            'metadata': self.metadata,
        }
