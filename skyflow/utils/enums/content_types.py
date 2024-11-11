from enum import Enum

class ContentType(Enum):
    JSON = 'application/json'
    PLAINTEXT = 'text/plain'
    XML = 'text/xml'
    URLENCODED = 'application/x-www-form-urlencoded'
    FORMDATA = 'multipart/form-data'