import time

from common.utils import SkyflowMessages
from common.utils.logger import log_info
from common.utils.enums.detect import DetectRunStatus

from ._constants import (
    DEFAULT_WAIT_TIME_SECONDS,
    DEFAULT_MAX_ATTEMPTS,
    INITIAL_DELAY_SECONDS,
    MAX_DELAY_SECONDS,
    DELAY_MULTIPLIER,
)
from ._models import GetRunResponse

_TERMINAL_STATUSES = (DetectRunStatus.SUCCESS, DetectRunStatus.FAILED, DetectRunStatus.UNKNOWN)


def _effective_wait_time(poll_options):
    return DEFAULT_WAIT_TIME_SECONDS if poll_options.wait_time is None else poll_options.wait_time


def _effective_max_attempts(poll_options):
    return DEFAULT_MAX_ATTEMPTS if poll_options.max_attempts is None else poll_options.max_attempts


def poll_run(run_id, poll_options, fetcher, logger=None, sleeper=time.sleep):
    wait_time = _effective_wait_time(poll_options)
    max_attempts = _effective_max_attempts(poll_options)
    log_info(SkyflowMessages.Info.POLL_RUN_STARTED.value.format(run_id, wait_time, max_attempts), logger)

    elapsed_seconds = 0
    delay_seconds = INITIAL_DELAY_SECONDS
    attempts = 0
    while True:
        run = fetcher(run_id)
        attempts += 1
        if run is None or run.status is None:
            run = GetRunResponse(
                run_id=run_id,
                status=DetectRunStatus.UNKNOWN,
                output_type=None,
                output=[],
                metrics=None,
                message=None,
            )
        if run.status in _TERMINAL_STATUSES:
            log_info(SkyflowMessages.Info.POLL_RUN_TERMINAL.value, logger)
            return run
        if attempts >= max_attempts or elapsed_seconds >= wait_time:
            log_info(SkyflowMessages.Info.POLL_RUN_BUDGET_EXHAUSTED.value, logger)
            return run
        sleep_seconds = min(delay_seconds, wait_time - elapsed_seconds)
        sleeper(sleep_seconds)
        elapsed_seconds += sleep_seconds
        delay_seconds = min(delay_seconds * DELAY_MULTIPLIER, MAX_DELAY_SECONDS)
