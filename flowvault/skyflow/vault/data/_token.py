class Token:
    def __init__(self, token: str = None, token_group_name: str = None, path: str = None):
        self.token = token
        self.token_group_name = token_group_name
        self.path = path

    def __repr__(self):
        return f"Token(token={self.token}, token_group_name={self.token_group_name}, path={self.path})"
