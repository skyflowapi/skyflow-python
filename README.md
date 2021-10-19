
# Description
---
skyflow-python is the Skyflow SDK for the Python programming language.


## Usage
---

### Service Account Token Generation

[This](https://github.com/skyflowapi/skyflow-python/tree/main/ServiceAccount) python module is used to generate service account tokens from service account credentials file which is downloaded upon creation of service account. The token generated from this module is valid for 60 minutes and can be used to make API calls to vault services as well as management API(s) based on the permissions of the service account.

  

You can install the package using the following command:


```bash
$ pip install skyflow
```

[Example](https://github.com/skyflowapi/skyflow-python/blob/main/examples/SATokenExample.py):


```python
from skyflow.ServiceAccount import GenerateToken

filepath =  '<YOUR_CREDENTIALS_FILE_PATH>'
accessToken, tokenType = GenerateToken(filepath)

print("Access Token:", accessToken)
print("Type of token:", tokenType)
```
