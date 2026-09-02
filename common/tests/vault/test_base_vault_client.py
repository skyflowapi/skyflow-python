import unittest
from unittest.mock import patch, MagicMock

from common.errors import SkyflowError
from common.utils import SkyflowMessages
from common.vault.base_vault_client import BaseVaultClient

CONFIG = {
    "credentials": "some_credentials",
    "cluster_id": "test_cluster_id",
    "env": "test_env",
    "vault_id": "test_vault_id",
    "roles": ["role_id_1", "role_id_2"],
    "ctx": "context"
}

CREDENTIALS_WITH_API_KEY = {"api_key": "dummy_api_key"}
CREDENTIALS_WITH_TOKEN = {"token": "dummy_static_token"}
CREDENTIALS_WITH_PATH = {"path": "/some/path/credentials.json"}
CREDENTIALS_WITH_STRING = {"credentials_string": '{"clientID": "x"}'}

ROLES = ["role_id_1", "role_id_2"]
STRING_CONTEXT = "user_12345"
DICT_CONTEXT = {"role": "admin", "department": "finance"}

CREDENTIALS_WITH_PATH_ROLES_AND_STRING_CONTEXT = {
    "path": "/some/path/credentials.json",
    "roles": ROLES,
    "context": STRING_CONTEXT,
}
CREDENTIALS_WITH_PATH_AND_DICT_CONTEXT = {
    "path": "/some/path/credentials.json",
    "context": DICT_CONTEXT,
}
CREDENTIALS_WITH_STRING_ROLES_AND_CONTEXT = {
    "credentials_string": '{"clientID": "x"}',
    "roles": ROLES,
    "context": STRING_CONTEXT,
}


class DummyVaultClient(BaseVaultClient):
    """Minimal concrete subclass -- exercises BaseVaultClient's shared logic without any
    variant-specific generated-API wiring. Mirrors what test__client.py used to test directly
    against v2's VaultClient, before initialize_client_configuration/get_bearer_token moved here.

    resolve_vault_url is a real (if trivial) implementation here, not just a stub, because
    BaseVaultClient.initialize_client_configuration() now delegates URL construction to it --
    each variant's derivation differs (see BaseVaultClient.resolve_vault_url's docstring), so
    there's no generic default to fall back on."""

    def resolve_vault_url(self, cluster_id, env, vault_id, logger=None):
        return "https://test-vault-url.com"

    def initialize_api_client(self, vault_url, bearer_token):
        self._api_client = MagicMock()


