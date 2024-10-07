import requests

from samples.v2sample import response
from skyflow.utils import construct_invoke_connection_request
from skyflow.vault.connection import InvokeConnectionRequest, InvokeConnectionResponse


class Connection:

    def __init__(self, vault_client):
        self.__vault_client = vault_client

    def invoke(self, request: InvokeConnectionRequest):
        #generate token

        session = requests.Session()
        config = self.__vault_client.get_config()
        bearer_token = self.__vault_client.get_bearer_token(config.get("credentials"))
        connection_url = config.get("connection_url")
        request = construct_invoke_connection_request(request, connection_url)
        request.headers['x-skyflow-authorization'] = f"Bearer ${bearer_token}"

        response = session.send(request)
        session.close()
        return InvokeConnectionResponse.parse_invoke_connection_response(response)