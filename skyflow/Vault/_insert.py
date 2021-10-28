
import requests
from skyflow.Errors import SkyflowError, SkyflowErrorCodes
from json.encoder import JSONEncoder


def getInsertRequestBody(data):
    records = data["records"]
    requestBody = {"records": []}
    for record in records:
        requestBody["records"].append({
            "tableName": record["table"],
            "fields": record["fields"],
            "method": "POST",
            "quorum": True})
    return requestBody

