from typing import List

from common.vault.data import BaseGetTokensRequest
from ._get_tokens_request_record import GetTokensRequestRecord


class GetTokensRequest(BaseGetTokensRequest):
    def __init__(self, records: List[GetTokensRequestRecord]):
        super().__init__(records)
