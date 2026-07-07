import platform
import sys

from common.errors import SkyflowError
from common.utils import SkyflowMessages as CommonMessages
from common.utils.constants import PROTOCOL, SdkMetricsKey, SdkPrefix
from common.utils.enums import Env
from ._version import SDK_VERSION
from .enums import EnvUrls

_CACHED_METRICS: dict = {}

invalid_input_error_code = CommonMessages.ErrorCodes.INVALID_INPUT.value


def get_vault_url(cluster_id, env, vault_id, logger=None):
    """Mirrors common.utils.get_vault_url with v3's own EnvUrls (different subdomain)."""
    if not cluster_id or not isinstance(cluster_id, str) or not cluster_id.strip():
        raise SkyflowError(CommonMessages.Error.INVALID_CLUSTER_ID.value.format(vault_id), invalid_input_error_code)

    if env not in Env:
        raise SkyflowError(CommonMessages.Error.INVALID_ENV.value.format(vault_id), invalid_input_error_code)

    base_url = EnvUrls[env.name].value

    return f"{PROTOCOL}://{cluster_id}.{base_url}"


def get_metrics():
    if _CACHED_METRICS:
        return _CACHED_METRICS

    try:
        sdk_client_device_model = platform.node()
    except Exception:
        sdk_client_device_model = ""

    try:
        sdk_client_os_details = sys.platform
    except Exception:
        sdk_client_os_details = ""

    try:
        sdk_runtime_details = sys.version
    except Exception:
        sdk_runtime_details = ""

    _CACHED_METRICS.update({
        SdkMetricsKey.SDK_NAME_VERSION: SdkPrefix.SKYFLOW_PYTHON + SDK_VERSION,
        SdkMetricsKey.SDK_CLIENT_DEVICE_MODEL: sdk_client_device_model,
        SdkMetricsKey.SDK_CLIENT_OS_DETAILS: sdk_client_os_details,
        SdkMetricsKey.SDK_RUNTIME_DETAILS: SdkPrefix.PYTHON_RUNTIME + sdk_runtime_details,
    })
    return _CACHED_METRICS
