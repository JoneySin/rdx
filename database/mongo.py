"""One place that turns ``DATABASE_URL`` into a safe PyMongo async client.

Everything here exists because of real deployment mistakes, not theory:

* ``mongodb+srv://`` (what MongoDB Atlas -> "Connect -> PyMongo (Asynchronous)"
  gives you) is parsed by PyMongo's own ``parse_uri``. Nothing in this file
  rebuilds or URL-encodes the URI, so passwords with ``@ / : # ? %`` and multi
  host strings such as ``cluster0-shard-00-00.xxx.mongodb.net:27017,...`` keep
  working exactly as Atlas printed them — only the whitespace/newlines that a
  phone copy-paste adds are removed.
* ``mongodb+srv://`` needs ``dnspython``. We ship it, and a missing/broken copy
  now logs one clear line instead of a stack trace inside the bot startup.
* TLS/queue/socket options stay inside PyMongo's accepted ranges. An invalid
  value raises ``ConfigurationError`` *at construction time*, i.e. before the
  web port is up — the app used to die silently during import instead of
  showing ``/health`` so the mistake was visible.
* The database name comes from ``DATABASE_NAME`` and only falls back to the
  name inside the URI (Atlas often leaves that empty), then to ``Cluster0``.
"""
import logging
import warnings
from urllib.parse import unquote_plus, urlsplit

from pymongo import AsyncMongoClient
from pymongo.errors import ConfigurationError, InvalidURI, OperationFailure

logger = logging.getLogger(__name__)

DEFAULT_DB_NAME = "Cluster0"

# Atlas free/hobby clusters answer a cold SRV lookup slowly, but a paused
# cluster never answers: 10s keeps the first error fast instead of hanging the
# startup/index sync for half a minute.
SERVER_SELECTION_TIMEOUT_MS = 10000
CONNECT_TIMEOUT_MS = 20000
SOCKET_TIMEOUT_MS = 45000
MAX_POOL_SIZE = 15
MIN_POOL_SIZE = 2

_CLIENT_OPTIONS = {
    "appname": "RdxTv-Bot",
    "serverSelectionTimeoutMS": SERVER_SELECTION_TIMEOUT_MS,
    "connectTimeoutMS": CONNECT_TIMEOUT_MS,
    "socketTimeoutMS": SOCKET_TIMEOUT_MS,
    "maxPoolSize": MAX_POOL_SIZE,
    "minPoolSize": MIN_POOL_SIZE,
    "maxIdleTimeMS": 300000,     # idle sockets stay warm for 5 minutes
    "waitQueueTimeoutMS": 10000,  # fail fast instead of hanging when saturated
    "retryWrites": True,
    "retryReads": True,
}

class MongoConfigError(RuntimeError):
    """DATABASE_URL / DATABASE_NAME cannot be used as configured."""


def normalize_uri(raw):
    """Return a copy-paste-safe URI or raise ``MongoConfigError``."""
    url = (raw or "").strip().strip('\'"`')
    if not url:
        raise MongoConfigError("DATABASE_URL is empty")
    if any(char.isspace() for char in url):
        cleaned = "".join(url.split())
        logger.warning("DATABASE_URL contained spaces/newlines; removed them before connecting")
        url = cleaned
    if not url.lower().startswith(("mongodb://", "mongodb+srv://")):
        raise MongoConfigError(
            "DATABASE_URL must start with mongodb:// or mongodb+srv:// "
            "(copy it from Atlas -> Connect -> Drivers -> PyMongo)"
        )
    authority = url.split("://", 1)[1].split("/", 1)[0].split("?", 1)[0]
    hosts = authority.rsplit("@", 1)[-1]
    if not hosts or not all(part.split(":", 1)[0] for part in hosts.split(",")):
        raise MongoConfigError(
            "DATABASE_URL has no host — copy the whole URI including "
            "cluster0.xxxxx.mongodb.net (Atlas -> Connect -> Drivers -> PyMongo)"
        )
    if "=" in url.split("@")[0] and "%" not in url:
        # mongodb+srv://user:pa$$word@... -> the password contains '=' or a
        # similar reserved character raw. Only warn: a valid unescaped password
        # with '=' exists, and PyMongo will raise its own clear error anyway.
        logger.warning(
            "DATABASE_URL password looks unescaped; if auth fails, percent-encode "
            "special characters (@ : / ? # [ ] % ) in the password"
        )
    return url


def database_name(url, configured):
    """Configured name wins; then the name inside the URI; then ``Cluster0``."""
    name = (configured or "").strip()
    if name:
        return name
    try:
        path = urlsplit(url).path.lstrip("/")
    except ValueError:
        path = ""
    name = unquote_plus(path.split("?")[0]).strip()
    if name:
        logger.warning("DATABASE_NAME is empty; using the database name from DATABASE_URL (%s)", name)
        return name
    logger.warning("DATABASE_NAME is empty and DATABASE_URL has no database name; using %s", DEFAULT_DB_NAME)
    return DEFAULT_DB_NAME


def create_client(url, *, purpose="bot"):
    """Build the shared async client for a (possibly different) URI.

    ``purpose`` only labels log lines so a failing ``/check_db`` migration is
    not mistaken for the main connection.
    """
    uri = normalize_uri(url)
    try:
        # PyMongo flags a bad option value (e.g. a pasted "maxPoolSize=abc")
        # with UserWarning and keeps the default. Turning it into an error means
        # a typo shows up at startup instead of silently half-applying.
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            return AsyncMongoClient(uri, **_CLIENT_OPTIONS)
    except (ConfigurationError, InvalidURI, ValueError, UserWarning) as exc:
        hint = ""
        if uri.startswith("mongodb+srv://") and "dnspython" in str(exc).lower():
            hint = " (pip install dnspython==2.9.2)"
        raise MongoConfigError(f"Could not configure MongoDB {purpose} client: {exc}{hint}") from exc


def connect_error_hint(exc):
    """Turn the most common Atlas failures into a one-line actionable hint."""
    text = str(exc) or exc.__class__.__name__
    lowered = text.lower()
    if "serverselection" in exc.__class__.__name__.lower() or "serverselectiontimeout" in lowered:
        return (text + "\n\n👉 Check: Atlas Network Access me 0.0.0.0/0 whitelist hai? "
                "Cluster paused hai? DATABASE_URL me space/newline to nahi?")
    if isinstance(exc, OperationFailure) and getattr(exc, "code", None) == 18:
        return text + "\n\n👉 Atlas user ka password galat hai (ya user Database Access me nahi hai)."
    if "dns" in lowered or "srv" in lowered:
        return text + "\n\n👉 mongodb+srv:// ke liye dnspython chahiye aur network ko DNS/53 allow karna hoga."
    if "certificate" in lowered or "ssl" in lowered or "tls" in lowered:
        return text + "\n\n👉 TLS blocked hai: container/host ka CA store aur outbound 27017 check karo."
    return text


async def ping(client):
    """Cheap round-trip used by /health and the admin DB tools."""
    await client.admin.command("ping")
