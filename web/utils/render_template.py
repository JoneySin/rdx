import urllib.parse, html, logging
from info import URL
from web.utils.media_info import get_media_info
from web.brand import BRAND_MARKUP, BRAND_CSS

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# 🎬 RDXTV AURORA THEATER STREAM TEMPLATE
# ─────────────────────────────────────────────
watch_tmplt = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{heading} — RdxTv</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/plyr@3.8.5/dist/plyr.css"/>
<style>
:root{{
--cyan:#06b6d4; --indigo:#6366f1; --grad:linear-gradient(135deg,#6366f1 0%,#06b6d4 100%);
--glow:rgba(6,182,212,.28); --bg1:#050914; --bg2:#0a1124; --card:#0c152c; --txt:#f1f5f9;
--nav1:rgba(10,17,36,.88); --box:#000; --box-bd:#1f315c;
--btn-c:#132042; --btn-bd:#1f315c; --txt-muted:#8ea4cb;
}}
html.light{{
--cyan:#0284c7; --indigo:#4f46e5; --grad:linear-gradient(135deg,#4f46e5 0%,#0284c7 100%);
--glow:rgba(79,70,229,.20); --bg1:#eff4fc; --bg2:#e4ecf8; --card:#ffffff; --txt:#0b132b;
--nav1:rgba(255,255,255,.90); --box:#000; --box-bd:#cbd8ef;
--btn-c:#e6eef9; --btn-bd:#cbd8ef; --txt-muted:#52658a;
}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{
background-color:var(--bg1);
background-image:
  radial-gradient(ellipse 70% 45% at 18% 0%,rgba(99,102,241,.20),transparent 65%),
  radial-gradient(ellipse 65% 42% at 84% 8%,rgba(6,182,212,.16),transparent 62%);
background-attachment:fixed;
font-family:'Plus Jakarta Sans',sans-serif;color:var(--txt);min-height:100vh;overflow-x:hidden;transition:background .25s,color .25s;
}}
.navbar{{width:100%;padding:15px 4%;display:flex;align-items:center;justify-content:space-between;position:fixed;top:0;z-index:999;background:var(--nav1);border-bottom:1px solid var(--box-bd);backdrop-filter:blur(18px);transition:background .25s;}}
.logo{{font-size:24px;font-weight:900;letter-spacing:.4px;color:var(--txt);display:flex;align-items:center;gap:9px;text-decoration:none;transition:.25s;}}
.logo:hover{{transform:scale(1.02);}}
.theme-btn{{background:var(--btn-c);border:1px solid var(--btn-bd);color:var(--txt);padding:7px 16px;border-radius:999px;font-family:inherit;font-weight:700;font-size:13px;cursor:pointer;transition:.22s;}}
.theme-btn:hover{{border-color:var(--cyan);transform:translateY(-1px);}}
.hero-container{{width:100%;max-width:1180px;margin:auto;padding:96px 20px 44px;}}
.player-box{{width:100%;border-radius:18px;background:var(--box);border:1px solid var(--box-bd);position:relative;box-shadow:0 0 42px var(--glow),0 24px 68px rgba(2,6,23,.68);overflow:hidden;transition:background .3s,border-color .3s;}}
video{{width:100%;height:auto;display:block;}}
.skip-zone{{position:absolute;top:0;bottom:35%;width:30%;z-index:20;display:flex;align-items:center;justify-content:center;cursor:pointer;-webkit-tap-highlight-color:transparent;touch-action:manipulation;}}
.skip-zone.left{{left:0;}} .skip-zone.right{{right:0;}}
.skip-ripple{{position:absolute;inset:0;background:rgba(6,182,212,.18);opacity:0;transition:opacity .3s;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;}}
.skip-zone.left .skip-ripple{{border-radius:0 50% 50% 0/0 100% 100% 0;transform-origin:left center;}}
.skip-zone.right .skip-ripple{{border-radius:50% 0 0 50%/100% 0 0 100%;transform-origin:right center;}}
.skip-zone.active .skip-ripple{{opacity:1;animation:pop .3s cubic-bezier(.25,1,.5,1) forwards;}}
@keyframes pop{{0%{{transform:scaleX(.85);}} 100%{{transform:scaleX(1);}}}}
.skip-text{{color:#fff;font-weight:800;font-size:14px;margin-top:6px;text-shadow:0 2px 8px rgba(0,0,0,.6);letter-spacing:.5px;}}
.skip-arrows svg{{width:28px;height:28px;fill:#fff;filter:drop-shadow(0 2px 6px rgba(0,0,0,.5));}}
.info-section{{margin-top:22px;background:var(--card);border:1px solid var(--box-bd);border-radius:18px;padding:22px 24px;box-shadow:0 12px 34px rgba(2,6,23,.24);}}
.stream-kicker{{display:inline-flex;align-items:center;gap:6px;font-size:10.5px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;color:var(--cyan);background:rgba(6,182,212,.12);border:1px solid rgba(6,182,212,.28);padding:4px 11px;border-radius:999px;margin-bottom:12px;}}
.title{{font-family:'Outfit','Plus Jakarta Sans',sans-serif;font-size:1.55rem;font-weight:800;line-height:1.38;margin-bottom:20px;word-break:break-word;}}
.controls-row{{display:flex;flex-wrap:wrap;gap:12px;}}
.btn{{display:inline-flex;align-items:center;gap:10px;padding:13px 24px;border-radius:12px;text-decoration:none;font-family:'Outfit','Plus Jakarta Sans',sans-serif;font-size:.98rem;font-weight:800;cursor:pointer;transition:.22s;border:none;}} .btn svg{{width:20px;height:20px;}}
.btn-download{{background:var(--grad);color:#fff;box-shadow:0 8px 24px var(--glow);}} .btn-download:hover{{transform:translateY(-2px);filter:brightness(1.08);}}
.btn-copy{{background:var(--btn-c);color:var(--txt);border:1px solid var(--btn-bd);}} .btn-copy:hover{{border-color:var(--cyan);}}
.plyr--video{{--plyr-color-main:#06b6d4;--plyr-video-background:#000;}}
.plyr__control--overlaid,.plyr__control:hover{{background:rgba(6,182,212,.92)!important;}} .plyr__controls{{z-index:30!important;}}
#toast{{visibility:hidden;min-width:220px;background:var(--grad);color:#fff;text-align:center;border-radius:999px;padding:13px 22px;position:fixed;right:24px;bottom:28px;z-index:9999;font-weight:700;font-size:14px;box-shadow:0 10px 30px var(--glow);}}
#toast.show{{visibility:visible;animation:fi .4s,fo .4s 2.6s;}}
@keyframes fi{{from{{opacity:0;bottom:0;}}to{{opacity:1;bottom:28px;}}}} @keyframes fo{{from{{opacity:1;bottom:28px;}}to{{opacity:0;bottom:0;}}}}
@media(max-width:768px){{.hero-container{{padding:84px 12px 32px;}} .logo{{font-size:20px;}} .player-box,.info-section{{border-radius:14px;}} .info-section{{padding:18px 16px;}} .title{{font-size:1.2rem;}} .controls-row{{flex-direction:column;}} .btn{{width:100%;justify-content:center;}}}}
__BRAND_CSS__
</style>
</head>
<body>
<nav class="navbar">
    <a href="/" class="logo watch-brand" aria-label="RdxTv home">__BRAND_MARKUP__</a>
    <button class="theme-btn" id="theme-btn">🌗 Theme</button>
</nav>
<div class="hero-container">
<div class="player-box"><video id="player" playsinline controls><source src="{src}" type="{mime_type}"></video></div>
<div class="info-section">
<div class="stream-kicker">🎬 RdxTv Cinema Stream</div>
<div class="title">{file_name}</div>
<div class="controls-row">
<a href="{src}" class="btn btn-download"><svg fill="currentColor" viewBox="0 0 24 24"><path d="M12 16L7 11H10V4H14V11H17L12 16ZM5 20V18H19V20H5Z"/></svg>Download</a>
<button onclick="copyLink()" class="btn btn-copy"><svg fill="currentColor" viewBox="0 0 24 24"><path d="M16 1H4C2.9 1 2 1.9 2 3V17H4V3H16V1ZM19 5H8C6.9 5 6 5.9 6 7V21C6 22.1 6.9 23 8 23H19C20.1 23 21 22.1 21 21V7C21 5.9 20.1 5 19 5ZM19 21H8V7H19V21Z"/></svg>Copy Link</button>
</div></div></div>
<div id="toast">✅ Stream Link Copied!</div>

<script src="https://cdn.jsdelivr.net/npm/plyr@3.8.5/dist/plyr.min.js"></script>
<script>
const docEl=document.documentElement, themeBtn=document.getElementById('theme-btn');
if(localStorage.getItem('theme')==='light') docEl.classList.add('light');
themeBtn.addEventListener('click',()=>{{
    let isLight = docEl.classList.toggle('light');
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
}});

const player=new Plyr('#player',{{iconUrl:'https://cdn.jsdelivr.net/npm/plyr@3.8.5/dist/plyr.svg',controls:['play-large','play','progress','current-time','mute','settings','pip','fullscreen'],settings:['quality','speed'],autoplay:!1,doubleClick:{{togglesFullscreen:!1}}}});

player.on('enterfullscreen', ()=>{{
    if(screen.orientation && screen.orientation.lock) {{
        screen.orientation.lock('landscape').catch(e => console.log(e));
    }}
}});
player.on('exitfullscreen', ()=>{{
    if(screen.orientation && screen.orientation.unlock) {{
        screen.orientation.unlock();
    }}
}});

player.on('ready',()=>{{
    const c=document.querySelector('.plyr'), l=document.createElement('div'), r=document.createElement('div');
    l.className='skip-zone left'; r.className='skip-zone right';
    const ui=d=>'<div class="skip-ripple"><div class="skip-arrows"><svg viewBox="0 0 24 24">'+d+'</svg></div><div class="skip-text">10s</div></div>';
    l.innerHTML=ui('<path d="M11 18V6l-8.5 6 8.5 6zm.5-6l8.5 6V6l-8.5 6z"/>');
    r.innerHTML=ui('<path d="M4 18l8.5-6L4 6v12zm9-12v12l8.5-6-8.5-6z"/>');
    c.append(l,r);

    let tc=0, tmr;
    const tap=(e,side,z)=>{{
        e.preventDefault(); e.stopPropagation();
        tc++;
        clearTimeout(tmr);
        let t = tc * 10;
        z.querySelector('.skip-text').innerText = t + 's';
        z.classList.remove('active'); void z.offsetWidth; z.classList.add('active');

        tmr = setTimeout(() => {{
            player.currentTime += side === 'l' ? -t : t;
            z.classList.remove('active');
            tc = 0;
        }}, 400);
    }};
    ['dblclick','click'].forEach(ev=>{{l.addEventListener(ev,e=>{{e.preventDefault();e.stopPropagation()}});r.addEventListener(ev,e=>{{e.preventDefault();e.stopPropagation()}})}});
    l.addEventListener('pointerup',e=>tap(e,'l',l)); r.addEventListener('pointerup',e=>tap(e,'r',r));
}});

function copyLink(){{navigator.clipboard.writeText("{src}"); let t=document.getElementById("toast"); t.classList.add("show"); setTimeout(()=>t.classList.remove("show"),3000);}}
</script>
</body></html>"""


async def media_watch(message_id, query=""):
    try:
        info = await get_media_info(message_id)
        if not info:
            return "<h2 style='color:#f1f5f9;text-align:center;padding:50px;'>❌ File Not Found</h2>"

        src = urllib.parse.urljoin(URL, f'download/{message_id}')
        if query:
            src += f'?{query}'
        mime = info.mime_type or 'video/mp4'

        if mime.split('/')[0].strip() == 'video':
            fn = html.escape(info.file_name or "RdxTv Stream")
            return (watch_tmplt.format(heading=f"Watch {fn}", file_name=fn, src=src, mime_type=html.escape(mime))
                    .replace("__BRAND_CSS__", BRAND_CSS).replace("__BRAND_MARKUP__", BRAND_MARKUP))

        return (
            f'<body style="background:#050914;color:#f1f5f9;display:flex;align-items:center;justify-content:center;height:100vh;font-family:\'Plus Jakarta Sans\',sans-serif;">'
            f'<div style="text-align:center;background:#0c152c;padding:40px;border-radius:18px;border:1px solid #1f315c;box-shadow:0 24px 60px rgba(2,6,23,.65);">'
            f'<h2>📦 Direct Download Ready</h2><br>'
            f'<a href="{src}" style="background:linear-gradient(135deg,#6366f1,#06b6d4);color:#fff;padding:12px 26px;border-radius:12px;text-decoration:none;font-weight:800;display:inline-block;">⬇️ Download Direct</a>'
            f'</div></body>'
        )
    except Exception as e:
        logger.error(f"Watch Error: {e}")
        return "<h2 style='color:#f43f5e;text-align:center;'>Server Error</h2>"
