# MongoDB (Atlas) setup — `mongodb+srv://` / PyMongo (Asynchronous)

## Environment variables

| Variable | Required | Example |
| --- | --- | --- |
| `DATABASE_URL` | ✅ | `mongodb+srv://rdxadmin:PASS@cluster0.ab1cd.mongodb.net/?retryWrites=true&w=majority` |
| `DATABASE_NAME` | optional | `Cluster0` (default). Set it if you want a different DB name than the one written in the URI. |

Copy the string from **Atlas → Database → Connect → Drivers → Python → PyMongo (Asynchronous)**.

## What the code now tolerates

`database/mongo.py` is the single place the URI is turned into a PyMongo client
(the bot, the web dashboard and the `/check_db` migration tool all use it):

* Spaces, newlines and wrapping quotes from a phone copy-paste are removed.
  Nothing else about the URI is rewritten, so passwords with `@ / : # ?` and
  multi-host strings keep working.
* `mongodb+srv://` is resolved by PyMongo itself (needs `dnspython`, pinned in
  `requirements.txt`). SRV **must not** contain a port — that raises a clear
  config error instead of a stack trace at import time.
* Bad URI options (e.g. a pasted `maxPoolSize=abc`) raise at startup instead of
  being silently ignored.
* `DATABASE_NAME` wins; otherwise the DB name inside the URI; otherwise
  `Cluster0` — so an Atlas URI with an empty `/` still works.
* Pool/TLS tuning lives in one place: `maxPoolSize=15`, `minPoolSize=2`,
  server selection 10 s, connect 20 s, socket 45 s, retries on.

## Verifying it works

1. `GET /health` → `{"status":"alive","database":"connected"|"unknown"|"error", ...}`
2. `GET /health?db=1` → actually pings MongoDB; returns **503** with an Atlas
   specific hint (whitelist / wrong password / DNS / TLS) when it fails.
3. Bot logs on startup: `✅ MongoDB connected` or one line
   `❌ Database index sync failed: <hint>` — the web port stays up either way.
4. Admin tool: `/check_db` (defaults to `DATABASE_URL`) or
   `/check_db <URI> [DB_NAME]` for any other cluster.

## Atlas checklist

* **Network Access** → `0.0.0.0/0` (or the host's egress IP) whitelisted.
* **Database Access** → a user with read/write on the database.
* Cluster not **paused** (free tier pauses when idle).
* Password special characters (`@ : / ? # [ ] %`) percent-encoded.
* The free-tier cluster must accept connections from the container's outbound
  network (port 27017 / DNS for `+srv`).
