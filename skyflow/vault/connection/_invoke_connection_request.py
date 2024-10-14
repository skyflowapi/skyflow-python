class InvokeConnectionRequest:
    def __init__(self, method, params, body):
        self.method = method
        self.params = params
        self.body = body