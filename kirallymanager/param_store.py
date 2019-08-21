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

import os
import boto3
import logging
import json


class ParamStore:

    @classmethod
    def get(cls, key, default=None):
        """
        Tries to get a value from the OS then SSM otherwise it returns the default value.
        """
        # Try to get the value from the local environment.
        result = cls._get_from_os(key)
        if result != None:
            return result

        # Try to get the value from SSM.
        result = cls._get_from_ssm(key)
        if result != None:
            return result

        return default

    @classmethod
    def _get_from_os(cls, key):
        """
        Gets a value from the OS.
        """
        return os.environ.get(key)

    @classmethod
    def _get_from_ssm(cls, key):
        """
        Gets a value from SSM.
        """
        client = boto3.client('ssm')
        ssm_key = cls._build_ssm_key(key)
        result = None

        try:
            get_response = client.get_parameter(Name=ssm_key, WithDecryption=True)
            result = get_response.get('Parameter').get('Value')
        except client.exceptions.ParameterNotFound:
            logging.exception('SSM Parameter Not Found: {}'.format(ssm_key))

        return result

    @classmethod
    def _set_ssm_parameter(cls, key, value, type='SecureString'):
        """
        Sets an SSM key/value.
        """
        client = boto3.client('ssm')
        ssm_key = cls._build_ssm_key(key)
        return client.put_parameter(Name=ssm_key, Value=value, Type=type, Overwrite=True)

    @classmethod
    def _build_ssm_key(cls, key):
        """
        Builds a SSM key in the format for service_name/service_stage/key.
        """
        service_name = cls._get_from_os('SERVICE_NAME')
        service_stage = cls._get_from_os('SERVICE_STAGE')

        return '/{0}/{1}/{2}'.format(service_name, service_stage, key)

    """
    ===============================================================================================
    Getter Methods.
    ===============================================================================================
    """

    @classmethod
    def SERVICE_NAME(cls, default=None):
        return cls.get('SERVICE_NAME', default)

    @classmethod
    def SERVICE_STAGE(cls, default=None):
        return cls.get('SERVICE_STAGE', default)

    @classmethod
    def LOG_LEVEL(cls, default=None):
        return cls.get('LOG_LEVEL', default)

    @classmethod
    def SYNAPSE_USERNAME(cls, default=None):
        return cls.get('SYNAPSE_USERNAME', default)

    @classmethod
    def SYNAPSE_PASSWORD(cls, default=None):
        return cls.get('SYNAPSE_PASSWORD', default)

    @classmethod
    def JWT_SECRET(cls, default=None):
        """
        Secret key used to encode JWTs.
        """
        return cls.get('JWT_SECRET', default)

    @classmethod
    def JWT_API_KEYS(cls, default=None):
        """
        String of comma separated keys that are used for API access.
        """
        return cls.get('JWT_API_KEYS', default)

    @classmethod
    def SLIDE_DECKS_BUCKET_NAME(cls, default=None):
        return cls.get('SLIDE_DECKS_BUCKET_NAME', default)

    @classmethod
    def SLIDE_DECKS_URL_EXPIRES_IN_SECONDS(cls, default=300):
        return int(cls.get('SLIDE_DECKS_URL_EXPIRES_IN_SECONDS', default))
