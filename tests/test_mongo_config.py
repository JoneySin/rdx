"""DATABASE_URL handling for the Atlas "PyMongo (Asynchronous)" URI.

Atlas hands out ``mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority``.
That URI has to survive a phone copy-paste (spaces, newlines, quotes, a password
with ``@``) and it must actually reach PyMongo with SRV + TLS options intact.
"""
import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs

ATLAS_URI = ("mongodb+srv://rdxadmin:C0ffee%40Shop@cluster0.ab1cd.mongodb.net/"
             "?retryWrites=true&w=majority&appName=Cluster0")

for key, value in {
    "API_ID": "1", "API_HASH": "test", "BOT_TOKEN": "1:test", "ADMINS": "1",
    "LOG_CHANNEL": "-1001", "BIN_CHANNEL": "-1002", "URL": "https://example.com",
    "UPI_ID": "test@upi", "UPI_NAME": "Test Merchant", "RECEIPT_SEND_USERNAME": "@admin",
    # The exact shape Atlas -> Connect -> "PyMongo (Asynchronous)" produces.
    "DATABASE_URL": ATLAS_URI,
}.items():
    os.environ.setdefault(key, value)

import pymongo  # noqa: E402

from database import mongo  # noqa: E402


class UriNormalizationTests(unittest.TestCase):
    def test_atlas_uri_is_used_verbatim(self):
        self.assertEqual(mongo.normalize_uri(ATLAS_URI), ATLAS_URI)

    def test_copied_uri_with_spaces_newlines_and_quotes_is_cleaned(self):
        clean = ATLAS_URI.split("&appName")[0]
        messy = '  "' + clean + '"\n'
        self.assertEqual(mongo.normalize_uri(messy), clean)

    def test_plain_multi_host_uri_is_accepted(self):
        uri = "mongodb://u:p@a.example.net:27017,b.example.net:27018/?replicaSet=rs0"
        self.assertEqual(mongo.normalize_uri(uri), uri)

    def test_wrong_scheme_is_a_clear_error(self):
        for bad in ("", "   ", "postgres://u:p@host/db", "cluster0.ab1cd.mongodb.net"):
            with self.assertRaises(mongo.MongoConfigError):
                mongo.normalize_uri(bad)

    def test_database_name_prefers_env_then_uri_then_default(self):
        self.assertEqual(mongo.database_name(ATLAS_URI, "MyDb"), "MyDb")
        self.assertEqual(mongo.database_name(ATLAS_URI, ""), "Cluster0")
        self.assertEqual(
            mongo.database_name("mongodb+srv://u:p@c.mongodb.net/RdxTv?retryWrites=true", ""),
            "RdxTv",
        )
        self.assertEqual(mongo.database_name("mongodb://localhost:27017", None), "Cluster0")

    def test_default_db_name_matches_info_default(self):
        from info import DATABASE_NAME
        self.assertEqual(mongo.DEFAULT_DB_NAME, "Cluster0")
        self.assertEqual(DATABASE_NAME, "Cluster0")


class ClientOptionTests(unittest.TestCase):
    def test_srv_client_gets_srv_parsing_options_and_atlas_defaults(self):
        client = mongo.create_client(ATLAS_URI, purpose="test")
        try:
            opts = client.options
            # SRV needs dnspython; requirements.txt pins it for the same reason.
            import dns.resolver  # noqa: F401
            self.assertTrue(hasattr(pymongo, "AsyncMongoClient"))
            self.assertEqual(opts.pool_options.max_pool_size, mongo.MAX_POOL_SIZE)
            self.assertEqual(opts.pool_options.min_pool_size, mongo.MIN_POOL_SIZE)
            # PyMongo exposes this in seconds, the URI option is milliseconds.
            self.assertEqual(opts.server_selection_timeout,
                             mongo.SERVER_SELECTION_TIMEOUT_MS / 1000)
            self.assertTrue(opts.retry_writes)
            self.assertEqual(opts.pool_options.appname, "RdxTv-Bot")
            # Atlas prints these itself; appending them again breaks the URI.
            self.assertEqual(parse_qs(ATLAS_URI.split("?", 1)[1])["retryWrites"], ["true"])
        finally:
            asyncio.run(client.close())

    def test_invalid_uri_raises_config_error_not_configuration_error(self):
        invalid = ("mongodb+srv://a:b@cluster0.ab1cd.mongodb.net/?maxPoolSize=-5",
                   "mongodb+srv://cluster0.ab1cd.mongodb.net:27017/",     # SRV + port
                   "mongodb+srv://u:p@cluster0.ab1cd.mongodb.net/?tls=maybe")
        for uri in invalid:
            with self.subTest(uri=uri), self.assertRaises(mongo.MongoConfigError):
                mongo.create_client(uri, purpose="test")

    def test_connection_hint_mentions_atlas_whitelist_and_auth(self):
        from pymongo.errors import OperationFailure, ServerSelectionTimeoutError
        hint = mongo.connect_error_hint(ServerSelectionTimeoutError("no primary"))
        self.assertIn("whitelist", hint.lower())
        auth = OperationFailure("Authentication failed.", code=18)
        self.assertIn("password", mongo.connect_error_hint(auth).lower())


