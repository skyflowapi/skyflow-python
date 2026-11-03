# Authentication credentials options

> **Note:** Only one type of credential can be used at a time. If the `credentials` dict has more than one of `api_key`, `token`, `path`, or `credentials_string`, the SDK raises a `SkyflowError`.

1. **API keys**

   A unique identifier used to authenticate and authorize requests to an API.

   ```python
   credentials = {
    "api_key": "<YOUR_API_KEY>"
    }
   ```

2. **Bearer tokens**

   A temporary access token used to authenticate API requests, typically included in the
   Authorization header.

   ```python
   credentials = {
    "token": "<YOUR_BEARER_TOKEN>"
    }
   ```

3. **Service account credentials file path**

   The file path pointing to a JSON file containing credentials for a service account, used
   for secure API access.

   ```python
   credentials = {
    "path": "<YOUR_CREDENTIALS_FILE_PATH>"
    }
   ```

4. **Service account credentials string**

   JSON-formatted string containing service account credentials, often used as an alternative to a file for programmatic authentication.

   ```python
   credentials = {
    "credentials_string": os.getenv("MY_APP_CREDENTIALS_JSON")
    }
   ```

   `MY_APP_CREDENTIALS_JSON` is an example name for a variable you choose yourself; it's unrelated to the `SKYFLOW_CREDENTIALS` variable the SDK reads automatically, described next.

5. **Environment variables**

   If no credentials are explicitly provided, the SDK automatically looks for the `SKYFLOW_CREDENTIALS` environment variable. This variable must contain a JSON string like one of the examples above.
