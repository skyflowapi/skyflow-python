from enum import Enum

class SkyflowErrorCodes(Enum):
    INVALID_INPUT = 400
    SERVER_ERROR = 500

class SkyflowErrorMessages(Enum):
    FILE_NOT_FOUND = "File at %s not found"
    FILE_INVALID_JSON = "File at %s is not in JSON format"
    INVALID_URL = "Given url '%s' is invalid"

    MISSING_PRIVATE_KEY = "Unable to read Private key"
    MISSING_CLIENT_ID = "Unable to read Client ID"
    MISSING_KEY_ID = "Unable to read Key ID"
    MISSING_TOKEN_URI = "Unable to read Token URI"

    JWT_INVALID_FORMAT = "Private key is not in correct format"
    MISSING_ACCESS_TOKEN = "accessToken not present in response"
    MISSING_TOKEN_TYPE = "tokenType not present in response"

    # vault
    RECORDS_KEY_ERROR = "Records key is missing from payload"


class SkyflowError(Exception):
    def __init__(self, code, message="An Error occured") -> None:
        if type(code) is SkyflowErrorCodes:
            self.code = code.value
        else:
            self.code = code
        if type(message) is SkyflowErrorMessages:
            self.message = message.value
        else:
            self.message = message
        super().__init__(self.message)

