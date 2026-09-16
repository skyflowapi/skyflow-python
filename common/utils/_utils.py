import os
import re

import dotenv
from dotenv import load_dotenv

from common.errors import SkyflowError
from . import SkyflowMessages
from .constants import PROTOCOL, ApiKey
from .enums import Env, EnvUrls
from .logger import log_error_log

invalid_input_error_code = SkyflowMessages.ErrorCodes.INVALID_INPUT.value


def get_credentials(config_level_creds=None, common_skyflow_creds=None, logger=None):
    if config_level_creds is not None:
        return config_level_creds
    if common_skyflow_creds is not None:
        return common_skyflow_creds
    dotenv_path = dotenv.find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path)
    env_skyflow_credentials = os.getenv("SKYFLOW_CREDENTIALS")
    if env_skyflow_credentials:
        env_creds = env_skyflow_credentials.strip().replace('\n', '\\n')
        return {'credentials_string': env_creds}
    raise SkyflowError(SkyflowMessages.Error.INVALID_CREDENTIALS.value, invalid_input_error_code)


def validate_api_key(api_key: str, logger=None) -> bool:
    if len(api_key) != ApiKey.LENGTH:
        log_error_log(SkyflowMessages.ErrorLogs.INVALID_API_KEY.value, logger=logger)
        return False
    api_key_pattern = re.compile(r'^sky-[a-zA-Z0-9]{5}-[a-fA-F0-9]{32}$')

    return bool(api_key_pattern.match(api_key))


def get_vault_url(cluster_id, env, vault_id, logger=None):
    if not cluster_id or not isinstance(cluster_id, str) or not cluster_id.strip():
        raise SkyflowError(SkyflowMessages.Error.INVALID_CLUSTER_ID.value.format(vault_id), invalid_input_error_code)

    if env not in Env:
        raise SkyflowError(SkyflowMessages.Error.INVALID_ENV.value.format(vault_id), invalid_input_error_code)

    base_url = EnvUrls[env.name].value
    protocol = PROTOCOL

    return f"{protocol}://{cluster_id}.{base_url}"
