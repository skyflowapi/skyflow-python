
import requests
from skyflow.Errors._skyflowErrors import SkyflowError, SkyflowErrorCodes, SkyflowErrorMessages
from json.encoder import JSONEncoder


def getInsertRequestBody(data):
    try:
        records = data["records"]
    except KeyError:
        raise SkyflowError(SkyflowErrorCodes.INVALID_INPUT, SkyflowErrorMessages.RECORDS_KEY_ERROR)
    requestBody = {"records": []}
    for record in records:
        requestBody["records"].append({
            "tableName": record["table"],
            "fields": record["fields"],
            "method": "POST",
            "quorum": True})
    return requestBody

