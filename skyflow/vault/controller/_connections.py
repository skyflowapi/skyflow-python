import json
import requests
from skyflow.error import SkyflowError
from skyflow.utils import construct_invoke_connection_request, SkyflowMessages, get_metrics, \
    parse_invoke_connection_response
from skyflow.utils.logger import log_info, log_error_log
from skyflow.vault.connection import InvokeConnectionRequest
from skyflow.utils.constants import SKY_META_DATA_HEADER, SKYFLOW, HttpHeader
from skyflow.utils import get_credentials


class Connection:
    def __init__(self, vault_client):
        self.__vault_client = vault_client

    def invoke(self, request: InvokeConnectionRequest):
        log_info(SkyflowMessages.Info.VALIDATING_INVOKE_CONNECTION_REQUEST.value, self.__vault_client.get_logger())
        config = self.__vault_client.get_config()
        connection_url = config.get("connection_url")
        invoke_connection_request = construct_invoke_connection_request(request, connection_url, self.__vault_client.get_logger())
        log_info(SkyflowMessages.Info.INVOKE_CONNECTION_REQUEST_RESOLVED.value, self.__vault_client.get_logger())
                
        credentials = get_credentials(config.get("credentials"), self.__vault_client.get_common_skyflow_credentials(), self.__vault_client.get_logger())

        bearer_token = self.__vault_client.get_bearer_token(credentials)

        session = requests.Session()

        if not HttpHeader.X_SKYFLOW_AUTHORIZATION_HEADER.lower() in invoke_connection_request.headers:
            invoke_connection_request.headers[SKYFLOW.X_SKYFLOW_AUTHORIZATION] = bearer_token

        invoke_connection_request.headers[SKY_META_DATA_HEADER] = json.dumps(get_metrics())

        log_info(SkyflowMessages.Info.INVOKE_CONNECTION_TRIGGERED.value, self.__vault_client.get_logger())

        try:
            response = session.send(invoke_connection_request)
            session.close()
            invoke_connection_response = parse_invoke_connection_response(response)
            return invoke_connection_response

        except Exception as e:
            log_error_log(SkyflowMessages.ErrorLogs.INVOKE_CONNECTION_REQUEST_REJECTED.value, self.__vault_client.get_logger())
            if isinstance(e, SkyflowError): raise e
            raise SkyflowError(SkyflowMessages.Error.INVOKE_CONNECTION_FAILED.value,
                               SkyflowMessages.ErrorCodes.SERVER_ERROR.value)