from typing import Callable, Optional

from ._request_context import RequestContext


class DeleteOptions:
    def __init__(self, interceptor: Optional[Callable[[RequestContext], None]] = None):
        self.interceptor = interceptor
