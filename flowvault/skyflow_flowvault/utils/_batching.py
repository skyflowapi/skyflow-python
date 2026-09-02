import math
import os

from dotenv import dotenv_values, find_dotenv

from common.utils.logger import log_warn
from skyflow_flowvault.utils._skyflow_messages import SkyflowMessages

DEFAULT_BATCH_SIZE = 50
MAX_BATCH_SIZE = 1000
DEFAULT_CONCURRENCY = 1
MAX_CONCURRENCY = 10

INSERT_BATCH_SIZE_KEY = "INSERT_BATCH_SIZE"
INSERT_CONCURRENCY_LIMIT_KEY = "INSERT_CONCURRENCY_LIMIT"
DETOKENIZE_BATCH_SIZE_KEY = "DETOKENIZE_BATCH_SIZE"
DETOKENIZE_CONCURRENCY_LIMIT_KEY = "DETOKENIZE_CONCURRENCY_LIMIT"


def _resolve_setting(key):
    value = os.getenv(key)
    if value is None:
        try:
            path = find_dotenv(usecwd=True)
            if path:
                value = dotenv_values(path).get(key)
        except Exception:
            value = None
    return value


def _resolve_batch_size(batch_env_key, logger):
    raw = _resolve_setting(batch_env_key)
    if raw is None:
        return DEFAULT_BATCH_SIZE
    try:
        parsed = int(raw)
    except (ValueError, TypeError):
        log_warn(SkyflowMessages.Error.INVALID_BATCH_SIZE.value, logger)
        return DEFAULT_BATCH_SIZE
    if parsed > MAX_BATCH_SIZE:
        log_warn(SkyflowMessages.Error.BATCH_SIZE_EXCEEDS_MAX.value, logger)
    capped = min(parsed, MAX_BATCH_SIZE)
    if capped > 0:
        return capped
    log_warn(SkyflowMessages.Error.INVALID_BATCH_SIZE.value, logger)
    return DEFAULT_BATCH_SIZE


def _resolve_concurrency(conc_env_key, item_count, batch_size, logger):
    batch_count = max(1, math.ceil(item_count / batch_size)) if batch_size > 0 else 1
    raw = _resolve_setting(conc_env_key)
    if raw is None:
        return min(DEFAULT_CONCURRENCY, batch_count)
    try:
        parsed = int(raw)
    except (ValueError, TypeError):
        log_warn(SkyflowMessages.Error.INVALID_CONCURRENCY_LIMIT.value, logger)
        return min(DEFAULT_CONCURRENCY, batch_count)
    if parsed > MAX_CONCURRENCY:
        log_warn(SkyflowMessages.Error.CONCURRENCY_EXCEEDS_MAX.value, logger)
    capped = min(parsed, MAX_CONCURRENCY)
    if capped > 0:
        return min(capped, batch_count)
    log_warn(SkyflowMessages.Error.INVALID_CONCURRENCY_LIMIT.value, logger)
    return min(DEFAULT_CONCURRENCY, batch_count)


def resolve_batch_config(batch_env_key, conc_env_key, item_count, logger=None):
    batch_size = _resolve_batch_size(batch_env_key, logger)
    concurrency = _resolve_concurrency(conc_env_key, item_count, batch_size, logger)
    return batch_size, concurrency


def create_batches(items, batch_size):
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
