OPTIONAL_TOKEN='token'
PROTOCOL='https'
SKY_META_DATA_HEADER='sky-metadata'

class SKYFLOW:
    SKYFLOW_ID = 'skyflowId'
    X_SKYFLOW_AUTHORIZATION = 'x-skyflow-authorization'


class HttpHeader:
    CONTENT_TYPE = 'Content-Type'
    CONTENT_TYPE_LOWERCASE = 'content-type'
    X_REQUEST_ID = 'x-request-id'
    ERROR_FROM_CLIENT = 'error-from-client'
    AUTHORIZATION = 'Authorization'


class HttpStatusCode:
    OK = 200
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500


class ContentType:
    APPLICATION_JSON = 'application/json'
    APPLICATION_X_WWW_FORM_URLENCODED = 'application/x-www-form-urlencoded'
    TEXT_PLAIN = 'text/plain'


class DetectStatus:
    IN_PROGRESS = 'IN_PROGRESS'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    UNKNOWN = 'UNKNOWN'


class FileExtension:
    JSON = 'json'
    MP3 = 'mp3'
    WAV = 'wav'
    PDF = 'pdf'
    TXT = 'txt'
    DOC = 'doc'
    DOCX = 'docx'
    JPG = 'jpg'
    JPEG = 'jpeg'
    PNG = 'png'
    BMP = 'bmp'
    TIF = 'tif'
    TIFF = 'tiff'
    PPT = 'ppt'
    PPTX = 'pptx'
    CSV = 'csv'
    XLS = 'xls'
    XLSX = 'xlsx'
    XML = 'xml'


class FileProcessing:
    PROCESSED_PREFIX = 'processed-'
    DEIDENTIFIED_PREFIX = 'deidentified.'
    ENTITIES = 'entities'


class EncodingType:
    UTF8 = 'utf8'
    UTF_8 = 'utf-8'
    BASE64 = 'base64'
    BINARY = 'binary'


class JWT:
    ALGORITHM_RS256 = 'RS256'
    GRANT_TYPE_JWT_BEARER = 'urn:ietf:params:oauth:grant-type:jwt-bearer'
    ISSUER_SDK = 'sdk'
    SIGNED_TOKEN_PREFIX = 'signed_token_'
    ROLE_PREFIX = 'role:'


class ApiKey:
    SKY_PREFIX = 'sky-'
    LENGTH = 42


class UrlProtocol:
    HTTPS = 'https'
    HTTP = 'http'


class BooleanString:
    TRUE = 'true'
    FALSE = 'false'


class ResponseField:
    STATUS = 'Status'
    BODY = 'Body'
    RECORDS = 'records'
    TOKENS = 'tokens'
    ERROR = 'error'
    SKYFLOW_ID = 'skyflow_id'
    REQUEST_INDEX = 'request_index'
    REQUEST_ID = 'request_id'
    HTTP_CODE = 'http_code'
    HTTP_STATUS = 'http_status'
    GRPC_CODE = 'grpc_code'
    DETAILS = 'details'
    MESSAGE = 'message'
    ERROR_FROM_CLIENT = 'error_from_client'
    TOKEN = 'token'
    VALUE = 'value'
    TYPE = 'type'
    TOKENIZED_DATA = 'tokenized_data'
    SIGNED_TOKEN = 'signed_token'


class CredentialField:
    PRIVATE_KEY = 'privateKey'
    CLIENT_ID = 'clientID'
    KEY_ID = 'keyID'
    TOKEN_URI = 'tokenURI'
    CREDENTIALS_STRING = 'credentials_string'
    API_KEY = 'api_key'
    TOKEN = 'token'
    PATH = 'path'


class JwtField:
    ISS = 'iss'
    KEY = 'key'
    AUD = 'aud'
    SUB = 'sub'
    EXP = 'exp'
    CTX = 'ctx'
    TOK = 'tok'
    IAT = 'iat'


class OptionField:
    ROLE_IDS = 'role_ids'
    DATA_TOKENS = 'data_tokens'
    TIME_TO_LIVE = 'time_to_live'
    ROLES = 'roles'
    CTX = 'ctx'
    VAULT_ID = 'vault_id'
    CONNECTION_ID = 'connection_id'
    CONNECTION_URL = 'connection_url'
    VAULT_CLIENT = 'vault_client'
    VAULT_CONTROLLER = 'vault_controller'
    DETECT_CONTROLLER = 'detect_controller'
    CONTROLLER = 'controller'
    VERIFY_SIGNATURE = 'verify_signature'
    VERIFY_AUD = 'verify_aud'


class ConfigField:
    CREDENTIALS = 'credentials'
    CLUSTER_ID = 'cluster_id'
    ENV = 'env'
    VAULT_ID = 'vault_id'


class RequestParameter:
    VALUE = 'value'
    COLUMN_GROUP = 'column_group'
    REDACTION = 'redaction'

