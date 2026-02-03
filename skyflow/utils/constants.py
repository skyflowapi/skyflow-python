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
    X_SKYFLOW_AUTHORIZATION_HEADER = 'X-Skyflow-Authorization'


class HttpStatusCode:
    OK = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
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
    CONTEXT = 'context'
    ROLES = 'roles'


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


class FileUploadField:
    TABLE = 'table'
    SKYFLOW_ID = 'skyflow_id'
    COLUMN_NAME = 'column_name'
    FILE_PATH = 'file_path'
    BASE64 = 'base64'
    FILE_OBJECT = 'file_object'
    FILE_NAME = 'file_name'
    FILE = 'file'
    NAME = 'name'


class DeidentifyFileRequestField:
    ENTITIES = 'entities'
    ALLOW_REGEX_LIST = 'allow_regex_list'
    RESTRICT_REGEX_LIST = 'restrict_regex_list'
    OUTPUT_PROCESSED_IMAGE = 'output_processed_image'
    OUTPUT_OCR_TEXT = 'output_ocr_text'
    MASKING_METHOD = 'masking_method'
    PIXEL_DENSITY = 'pixel_density'
    MAX_RESOLUTION = 'max_resolution'
    OUTPUT_PROCESSED_AUDIO = 'output_processed_audio'
    OUTPUT_TRANSCRIPTION = 'output_transcription'
    BLEEP = 'bleep'
    OUTPUT_DIRECTORY = 'output_directory'
    WAIT_TIME = 'wait_time'


class DeidentifyField:
    TEXT = 'text'
    ENTITY_TYPES = 'entity_types'
    TOKEN_TYPE = 'token_type'
    ALLOW_REGEX = 'allow_regex'
    RESTRICT_REGEX = 'restrict_regex'
    TRANSFORMATIONS = 'transformations'
    FORMAT = 'format'
    OUTPUT = 'output'
    STATUS = 'status'
    RUN_ID = 'run_id'
    WORD_CHARACTER_COUNT = 'word_character_count'
    WORD_COUNT = 'word_count'
    CHARACTER_COUNT = 'character_count'
    SIZE = 'size'
    DURATION = 'duration'
    PAGES = 'pages'
    SLIDES = 'slides'
    PROCESSED_FILE = 'processed_file'
    PROCESSED_FILE_TYPE = 'processed_file_type'
    PROCESSED_FILE_EXTENSION = 'processed_file_extension'
    REDACTED_FILE = 'redacted_file'
    SHIFT_DATES = 'shift_dates'
    DEFAULT = 'default'
    ENTITY_UNQ_COUNTER = 'entity_unq_counter'
    ENTITY_UNIQUE_COUNTER = 'entity_unique_counter'
    ENTITY_ONLY = 'entity_only'
    ENTITIES = 'entities'
    MAX_DAYS = 'max_days'
    MIN_DAYS = 'min_days'
    MAX = 'max'
    MIN = 'min'
    FILE = 'file'
    TYPE = 'type'
    EXTENSION = 'extension'
    IN_PROGRESS = 'IN_PROGRESS'
    REQUEST_OPTIONS = 'request_options'
    BLEEP_GAIN = 'bleep_gain'
    BLEEP_FREQUENCY = 'bleep_frequency'
    BLEEP_START_PADDING = 'bleep_start_padding'
    BLEEP_STOP_PADDING = 'bleep_stop_padding'
    DENSITY = 'density'
    TOKEN_FORMAT = 'token_format'
    PROCESSED_FILE_RESPONSE_KEY = 'processedFile'
    PROCESSED_FILE_TYPE_RESPONSE_KEY = 'processedFileType'
    PROCESSED_FILE_EXTENSION_RESPONSE_KEY = 'processedFileExtension'


class RequestOperation:
    INSERT = 'INSERT'
    DELETE = 'DELETE'
    GET = 'GET'
    UPDATE = 'UPDATE'
    QUERY = 'QUERY'
    TOKENIZE = 'TOKENIZE'
    DETOKENIZE = 'DETOKENIZE'
    FILE_UPLOAD = 'FILE_UPLOAD'


class ConfigType:
    VAULT = 'vault'
    CONNECTION = 'connection'


class SqlCommand:
    SELECT = 'SELECT'


class SdkPrefix:
    SKYFLOW_PYTHON = 'skyflow-python@'
    PYTHON_RUNTIME = 'Python '


class SdkMetricsKey:
    SDK_NAME_VERSION = 'sdk_name_version'
    SDK_CLIENT_DEVICE_MODEL = 'sdk_client_device_model'
    SDK_CLIENT_OS_DETAILS = 'sdk_client_os_details'
    SDK_RUNTIME_DETAILS = 'sdk_runtime_details'


class ErrorDefaults:
    UNKNOWN_REQUEST_ID = 'unknown-request-id'
