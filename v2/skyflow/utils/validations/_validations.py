def get_credentials(config_level_creds, common_skyflow_creds, env_skyflow_creds):
    if config_level_creds:
        return config_level_creds
    if common_skyflow_creds:
        return common_skyflow_creds
    if env_skyflow_creds:
        return env_skyflow_creds
    else:
        raise Exception("Invalid Credentials")
    pass


def validate_config(config):
    return True