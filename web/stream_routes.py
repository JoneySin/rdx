import math, os, secrets, mimetypes, logging, gc, ctypes, asyncio
from urllib.parse import quote
from aiohttp import web
from utils import temp
from web.utils.custom_dl import TGCustomYield, chunk_size, offset_fix
from web.utils.render_template import media_watch
from web.utils.media_info import get_media_info
from web.web_assets import get_auth
from web.brand import BRAND_MARKUP, BRAND_CSS
from stream_security import verify

routes = web.RouteTableDef()
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 🏠 ROOT ROUTE
# ─────────────────────────────────────────────
@routes.get("/", allow_head=True)
async def root_route_handler(request):
    role, _ = await get_auth(request)
    if role:                                   # लॉगिन है → लैंडिंग पेज की जगह सीधे dashboard
        raise web.HTTPFound('/dashboard')
    # ✅ BUG FIX: pehle `getattr(temp, 'U_NAME', 'AutoFilterBot')` tha, par temp.U_NAME
    # class me already `None` declared hai — isliye getattr ka default KABHI apply nahi
    # hota tha aur bot_username `None` aata tha. Uske baad `.replace(..., None)`
    # TypeError deta tha, yaani homepage `/` pura 500 crash karta tha jab tak bot client
    # start na ho jaaye. Ab `or` se sahi fallback milta hai.
    bot_username = temp.U_NAME or 'AutoFilterBot'

    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RdxTv — Next-Gen Cloud Cinema & Series</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#050914;
  --surface:rgba(12,21,44,.78);
  --surface-strong:rgba(16,28,58,.92);
  --border:rgba(99,102,241,.26);
  --text:#f1f5f9;
  --muted:#94a8cd;
  --accent:#6366f1;
  --cyan:#06b6d4;
  --grad:linear-gradient(135deg,#6366f1 0%,#06b6d4 100%);
  --glow:rgba(6,182,212,.28);
}
html.light{
  --bg:#eff4fc;
  --surface:rgba(255,255,255,.86);
  --surface-strong:#ffffff;
  --border:#cbd8ef;
  --text:#0b132b;
  --muted:#52658a;
  --accent:#4f46e5;
  --cyan:#0284c7;
  --grad:linear-gradient(135deg,#4f46e5 0%,#0284c7 100%);
  --glow:rgba(79,70,229,.20);
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Plus Jakarta Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;display:flex;flex-direction:column;overflow-x:hidden;transition:background .25s,color .25s}
.hero-bg{
  position:fixed;inset:0;z-index:-1;pointer-events:none;
  background-color:var(--bg);
  background-image:
    radial-gradient(circle at 18% 15%,rgba(99,102,241,.32) 0%,transparent 45%),
    radial-gradient(circle at 84% 18%,rgba(6,182,212,.26) 0%,transparent 44%),
    radial-gradient(circle at 50% 88%,rgba(168,85,247,.18) 0%,transparent 52%),
    linear-gradient(rgba(148,168,205,.05) 1px,transparent 1px),
    linear-gradient(90deg,rgba(148,168,205,.05) 1px,transparent 1px);
  background-size:100% 100%,100% 100%,100% 100%,42px 42px,42px 42px;
}
html.light .hero-bg{
  background-image:
    radial-gradient(circle at 18% 15%,rgba(79,70,229,.15) 0%,transparent 45%),
    radial-gradient(circle at 84% 18%,rgba(2,132,199,.14) 0%,transparent 44%),
    linear-gradient(rgba(15,23,42,.04) 1px,transparent 1px),
    linear-gradient(90deg,rgba(15,23,42,.04) 1px,transparent 1px);
  background-size:100% 100%,100% 100%,42px 42px,42px 42px;
}
.navbar{display:flex;justify-content:space-between;align-items:center;padding:20px 5%;z-index:10;border-bottom:1px solid rgba(148,168,205,.12);backdrop-filter:blur(16px);background:rgba(5,9,20,.45)}
html.light .navbar{background:rgba(255,255,255,.68);border-bottom-color:var(--border)}
.logo{font-size:26px;font-weight:900;color:var(--text);text-decoration:none;display:flex;align-items:center;gap:9px;letter-spacing:.4px}
.header-actions{display:flex;align-items:center;gap:10px}
.theme-btn{background:var(--surface);border:1px solid var(--border);color:var(--text);padding:8px 16px;border-radius:999px;font-family:inherit;font-weight:700;font-size:13px;cursor:pointer;transition:.2s;backdrop-filter:blur(10px)}
.theme-btn:hover{border-color:var(--cyan);transform:translateY(-1px)}
.admin-btn{background:var(--grad);color:#fff;text-decoration:none;padding:9px 20px;border-radius:999px;font-weight:800;font-size:13px;transition:.2s;box-shadow:0 6px 20px var(--glow)}
.admin-btn:hover{filter:brightness(1.08);transform:translateY(-1px)}
.hero-content{flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:48px 20px 56px;z-index:10;max-width:960px;margin:0 auto;width:100%}
.hero-badge{display:inline-flex;align-items:center;gap:8px;padding:6px 16px;border-radius:999px;background:rgba(6,182,212,.12);border:1px solid rgba(6,182,212,.32);color:var(--cyan);font-size:11.5px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;margin-bottom:22px}
.hero-title{font-family:'Outfit','Plus Jakarta Sans',sans-serif;font-size:clamp(2.35rem,6vw,4.35rem);font-weight:900;margin-bottom:16px;line-height:1.08;letter-spacing:-1.2px}
.hero-title .grad-txt{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero-sub{font-size:clamp(1.02rem,2.2vw,1.28rem);color:var(--muted);font-weight:500;margin-bottom:34px;max-width:640px;line-height:1.6}
.search-container{display:flex;width:100%;max-width:680px;padding:7px;border-radius:18px;background:var(--surface);border:1px solid var(--border);backdrop-filter:blur(20px);box-shadow:0 20px 55px rgba(2,6,23,.42);gap:8px}
html.light .search-container{box-shadow:0 16px 42px rgba(15,23,42,.09)}
.search-input{flex:1;padding:15px 18px;font-family:inherit;font-size:1.05rem;font-weight:600;border:none;border-radius:12px;background:transparent;color:var(--text);outline:none;min-width:0}
.search-input::placeholder{color:var(--muted);font-weight:500}
.search-btn{background:var(--grad);color:#fff;border:none;padding:0 28px;font-family:'Outfit','Plus Jakarta Sans',sans-serif;font-size:1.05rem;font-weight:800;border-radius:12px;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;transition:.2s;box-shadow:0 8px 22px var(--glow);white-space:nowrap}
.search-btn:hover{filter:brightness(1.08);transform:translateY(-1px)}
.quick-picks{margin-top:28px;display:flex;flex-wrap:wrap;justify-content:center;gap:9px}
.qp-title{width:100%;font-size:11px;color:var(--muted);margin-bottom:6px;font-weight:800;text-transform:uppercase;letter-spacing:1.6px}
.tag{background:var(--surface);border:1px solid var(--border);padding:7px 16px;border-radius:999px;font-size:13px;font-weight:700;cursor:pointer;transition:.2s;backdrop-filter:blur(10px)}
.tag:hover{border-color:var(--cyan);color:var(--cyan);transform:translateY(-2px)}
.feature-strip{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;width:100%;margin-top:48px;text-align:left}
.feat-card{background:var(--surface);border:1px solid var(--border);border-radius:18px;padding:20px;backdrop-filter:blur(14px);transition:transform .22s,border-color .22s}
.feat-card:hover{transform:translateY(-4px);border-color:var(--cyan)}
.feat-icon{display:inline-grid;place-items:center;width:38px;height:38px;border-radius:11px;background:rgba(99,102,241,.16);border:1px solid rgba(99,102,241,.3);font-size:18px;margin-bottom:12px}
.feat-card h3{font-family:'Outfit','Plus Jakarta Sans',sans-serif;font-size:16px;font-weight:800;margin-bottom:5px}
.feat-card p{font-size:13px;color:var(--muted);line-height:1.5}
@media (max-width:760px){.feature-strip{grid-template-columns:1fr;gap:12px;margin-top:36px}}
@media (max-width:600px){
  .navbar{padding:14px 4%}
  .search-container{flex-direction:column;padding:10px;border-radius:16px}
  .search-input{padding:12px 14px;background:var(--surface-strong)}
  .search-btn{padding:14px;width:100%}
  .logo{font-size:20px}
  .theme-btn,.admin-btn{padding:6px 12px;font-size:12px}
}
__BRAND_CSS__
</style>
</head>
<body>
<div class="hero-bg"></div>
<header class="navbar">
    <a href="/" class="logo landing-brand" aria-label="RdxTv home">__BRAND_MARKUP__</a>
    <div class="header-actions">
        <button class="theme-btn" id="theme-btn">🌗 Theme</button>
        <a href="/login" class="admin-btn">Sign In</a>
    </div>
</header>
<main class="hero-content">
    <div class="hero-badge">⚡ Direct Cloud Cinema Engine</div>
    <h1 class="hero-title">Unlimited Cinema,<br><span class="grad-txt">Reimagined on RdxTv.</span></h1>
    <p class="hero-sub">Instant multi-vault search, high-bitrate byte streaming, and curated series collections — synced across Web &amp; Telegram.</p>
    <div class="search-container">
        <input type="text" id="searchInput" class="search-input" placeholder="Search movies, web series, 4K UHD, anime..." autocomplete="off">
        <button class="search-btn" onclick="startSearch()">Stream Now &rarr;</button>
    </div>
    <div class="quick-picks">
        <div class="qp-title">Trending Vault Picks</div>
        <span class="tag" onclick="fillAndSearch('Action')">🔥 Action</span>
        <span class="tag" onclick="fillAndSearch('Web Series')">📺 Web Series</span>
        <span class="tag" onclick="fillAndSearch('Thriller')">🕵️ Thriller</span>
        <span class="tag" onclick="fillAndSearch('Anime')">🎌 Anime</span>
        <span class="tag" onclick="fillAndSearch('4K')">💎 4K UHD</span>
        <span class="tag" onclick="fillAndSearch('Sci-Fi')">🚀 Sci-Fi</span>
    </div>
    <section class="feature-strip" aria-label="RdxTv highlights">
        <div class="feat-card"><div class="feat-icon">⚡</div><h3>Zero-Wait Byte Stream</h3><p>Direct range-request playback with smooth 10-second seek and adaptive Plyr controls.</p></div>
        <div class="feat-card"><div class="feat-icon">🗂️</div><h3>Smart Quality &amp; Series</h3><p>Grouped multi-resolution packs and ordered season episodes in one unified hub.</p></div>
        <div class="feat-card"><div class="feat-icon">📱</div><h3>Web + Mini App Sync</h3><p>Jump seamlessly between the RdxTv Web Portal and the native Telegram Mini App.</p></div>
    </section>
</main>
<script>
(function(){if(localStorage.getItem('theme')==='light')document.documentElement.classList.add('light')})();
document.getElementById('theme-btn').addEventListener('click',()=>{
    let isLight = document.documentElement.classList.toggle('light');
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
});
function startSearch(){
    const q=document.getElementById('searchInput').value.trim();
    const base=`https://t.me/BOT_USERNAME_PLACEHOLDER`;
    window.open(q?`${base}?start=${encodeURIComponent(q)}`:base,'_blank');
}
function fillAndSearch(q){
    document.getElementById('searchInput').value=q;
    startSearch();
}
document.getElementById('searchInput').addEventListener('keydown',e=>{
    if(e.key==='Enter') startSearch();
});
</script>
</body>
</html>""".replace("BOT_USERNAME_PLACEHOLDER", bot_username).replace("__BRAND_CSS__", BRAND_CSS).replace("__BRAND_MARKUP__", BRAND_MARKUP)

    return web.Response(text=html_content, content_type='text/html')


# ─────────────────────────────────────────────
# 📺 STREAM / WATCH ROUTE
# ─────────────────────────────────────────────
@routes.get("/watch/{message_id}")
async def watch_handler(request):
    try:
        mid = int(request.match_info['message_id'])
        e, s = request.query.get("e"), request.query.get("s")
        if not verify(mid, e, s):
            return web.Response(status=403, text="Link expired or invalid", content_type='text/plain')
        return web.Response(
            text=await media_watch(mid, f"e={int(e)}&s={s}"),
            content_type='text/html'
        )
    except ValueError:
        return web.Response(status=400, text="Invalid Message ID")
    except Exception as e:
        logger.error(f"Watch Error: {e}")
        return web.Response(status=500, text="Internal Server Error")


# ─────────────────────────────────────────────
# 📐 HTTP RANGE PARSER (extracted + hardened)
# ✅ BUG FIX: पहले यह parsing media_download() के अंदर inline थी और `r_head` try-block
# के अंदर assign होकर बाहर इस्तेमाल होता था — अगर `int()` कहीं बीच में फेंकता तो
# `r_head` unbound रह सकता था। साथ ही unsatisfiable range (start > file_size) पर
# 416 की जगह आगे बढ़कर negative Content-Length बन सकता था। अब सब एक pure function
# में है, इसलिए इसे test भी किया जा सकता है।
# return: (first_byte, last_byte, length, is_partial) या None (416 भेजना है)
# ─────────────────────────────────────────────
def parse_range(header, file_size):
    """Range header को validated (start, end, length, partial) में बदलता है।"""
    partial = bool(header)
    try:
        if header:
            spec = header.replace("bytes=", "").split(",")[0].strip()
            a, b = spec.split("-", 1)
            if a == "":                       # suffix range: bytes=-N => aakhri N bytes
                first, last = max(file_size - int(b), 0), file_size - 1
            else:
                first = int(a)
                last = int(b) if b else file_size - 1
        else:
            first, last = 0, file_size - 1
    except Exception:
        first, last, partial = 0, file_size - 1, False

    last = min(last, file_size - 1)          # upper bound clamp
    if first < 0 or last < first:            # unsatisfiable
        return None
    return first, last, last - first + 1, partial


# ─────────────────────────────────────────────
# 📥 DOWNLOAD & STREAMING CORE
# ─────────────────────────────────────────────
# Ek saath max kitne open stream connections (RAM bachane ke liye; har connection par
# PREFETCH MB tak buffer rehta hai). Ye sirf connections gino hai — asli speed-control
# custom_dl.py me STREAM_FETCH_CONCURRENCY se hota hai.
MAX_CONNS = max(1, int(os.environ.get("STREAM_MAX_CONNS", "15")))
_ACTIVE_STREAMS = 0



# ─────────────────────────────────────────────
# 🧹 RAM TRIM — स्ट्रीम बंद होने के बाद freed memory को OS को लौटाओ
# Python/glibc free की हुई मेमोरी अपने पास रोक लेता है, इसलिए Koyeb का Memory ग्राफ
# वीडियो बंद होने पर भी ऊँचा दिखता है। सब स्ट्रीम खत्म होने के कुछ सेकंड बाद gc +
# malloc_trim चलाते हैं (सिर्फ़ Linux/glibc पर; वरना चुपचाप skip)।
# ─────────────────────────────────────────────
_trim_task = None

def _trim_now():
    gc.collect()
    try:
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except Exception:
        pass

async def _trim_later(delay=8):
    try:
        await asyncio.sleep(delay)
        if _ACTIVE_STREAMS == 0:
            _trim_now()
    except asyncio.CancelledError:
        pass

def _schedule_trim():
    global _trim_task
    if _trim_task and not _trim_task.done():
        _trim_task.cancel()
    _trim_task = asyncio.ensure_future(_trim_later())

@routes.get("/download/{message_id}")
async def download_handler(request):
    try:
        mid = int(request.match_info['message_id'])
    except ValueError:
        return web.Response(status=400, text="Invalid Message ID")

    if not verify(mid, request.query.get("e"), request.query.get("s")):
        return web.Response(status=403, text="Link expired or invalid", content_type='text/plain')

    # ⚠️ yahan generic `except Exception` jaan-boojhkar nahi hai: body bhejna shuru hone ke baad
    # alag 500 response bhejna possible nahi hota. Setup ke errors media_download khud sambhalta hai.
    return await media_download(request, mid)


async def media_download(request, message_id: int):
    global _ACTIVE_STREAMS

    # ── 1) SETUP (body shuru hone se pehle) — errors par normal 4xx/5xx response ──
    try:
        info = await get_media_info(message_id)      # cache: har Range par Telegram call nahi
        if not info:
            return web.Response(status=404, text="Media Not Supported or Not Found")

        file_size = info.file_size
        file_name = info.file_name
        if not file_name:
            file_name = (
                f"video_{secrets.token_hex(3)}.mp4"
                if info.is_video
                else f"file_{secrets.token_hex(3)}.bin"
            )

        declared_type = (info.mime_type or "").split(";", 1)[0].strip().lower()
        guessed_type = mimetypes.guess_type(file_name)[0]
        # Telegram documents often report octet-stream even when they have a
        # playable extension. Preserve specific types; infer only generic ones.
        mime_type = (guessed_type or ("video/mp4" if info.is_video else "application/octet-stream")) \
            if declared_type in ("", "application/octet-stream", "binary/octet-stream") else declared_type

        # ── Range Header Parse + Clamp/Validate (देखें parse_range) ──
        parsed = parse_range(request.headers.get('Range'), file_size)
        if parsed is None:
            return web.Response(
                status=416,
                body="416: Range Not Satisfiable",
                headers={"Content-Range": f"bytes */{file_size}"}
            )
        fb, ub, req_len, is_partial = parsed

        ncs    = chunk_size(req_len)
        offset = offset_fix(fb, ncs)

        first_cut = fb - offset
        last_cut  = (ub % ncs) + 1
        parts     = math.ceil((req_len + first_cut) / ncs)

        enc_fn = quote(file_name)
        # Only media types may be served inline; other files keep download-only
        # disposition even when a signed URL contains the inline flag.
        disposition = "inline" if request.query.get("inline") == "1" and mime_type.startswith(("video/", "audio/")) else "attachment"
        headers = {
            "Content-Type":        mime_type,
            "Content-Disposition": f'{disposition}; filename="{enc_fn}"; filename*=UTF-8\'\'{enc_fn}',
            "Accept-Ranges":       "bytes",
            "X-Content-Type-Options": "nosniff",
            "Content-Length":      str(req_len),
        }
        if is_partial:
            headers["Content-Range"] = f"bytes {fb}-{ub}/{file_size}"
        status = 206 if is_partial else 200

    except Exception as e:
        logger.error(f"Stream Setup Error: {e}")
        return web.Response(status=500, text="Server Error")

    resp = web.StreamResponse(status=status, headers=headers)

    # HEAD: sirf headers, Telegram se data mangwane ki zaroorat nahi
    if request.method == "HEAD":
        await resp.prepare(request)
        await resp.write_eof()
        return resp

    if _ACTIVE_STREAMS >= MAX_CONNS:
        return web.Response(status=503, text="Server busy, please retry in a few seconds",
                            headers={"Retry-After": "5"})

    # ── 2) STREAMING (backpressure ke saath; prefetch custom_dl.yield_file me hota hai) ──
    _ACTIVE_STREAMS += 1
    agen = None
    try:
        await resp.prepare(request)
        agen = TGCustomYield().yield_file(
            info.file_id_obj, offset, first_cut, last_cut, parts, ncs
        )
        async for chunk in agen:
            await resp.write(chunk)
        await resp.write_eof()
    except ConnectionError:
        pass            # viewer ne tab band kar diya / seek kiya — normal hai
    except Exception as e:
        logger.error(f"Stream Error (mid-body): {e!r}")
        raise           # connection todo, taaki player ko adhoora data 'poora' na lage
    finally:
        _ACTIVE_STREAMS -= 1
        if agen is not None:
            try:
                await agen.aclose()      # pending prefetch tasks cancel
            except Exception:
                pass
        if _ACTIVE_STREAMS == 0:
            _schedule_trim()
    return resp
