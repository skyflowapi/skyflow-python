from enum import Enum


class CustomHeaderKey(Enum):
    SKYFLOW_ACCOUNT_ID = "x-skyflow-account-id"
    SKYFLOW_ACCOUNT_NAME = "x-skyflow-account-name"
    REQUEST_ID_HEADER = "x-request-id"

    def __str__(self):
        return self.value
