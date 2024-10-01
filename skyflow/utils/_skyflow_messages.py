from enum import Enum

class SkyflowMessages:
    class Error(Enum):
        ERROR_MESSAGE = "ERROR MESSAGE"

    class Info(Enum):
        INFO_MESSAGE = "INFO MESSAGE"

    class Warning(Enum):
        WARNING_MESSAGE = "WARNING MESSAGE"
