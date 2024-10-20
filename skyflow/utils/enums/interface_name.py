from enum import Enum

class InterfaceName(Enum):
    CLIENT = "client"
    INSERT = "client.insert"
    DETOKENIZE = "client.detokenize"
    GET_BY_ID = "client.get_by_id"
    GET = "client.get"
    UPDATE = "client.update"
    INVOKE_CONNECTION = "client.invoke_connection"
    QUERY = "client.query"
    GENERATE_BEARER_TOKEN = "service_account.generate_bearer_token"
    IS_TOKEN_VALID = "service_account.isTokenValid"
    IS_EXPIRED = "service_account.is_expired"
    DELETE = "client.delete"