class TestBaseVaultClient(unittest.TestCase):
    def setUp(self):
        self.vault_client = DummyVaultClient(dict(CONFIG))

    # ------------------------------------------------------------------ #
    # Basic setters / getters
    # ------------------------------------------------------------------ #

    def test_set_common_skyflow_credentials(self):
        credentials = {"api_key": "dummy_api_key"}
        self.vault_client.set_common_skyflow_credentials(credentials)
        self.assertEqual(self.vault_client.get_common_skyflow_credentials(), credentials)

    def test_set_logger(self):
        mock_logger = MagicMock()
        self.vault_client.set_logger("INFO", mock_logger)
        self.assertEqual(self.vault_client.get_log_level(), "INFO")
        self.assertEqual(self.vault_client.get_logger(), mock_logger)

    def test_get_vault_id(self):
        self.assertEqual(self.vault_client.get_vault_id(), CONFIG["vault_id"])

    def test_get_config(self):
        self.assertEqual(self.vault_client.get_config(), CONFIG)

    # ------------------------------------------------------------------ #
    # initialize_client_configuration — first call (slow path)
    # ------------------------------------------------------------------ #

    @patch("common.vault.base_vault_client.get_credentials")
    @patch.object(DummyVaultClient, "resolve_vault_url")
    @patch.object(DummyVaultClient, "initialize_api_client")
    def test_initialize_client_configuration_first_call(
        self, mock_init_api_client, mock_resolve_vault_url, mock_get_credentials
    ):
        mock_get_credentials.return_value = CREDENTIALS_WITH_API_KEY
        mock_resolve_vault_url.return_value = "https://test-vault-url.com"

        self.vault_client.initialize_client_configuration()

        mock_get_credentials.assert_called_once_with(
            CONFIG["credentials"], None, logger=None
        )
        mock_resolve_vault_url.assert_called_once_with(
            CONFIG["cluster_id"], CONFIG["env"], CONFIG["vault_id"], logger=None
        )
        mock_init_api_client.assert_called_once()

    # ------------------------------------------------------------------ #
    # initialize_client_configuration — fast path (static token)
    # ------------------------------------------------------------------ #

    @patch("common.vault.base_vault_client.get_credentials")
    @patch.object(DummyVaultClient, "resolve_vault_url")
    def test_initialize_client_configuration_fast_path_api_key(
        self, mock_resolve_vault_url, mock_get_credentials
    ):
        """Once initialized with api_key, subsequent calls skip all work."""
        mock_get_credentials.return_value = CREDENTIALS_WITH_API_KEY
        mock_resolve_vault_url.return_value = "https://test-vault-url.com"

        self.vault_client.initialize_client_configuration()  # first call — slow path
        mock_get_credentials.reset_mock()
        mock_resolve_vault_url.reset_mock()

        self.vault_client.initialize_client_configuration()  # second call — fast path

        mock_get_credentials.assert_not_called()
        mock_resolve_vault_url.assert_not_called()

    @patch("common.vault.base_vault_client.get_credentials")
    @patch.object(DummyVaultClient, "resolve_vault_url")
    def test_initialize_client_configuration_fast_path_static_token(
        self, mock_resolve_vault_url, mock_get_credentials
    ):
        """Once initialized with a static token, subsequent calls skip all work."""
        mock_get_credentials.return_value = CREDENTIALS_WITH_TOKEN
        mock_resolve_vault_url.return_value = "https://test-vault-url.com"

        self.vault_client.initialize_client_configuration()
        mock_get_credentials.reset_mock()
        mock_resolve_vault_url.reset_mock()

        self.vault_client.initialize_client_configuration()

        mock_get_credentials.assert_not_called()
        mock_resolve_vault_url.assert_not_called()

    # ------------------------------------------------------------------ #
    # initialize_client_configuration — fast path (service account)
    # ------------------------------------------------------------------ #

    @patch("common.vault.base_vault_client.is_expired", return_value=False)
    @patch("common.vault.base_vault_client.get_credentials")
    @patch.object(DummyVaultClient, "resolve_vault_url")
    @patch.object(DummyVaultClient, "initialize_api_client")
    def test_initialize_client_configuration_fast_path_valid_sa_token(
        self, mock_init_api_client, mock_resolve_vault_url, mock_get_credentials, mock_is_expired
    ):
        """Service account with a still-valid token skips get_bearer_token entirely."""
        mock_get_credentials.return_value = CREDENTIALS_WITH_PATH
        mock_resolve_vault_url.return_value = "https://test-vault-url.com"

        # Seed the cached bearer token as if first call already ran
        self.vault_client._api_client = MagicMock()
        self.vault_client._is_static_token = False
        self.vault_client._bearer_token = "cached_sa_token"
        self.vault_client._credentials = CREDENTIALS_WITH_PATH

        self.vault_client.initialize_client_configuration()

        mock_get_credentials.assert_not_called()
        mock_resolve_vault_url.assert_not_called()
        mock_init_api_client.assert_not_called()

    # ------------------------------------------------------------------ #
    # initialize_client_configuration — token expiry (no client reinit)
    # ------------------------------------------------------------------ #

    @patch("common.vault.base_vault_client.generate_bearer_token", return_value=("new_sa_token", None))
    @patch("common.vault.base_vault_client.is_expired", return_value=True)
    @patch("common.vault.base_vault_client.get_credentials")
    @patch.object(DummyVaultClient, "resolve_vault_url")
    @patch.object(DummyVaultClient, "initialize_api_client")
    def test_initialize_client_configuration_expired_token_no_reinit(
        self, mock_init_api_client, mock_resolve_vault_url, mock_get_credentials,
        mock_is_expired, mock_generate_bearer_token
    ):
        """Expired service account token is regenerated in-place; the api client is NOT recreated."""
        mock_get_credentials.return_value = CREDENTIALS_WITH_PATH
        mock_resolve_vault_url.return_value = "https://test-vault-url.com"

        # Client already initialized — simulate warm state with an expired token
        self.vault_client._api_client = MagicMock()
        self.vault_client._is_static_token = False
        self.vault_client._bearer_token = "expired_sa_token"
        self.vault_client._credentials = CREDENTIALS_WITH_PATH

        self.vault_client.initialize_client_configuration()

        # Token was regenerated
        mock_generate_bearer_token.assert_called_once()
        self.assertEqual(self.vault_client._bearer_token, "new_sa_token")
        # api client was NOT recreated
        mock_init_api_client.assert_not_called()

    # ------------------------------------------------------------------ #
    # initialize_client_configuration — config update forces reinit
    # ------------------------------------------------------------------ #

    @patch("common.vault.base_vault_client.get_credentials")
    @patch.object(DummyVaultClient, "resolve_vault_url")
    @patch.object(DummyVaultClient, "initialize_api_client")
    def test_initialize_client_configuration_reinit_after_update_config(
        self, mock_init_api_client, mock_resolve_vault_url, mock_get_credentials
    ):
        """update_config() marks the client stale; next call must recreate it."""
        mock_get_credentials.return_value = CREDENTIALS_WITH_API_KEY
        mock_resolve_vault_url.return_value = "https://test-vault-url.com"

        # Simulate already-initialized client
        self.vault_client._api_client = MagicMock()
        self.vault_client._is_static_token = True

        self.vault_client.update_config({"cluster_id": "new_cluster"})
        self.vault_client.initialize_client_configuration()

        mock_get_credentials.assert_called_once()
        mock_resolve_vault_url.assert_called_once()
        mock_init_api_client.assert_called_once()

    # ------------------------------------------------------------------ #
    # get_bearer_token
    # ------------------------------------------------------------------ #

    def test_get_bearer_token_with_api_key(self):
        result = self.vault_client.get_bearer_token(CREDENTIALS_WITH_API_KEY)
        self.assertEqual(result, "dummy_api_key")

    def test_get_bearer_token_with_static_token(self):
        result = self.vault_client.get_bearer_token(CREDENTIALS_WITH_TOKEN)
        self.assertEqual(result, "dummy_static_token")

    @patch("common.vault.base_vault_client.generate_bearer_token", return_value=("sa_token", None))
    def test_get_bearer_token_generates_from_path_on_first_call(self, mock_generate):
        result = self.vault_client.get_bearer_token(CREDENTIALS_WITH_PATH)
        mock_generate.assert_called_once()
        self.assertEqual(result, "sa_token")
        self.assertEqual(self.vault_client._bearer_token, "sa_token")

    @patch("common.vault.base_vault_client.generate_bearer_token_from_creds", return_value=("sa_token_str", None))
    @patch("common.vault.base_vault_client.log_info")
    def test_get_bearer_token_generates_from_credentials_string(self, mock_log, mock_generate):
        result = self.vault_client.get_bearer_token(CREDENTIALS_WITH_STRING)
        mock_generate.assert_called_once()
        self.assertEqual(result, "sa_token_str")

    @patch("common.vault.base_vault_client.generate_bearer_token", return_value=("new_token", None))
    @patch("common.vault.base_vault_client.is_expired", return_value=True)
    @patch("common.vault.base_vault_client.log_info")
    def test_get_bearer_token_regenerates_on_expiry(self, mock_log, mock_is_expired, mock_generate):
        """Expired token is regenerated silently — no exception raised."""
        self.vault_client._bearer_token = "expired_token"
        result = self.vault_client.get_bearer_token(CREDENTIALS_WITH_PATH)
        mock_generate.assert_called_once()
        self.assertEqual(result, "new_token")

    @patch("common.vault.base_vault_client.generate_bearer_token")
    @patch("common.vault.base_vault_client.is_expired", return_value=False)
    @patch("common.vault.base_vault_client.log_info")
    def test_get_bearer_token_reuses_valid_cached_token(self, mock_log, mock_is_expired, mock_generate):
        """Valid cached token is reused without calling generate_bearer_token."""
        self.vault_client._bearer_token = "valid_token"
        result = self.vault_client.get_bearer_token(CREDENTIALS_WITH_PATH)
        mock_generate.assert_not_called()
        self.assertEqual(result, "valid_token")

    # ------------------------------------------------------------------ #
    # update_config
    # ------------------------------------------------------------------ #

    def test_update_config_sets_flag(self):
        self.vault_client.update_config({"credentials": "new_credentials"})
        self.assertTrue(self.vault_client._is_config_updated)
        self.assertEqual(self.vault_client.get_config()["credentials"], "new_credentials")

    # ------------------------------------------------------------------ #
    # get_current_bearer_token (new accessor -- did not exist pre-split)
    # ------------------------------------------------------------------ #

    def test_get_current_bearer_token_none_before_first_fetch(self):
        self.assertIsNone(self.vault_client.get_current_bearer_token())

    def test_get_current_bearer_token_returns_cached_value(self):
        self.vault_client._bearer_token = "cached_value"
        self.assertEqual(self.vault_client.get_current_bearer_token(), "cached_value")

    # ------------------------------------------------------------------ #
    # resolve_vault_url is abstract -- a subclass that forgets it can't instantiate
    # ------------------------------------------------------------------ #

    def test_resolve_vault_url_is_a_required_abstract_hook(self):
        class MissingResolveVaultUrl(BaseVaultClient):
            def initialize_api_client(self, vault_url, bearer_token):
                pass

        with self.assertRaises(TypeError):
            MissingResolveVaultUrl(dict(CONFIG))

    # ------------------------------------------------------------------ #
    # get_bearer_token — roles / context forwarded to the token engine
    # ------------------------------------------------------------------ #

    @patch("common.vault.base_vault_client.generate_bearer_token", return_value=("sa_token", None))
    def test_get_bearer_token_forwards_roles_and_string_context_from_path_credentials(self, mock_generate):
        self.vault_client.get_bearer_token(CREDENTIALS_WITH_PATH_ROLES_AND_STRING_CONTEXT)
        _, options, _ = mock_generate.call_args[0]
        self.assertEqual(options["role_ids"], ROLES)
        self.assertEqual(options["ctx"], STRING_CONTEXT)

    @patch("common.vault.base_vault_client.generate_bearer_token_from_creds", return_value=("sa_token_str", None))
    @patch("common.vault.base_vault_client.log_info")
    def test_get_bearer_token_forwards_roles_and_context_from_credentials_string(self, mock_log, mock_generate):
        self.vault_client.get_bearer_token(CREDENTIALS_WITH_STRING_ROLES_AND_CONTEXT)
        _, options, _ = mock_generate.call_args[0]
        self.assertEqual(options["role_ids"], ROLES)
        self.assertEqual(options["ctx"], STRING_CONTEXT)

    @patch("common.vault.base_vault_client.generate_bearer_token", return_value=("sa_token", None))
    def test_get_bearer_token_forwards_dict_context_unmodified(self, mock_generate):
        self.vault_client.get_bearer_token(CREDENTIALS_WITH_PATH_AND_DICT_CONTEXT)
        _, options, _ = mock_generate.call_args[0]
        self.assertEqual(options["ctx"], DICT_CONTEXT)
        self.assertNotIn("role_ids", options)

    @patch("common.vault.base_vault_client.generate_bearer_token", return_value=("sa_token", None))
    def test_get_bearer_token_forwards_scalar_context_unmodified(self, mock_generate):
        for scalar_context in [123, 0, 1.5, 0.0, True, False]:
            with self.subTest(context=scalar_context):
                mock_generate.reset_mock()
                self.vault_client._bearer_token = None
                credentials = {**CREDENTIALS_WITH_PATH, "context": scalar_context}
                self.vault_client.get_bearer_token(credentials)
                _, options, _ = mock_generate.call_args[0]
                self.assertEqual(options["ctx"], scalar_context)
                self.assertIs(type(options["ctx"]), type(scalar_context))

    @patch("common.vault.base_vault_client.generate_bearer_token", return_value=("sa_token", None))
    def test_get_bearer_token_omits_options_when_roles_and_context_absent(self, mock_generate):
        self.vault_client.get_bearer_token(CREDENTIALS_WITH_PATH)
        _, options, _ = mock_generate.call_args[0]
        self.assertNotIn("role_ids", options)
        self.assertNotIn("ctx", options)

    @patch("common.vault.base_vault_client.generate_bearer_token")
    def test_get_bearer_token_rejects_empty_roles(self, mock_generate):
        credentials = {**CREDENTIALS_WITH_PATH, "roles": []}
        with self.assertRaises(SkyflowError) as ctx:
            self.vault_client.get_bearer_token(credentials)
        self.assertEqual(ctx.exception.message, SkyflowMessages.Error.EMPTY_ROLES.value)
        mock_generate.assert_not_called()

    @patch("common.vault.base_vault_client.generate_bearer_token")
    def test_get_bearer_token_rejects_empty_context(self, mock_generate):
        for empty_context in [{}, "", "   "]:
            credentials = {**CREDENTIALS_WITH_PATH, "context": empty_context}
            with self.assertRaises(SkyflowError) as ctx:
                self.vault_client.get_bearer_token(credentials)
            self.assertEqual(ctx.exception.message, SkyflowMessages.Error.EMPTY_CONTEXT.value)
        mock_generate.assert_not_called()

    @patch("common.vault.base_vault_client.generate_bearer_token", return_value=("sa_token", None))
    def test_get_bearer_token_ignores_top_level_config_roles_and_ctx(self, mock_generate):
        vault_client = DummyVaultClient({**CONFIG, "roles": ["stale_role"], "ctx": "stale_ctx"})
        vault_client.get_bearer_token(CREDENTIALS_WITH_PATH)
        _, options, _ = mock_generate.call_args[0]
        self.assertNotIn("role_ids", options)
        self.assertNotIn("ctx", options)

    @patch("common.vault.base_vault_client.generate_bearer_token", return_value=("sa_token", None))
    def test_get_bearer_token_forwards_token_uri_alongside_roles_and_context(self, mock_generate):
        credentials = {
            **CREDENTIALS_WITH_PATH_ROLES_AND_STRING_CONTEXT,
            "token_uri": "https://manage.skyflowapis.com/v1/auth/sa/oauth/token",
        }
        self.vault_client.get_bearer_token(credentials)
        _, options, _ = mock_generate.call_args[0]
        self.assertEqual(options["role_ids"], ROLES)
        self.assertEqual(options["ctx"], STRING_CONTEXT)
        self.assertEqual(options["token_uri"], credentials["token_uri"])

    @patch("common.vault.base_vault_client.generate_bearer_token", return_value=("refreshed_token", None))
    @patch("common.vault.base_vault_client.is_expired", return_value=True)
    def test_initialize_client_configuration_refresh_preserves_roles_and_context(self, mock_is_expired, mock_generate):
        self.vault_client._api_client = MagicMock()
        self.vault_client._is_static_token = False
        self.vault_client._bearer_token = "expired_sa_token"
        self.vault_client._credentials = CREDENTIALS_WITH_PATH_ROLES_AND_STRING_CONTEXT
        self.vault_client.initialize_client_configuration()
        _, options, _ = mock_generate.call_args[0]
        self.assertEqual(options["role_ids"], ROLES)
        self.assertEqual(options["ctx"], STRING_CONTEXT)


if __name__ == "__main__":
    unittest.main()
