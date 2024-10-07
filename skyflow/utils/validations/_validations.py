from skyflow.error import SkyflowError


def validate_vault_config(config):
    #validate vault configuration
    return True

def validate_connection_config(config):
    #validate connection configuration
    return True

def validate_insert_request(request):
    if not request.table_name:
        raise SkyflowError("Table name is required.")
    if not isinstance(request.values, list) or len(request.values) == 0:
        raise SkyflowError("At least one record must be provided.")

def validate_credentials(credentials):
    keys_to_check = ['path', 'token', 'credentials_string']
    present_keys = [key for key in keys_to_check if credentials.get(key)]
    if len(present_keys) > 1:
        raise SkyflowError(
            f"Only one of 'path', 'token', or 'credentials_string' should be present. Found multiple: {present_keys}")