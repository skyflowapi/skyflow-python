import os
from abc import ABC, abstractmethod

import dotenv
from dotenv import load_dotenv

from common.utils import SkyflowMessages
from common.utils.logger import log_warn

DEFAULT_INSERT_BATCH_SIZE = 50
MAX_INSERT_BATCH_SIZE = 1000


class VaultController(ABC):
    """Shared invocation-flow base for vault operations, mirroring Java's VaultController
    interface shape. Every method is abstract with no shared body -- each variant's concrete
    controller provides its own override (a stub is fine). Only _get_insert_batch_size/
    _run_batches below are actually shared, reusable logic."""

    def __init__(self, vault_client):
        self._vault_client = vault_client

    @abstractmethod
    def insert(self, request):
        raise NotImplementedError

    @abstractmethod
    def get(self, request):
        raise NotImplementedError

    @abstractmethod
    def update(self, request):
        raise NotImplementedError

    @abstractmethod
    def delete(self, request):
        raise NotImplementedError

    @abstractmethod
    def query(self, request):
        raise NotImplementedError

    @abstractmethod
    def detokenize(self, request):
        raise NotImplementedError

    @staticmethod
    def _get_insert_batch_size(logger=None):
        """Reads INSERT_BATCH_SIZE (env var or .env), defaulting to DEFAULT_INSERT_BATCH_SIZE
        and clamping to MAX_INSERT_BATCH_SIZE."""
        dotenv_path = dotenv.find_dotenv(usecwd=True)
        if dotenv_path:
            load_dotenv(dotenv_path)
        raw = os.getenv("INSERT_BATCH_SIZE")
        if raw is None:
            return DEFAULT_INSERT_BATCH_SIZE

        try:
            value = int(raw)
        except ValueError:
            log_warn(SkyflowMessages.Warning.INVALID_BATCH_SIZE_PROVIDED.value, logger)
            return DEFAULT_INSERT_BATCH_SIZE

        if value <= 0:
            log_warn(SkyflowMessages.Warning.INVALID_BATCH_SIZE_PROVIDED.value, logger)
            return DEFAULT_INSERT_BATCH_SIZE

        if value > MAX_INSERT_BATCH_SIZE:
            log_warn(SkyflowMessages.Warning.BATCH_SIZE_EXCEEDS_MAX_LIMIT.value, logger)
            return MAX_INSERT_BATCH_SIZE

        return value

    @staticmethod
    def _run_batches(items, batch_size, send_batch_fn):
        """Fixed-size, order-preserving chunking + sequential dispatch, no concurrency.
        send_batch_fn(batch, start_index) -> (successes, errors); a failing batch doesn't abort
        the rest."""
        all_successes, all_errors = [], []
        for start in range(0, len(items), batch_size):
            successes, errors = send_batch_fn(items[start:start + batch_size], start)
            all_successes.extend(successes)
            all_errors.extend(errors)
        return all_successes, all_errors
