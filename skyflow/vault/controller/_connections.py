import json

import requests
from skyflow.error import SkyflowError
from skyflow.utils import construct_invoke_connection_request, log_info, SkyflowMessages, get_metrics, log_error
from skyflow.vault.connection import InvokeConnectionRequest, InvokeConnectionResponse


class Connection:
    def __init__(self, vault_client):
        self.__vault_client = vault_client
        self.logger = self.__vault_client.get_logger()

    def invoke(self, request: InvokeConnectionRequest):
        interface = SkyflowMessages.InterfaceName.INVOKE_CONNECTION.value
        log_info(self.logger, SkyflowMessages.Info.INVOKE_CONNECTION_TRIGGERED, interface)

        session = requests.Session()

        config = self.__vault_client.get_config()
        bearer_token = self.__vault_client.get_bearer_token(config.get("credentials"))

        connection_url = config.get("connection_url")
        invoke_connection_request = construct_invoke_connection_request(request, connection_url, self.logger)

        if not 'X-Skyflow-Authorization'.lower() in invoke_connection_request.headers:
            invoke_connection_request.headers['x-skyflow-authorization'] = f"Bearer ${bearer_token}"

        invoke_connection_request.headers['sky-metadata'] = json.dumps(get_metrics())

        log_info(self.logger, SkyflowMessages.Info.INVOKE_CONNECTION_TRIGGERED, interface)

        try:
            response = session.send(invoke_connection_request)
            session.close()
            invoke_connection_response = InvokeConnectionResponse()
            return invoke_connection_response.parse_invoke_connection_response(response)
        except:
            raise SkyflowError(SkyflowMessages.Error.INVOKE_CONNECTION_FAILED.value, SkyflowMessages.ErrorCodes.SERVER_ERROR, logger = self.logger, logger_method=log_error)