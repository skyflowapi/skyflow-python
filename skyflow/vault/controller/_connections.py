import json
import requests
from skyflow.error import SkyflowError
from skyflow.utils import construct_invoke_connection_request, SkyflowMessages, get_metrics, \
    parse_invoke_connection_response
from skyflow.utils.logger import log_info, log_error_log
from skyflow.vault.connection import InvokeConnectionRequest


class Connection:
    def __init__(self, vault_client):
        self.__vault_client = vault_client

    def invoke(self, request: InvokeConnectionRequest):
        session = requests.Session()

        config = self.__vault_client.get_config()
        bearer_token = self.__vault_client.get_bearer_token(config.get("credentials"))

        connection_url = config.get("connection_url")
        log_info(SkyflowMessages.Info.VALIDATING_INVOKE_CONNECTION_REQUEST.value, self.__vault_client.get_logger())
        invoke_connection_request = construct_invoke_connection_request(request, connection_url, self.__vault_client.get_logger())
        log_info(SkyflowMessages.Info.INVOKE_CONNECTION_REQUEST_RESOLVED.value, self.__vault_client.get_logger())

        if not 'X-Skyflow-Authorization'.lower() in invoke_connection_request.headers:
            invoke_connection_request.headers['x-skyflow-authorization'] = bearer_token

        invoke_connection_request.headers['sky-metadata'] = json.dumps(get_metrics())

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