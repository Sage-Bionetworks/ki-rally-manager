# Copyright 2018-present, Bill & Melinda Gates Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

import synapseclient

from .param_store import ParamStore

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

class Synapse:

    _synapse_client = None

    ADMIN_PERMS = [
        'UPDATE',
        'DELETE',
        'CHANGE_PERMISSIONS',
        'CHANGE_SETTINGS',
        'CREATE',
        'DOWNLOAD',
        'READ',
        'MODERATE'
    ]

    CAN_EDIT_AND_DELETE_PERMS = [
        'DOWNLOAD',
        'UPDATE',
        'CREATE',
        'DELETE',
        'READ'
    ]

    CAN_EDIT_PERMS = [
        'DOWNLOAD',
        'UPDATE',
        'CREATE',
        'READ'
    ]

    CAN_DOWNLOAD_PERMS = [
        'DOWNLOAD',
        'READ'
    ]

    CAN_VIEW_PERMS = [
        'READ'
    ]

    @classmethod
    def client(cls, *args, **kwargs):
        """
        Gets a logged in instance of the synapseclient.
        """
        if cls._synapse_client is None:
            LOGGER.debug("Getting a new Synapse client.")
            cls._synapse_client = synapseclient.Synapse(*args, **kwargs)
            try:
                cls._synapse_client.login(silent=True)
            except Exception as e:
                syn_user = ParamStore.SYNAPSE_USERNAME()
                syn_pass = ParamStore.SYNAPSE_PASSWORD()
                cls._synapse_client.login(syn_user, syn_pass, silent=True)

        LOGGER.debug("Already have a Synapse client, returning it.")
        return cls._synapse_client