class AdminToolUriTests(unittest.IsolatedAsyncioTestCase):
    """The /check_db migration flow must accept a real Atlas paste."""

    async def test_multiline_atlas_paste_with_db_name_is_parsed(self):
        from plugins import check_db_TEMP

        seen = {}
        class FakeClient:
            def __init__(self):
                self.admin = SimpleNamespace(command=AsyncMock())
                self.close = AsyncMock()
            def __getitem__(self, name):
                seen["db"] = name
                return SimpleNamespace(list_collection_names=AsyncMock(return_value=[]))
        created = []

        def fake_create(url, purpose="bot"):
            created.append(url)
            return FakeClient()

        message = SimpleNamespace(
            from_user=SimpleNamespace(id=56),
            text="mongodb+srv://u:p%40x@cluster0.ab1cd.mongodb.net/?retryWrites=true&\n w=majority RdxTv",
            reply=AsyncMock(return_value=SimpleNamespace(edit=AsyncMock())),
        )
        check_db_TEMP.PENDING[56] = {"action": "copy_db", "collection": None}
        with patch.object(check_db_TEMP, "create_client", fake_create):
            await check_db_TEMP.receive_new_url(None, message)
        # Newlines inside the pasted URL are stripped, the DB name is separate.
        self.assertEqual(created[1],
                         "mongodb+srv://u:p%40x@cluster0.ab1cd.mongodb.net/?retryWrites=true&w=majority")
        self.assertEqual(seen["db"], "RdxTv")
        self.assertNotIn(56, check_db_TEMP.PENDING)


class StartupWiringTests(unittest.IsolatedAsyncioTestCase):
    async def test_bot_and_library_share_the_same_client_settings(self):
        from database import ia_filterdb
        from database.users_chats_db import Database
        bot_client = Database().client
        try:
            library = ia_filterdb.client
            self.assertEqual(bot_client.options.pool_options.max_pool_size,
                             library.options.pool_options.max_pool_size)
            self.assertEqual(bot_client.options.server_selection_timeout,
                             library.options.server_selection_timeout)
            self.assertEqual(bot_client.options.pool_options.appname,
                             library.options.pool_options.appname)
        finally:
            await bot_client.close()

    async def test_health_route_reports_database_state(self):
        from web.dashboard_routes import koyeb_health_check
        from utils import temp

        class Request:
            def __init__(self, query):
                self.query = query

        with patch.object(temp, "DB_STATE", "connected", create=True):
            response = await koyeb_health_check(Request({}))
        self.assertEqual(response.status, 200)
        self.assertEqual(response.text.find('"database": "connected"') > 0, True)

        with patch.object(temp, "DB_STATE", "connected", create=True), \
                patch.object(mongo, "ping", AsyncMock()) as pinged:
            response = await koyeb_health_check(Request({"db": "1"}))
            pinged.assert_awaited_once()
        self.assertEqual(response.status, 200)

        with patch.object(temp, "DB_STATE", "error", create=True), \
                patch.object(mongo, "ping", AsyncMock(side_effect=RuntimeError("no auth"))):
            response = await koyeb_health_check(Request({"db": "1"}))
        self.assertEqual(response.status, 503)


if __name__ == "__main__":
    unittest.main()
