from typing import Callable, Optional

from ._request_context import RequestContext


class BulkDetokenizeOptions:
    def __init__(self, interceptor: Optional[Callable[[RequestContext], None]] = None):
        self.interceptor = interceptor
