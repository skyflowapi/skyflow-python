class InvokeConnectionRequest:
    def __init__(self,
                 method,
                 body = None,
                 path_params = None,
                 query_params = None,
                 headers = None):
        self.body = body if body is not None else {}
        self.method = method
        self.path_params = path_params if path_params is not None else {}
        self.query_params = query_params if query_params is not None else {}
        self.headers = headers if headers is not None else {}