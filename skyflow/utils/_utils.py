
import os
from urllib.parse import urlparse

from skyflow.generated.rest import RedactionEnumREDACTION
from skyflow.utils.enums import Env
import skyflow.generated.rest as vault_client

def get_credentials(config_level_creds = None, common_skyflow_creds = None):
    env_skyflow_credentials = os.getenv("SKYFLOW_CREDENTIALS")
    if config_level_creds:
        return config_level_creds
    if common_skyflow_creds:
        return common_skyflow_creds
    if env_skyflow_credentials:
        return env_skyflow_credentials
    else:
        raise Exception("Invalid Credentials")
    pass


def get_vault_url(cluster_id, env):
    if env == Env.PROD:
        return f"http://{cluster_id}.vault.skyflowapis.com"
    elif env == Env.SANDBOX:
        return f"https://{cluster_id}.vault.skyflowapis-preview.com"
    elif env == Env.DEV:
        return f"https://{cluster_id}.vault.skyflowapis.dev"
    else:
        return f"https://{cluster_id}.vault.skyflowapis.com"

def get_client_configuration(vault_url, bearer_token):
        return vault_client.Configuration(
            host=vault_url,
            api_key_prefix="Bearer",
            api_key=bearer_token
        )

def get_base_url(url):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url

def format_scope(scopes):
    if not scopes:
        return None
    return " ".join([f"role:{scope}" for scope in scopes])


def get_redaction_type(redaction_type):
    if redaction_type == "plain-text":
        return RedactionEnumREDACTION.PLAIN_TEXT

