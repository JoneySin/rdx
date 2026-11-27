from web.media_cards import MEDIA_CARD_JS
from web.brand import BRAND_MARKUP, BRAND_CSS
import time
import html
import orjson
from aiohttp import web
from info import ADMINS
from utils import temp
from database.users_chats_db import db as user_db, web_db
from web.player_assets import PLAYER_UI


def fast_json(data):
    """Serialize Python structures to UTF-8 JSON string via orjson."""
    return orjson.dumps(data).decode('utf-8')


DEFAULT_VIEW_MODE = "text"  # "text" or "poster"
DEFAULT_CATALOG_MODE = DEFAULT_VIEW_MODE
DEFAULT_MEDIA_MODE = "none" if DEFAULT_VIEW_MODE == "text" else "tg"

# Shared filter controls for the home, profile directory and post directory pages.
DIRECTORY_FILTER_CSS = """<style>
        .cdd-wrap { position: relative; background: var(--bg3); border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px; cursor: pointer; font-weight: 700; font-size: 13px; color: var(--text); flex: 1; min-width: 100px; display: flex; justify-content: space-between; align-items: center; user-select: none; transition: border-color .2s, background .2s, transform .15s; }
        .cdd-wrap:hover { border-color: var(--accent-cyan); background: var(--bg4); }
        .cdd-arrow { font-size:10px; color:var(--muted); }
        .cdd-menu { position: absolute; top: calc(100% + 6px); left: 0; right: 0; background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; z-index: 100; display: none; box-shadow: 0 14px 36px rgba(2,6,23,0.45); backdrop-filter: blur(16px); }
        .cdd-item { padding: 10px 14px; border-bottom: 1px solid var(--border); transition: 0.18s; font-weight: 600; }
        .cdd-item:last-child { border-bottom: none; }
        .cdd-item:hover { background: var(--bg3); color: var(--accent-cyan); }
        .cdd-item.selected { color: var(--accent-cyan); background: rgba(6,182,212,0.08); }
</style>"""

DIRECTORY_CSS = """
    <style>
        .dir-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
        @media(min-width: 768px) { .dir-grid { grid-template-columns: repeat(5, 1fr); gap: 20px; } }

        .s-row-1 { display: flex; gap: 10px; margin-bottom: 12px; position: relative; }
        .s-input { flex: 1; background:var(--bg3); border:1px solid var(--border); padding:12px 16px; color:var(--text); border-radius:11px; outline:none; font-family:inherit; font-weight:600; font-size:14px; transition:border-color .2s, box-shadow .2s; }
        .s-input:focus { border-color:var(--accent-cyan); box-shadow:0 0 0 3px var(--accent-glow); }
        .s-spinner { display:none; position:absolute; right:14px; top:50%; transform:translateY(-50%); width:16px; height:16px; border:2px solid var(--border); border-top-color:var(--accent-cyan); border-radius:50%; animation:sSpin .6s linear infinite; }
        .s-row-1.loading .s-spinner { display:block; }
        @keyframes sSpin { to { transform:translateY(-50%) rotate(360deg); } }
        .s-btn { background:var(--accent-grad); color:#fff; border:none; padding:0 24px; border-radius:11px; font-weight:800; cursor:pointer; transition:transform .18s, box-shadow .2s, filter .2s; white-space:nowrap; box-shadow:0 6px 18px var(--accent-glow); }
        .s-btn:hover { filter:brightness(1.08); transform:translateY(-1px); }

        .s-row-2 { display: flex; gap: 10px; flex-wrap:wrap; align-items:center; }
    </style>
""" + DIRECTORY_FILTER_CSS + """
    <style>
        .pg-bar { display:flex; justify-content:center; align-items:center; gap:14px; margin-top:30px; }
        .pg-btn { background:var(--bg4); color:var(--text); border:1px solid var(--border); padding:9px 20px; border-radius:10px; font-weight:700; cursor:pointer; font-size:13px; transition:0.2s; }
        .pg-btn:hover:not(:disabled) { background:var(--accent-grad); color:#fff; border-color:transparent; box-shadow:0 6px 18px var(--accent-glow); }
        .pg-btn:disabled { opacity:0.4; cursor:not-allowed; }
        .pg-info { color:var(--text); font-weight:800; font-size:13px; background:var(--bg3); padding:7px 15px; border-radius:10px; border:1px solid var(--border); }

        /* Text View mode overrides */
        .card-body { display: none; }
        .grid-text-mode .poster-wrap { display: none !important; }
        .grid-text-mode .act-card { display:flex; align-items:center; padding:6px; background:var(--card); border-radius:14px; }
        .grid-text-mode .card-body { display: block !important; text-align:left !important; padding:10px 15px !important; flex:1; }
    </style>
"""

# ----------------- RDXTV AURORA CYBER-SAPPHIRE DESIGN SYSTEM -----------------
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#050914;
  --bg2:#0a1124;
  --bg3:#111c38;
  --bg4:#19284c;
  --card:#0c152c;
  --border:#1f315c;
  --accent:#6366f1;
  --accent-hover:#4f46e5;
  --accent-cyan:#06b6d4;
  --accent-grad:linear-gradient(135deg,#6366f1 0%,#06b6d4 100%);
  --accent-glow:rgba(99,102,241,.28);
  --panel-shadow:0 12px 34px rgba(2,6,23,.38);
  --text:#f1f5f9;
  --muted:#8ea4cb;
  --sidebar-w:272px;
  --primary-p:0%;
  --cloud-p:0%;
  --archive-p:0%;
}
.light{
  --bg:#eff4fc;
  --bg2:#ffffff;
  --bg3:#e6eef9;
  --bg4:#d4e0f3;
  --card:#ffffff;
  --border:#cbd8ef;
  --accent:#4f46e5;
  --accent-hover:#4338ca;
  --accent-cyan:#0284c7;
  --accent-grad:linear-gradient(135deg,#4f46e5 0%,#0284c7 100%);
  --accent-glow:rgba(79,70,229,.20);
  --panel-shadow:0 10px 28px rgba(15,23,42,.07);
  --text:#0b132b;
  --muted:#52658a;
}
body{
  font-family:'Plus Jakarta Sans',sans-serif;
  background-color:var(--bg);
  background-image:
    radial-gradient(ellipse 75% 45% at 12% -8%,rgba(99,102,241,.16),transparent 65%),
    radial-gradient(ellipse 65% 40% at 88% -5%,rgba(6,182,212,.13),transparent 62%);
  background-attachment:fixed;
  color:var(--text);
  min-height:100vh;
  overflow-x:hidden;
  transition:background-color .22s,color .22s;
}
.light body,html.light body{
  background-image:
    radial-gradient(ellipse 75% 45% at 12% -8%,rgba(79,70,229,.09),transparent 65%),
    radial-gradient(ellipse 65% 40% at 88% -5%,rgba(2,132,199,.08),transparent 62%);
}
h1,h2,h3{font-family:'Outfit','Plus Jakarta Sans',sans-serif}

/* ── Topbar & Desktop Quick-Nav ── */
.topbar{
  background:rgba(10,17,36,.84);
  backdrop-filter:blur(18px) saturate(160%);
  -webkit-backdrop-filter:blur(18px) saturate(160%);
  padding:0 4%;
  display:flex;
  align-items:center;
  height:68px;
  position:sticky;
  top:0;
  z-index:100;
  gap:14px;
  box-shadow:0 8px 28px rgba(2,6,23,.32);
  border-bottom:1px solid var(--border);
}
.light .topbar{background:rgba(255,255,255,.86);box-shadow:0 4px 20px rgba(15,23,42,.06)}
.ham-btn{background:var(--bg3);border:1px solid var(--border);border-radius:10px;cursor:pointer;color:var(--text);display:flex;flex-direction:column;justify-content:center;align-items:center;gap:4px;width:38px;height:38px;padding:0;flex-shrink:0;transition:border-color .2s,background .2s}
.ham-btn:hover{border-color:var(--accent-cyan);background:var(--bg4)}
.ham-line{width:18px;height:2px;border-radius:2px;background:currentColor;transition:.2s}
.logo{font-size:20px;font-weight:900;letter-spacing:.4px;color:var(--text);display:flex;align-items:center;gap:9px;text-decoration:none;flex:0 1 auto;min-width:0}
.tb-nav{display:none;align-items:center;gap:6px;margin-left:14px;padding:4px;border-radius:999px;background:var(--bg3);border:1px solid var(--border)}
@media(min-width:980px){.tb-nav{display:flex}}
.tb-nav-link{display:inline-flex;align-items:center;gap:6px;padding:6px 13px;border-radius:999px;text-decoration:none;color:var(--muted);font-size:12.5px;font-weight:700;transition:color .18s,background .18s,box-shadow .18s;white-space:nowrap}
.tb-nav-link:hover{color:var(--text);background:var(--bg4)}
.tb-nav-link.active{background:var(--accent-grad);color:#fff;box-shadow:0 4px 14px var(--accent-glow)}
.topbar-right{margin-left:auto;display:flex;align-items:center;gap:8px;flex-shrink:0}
.theme-btn{background:var(--bg3);border:1px solid var(--border);border-radius:999px;padding:7px 14px;font-family:inherit;font-size:12px;font-weight:700;color:var(--text);cursor:pointer;transition:border-color .2s,background .2s,transform .15s}
.theme-btn:hover{background:var(--bg4);border-color:var(--accent-cyan);transform:translateY(-1px)}

/* ── Slide-out Frosted Sidebar ── */
.sidebar-overlay{position:fixed;inset:0;background:rgba(2,6,23,.72);backdrop-filter:blur(4px);z-index:150;opacity:0;pointer-events:none;transition:.22s}
.sidebar-overlay.open{opacity:1;pointer-events:all}
.sidebar{position:fixed;top:0;left:0;height:100%;width:var(--sidebar-w);background:var(--bg2);border-right:1px solid var(--border);z-index:160;display:flex;flex-direction:column;transform:translateX(-100%);transition:transform .28s cubic-bezier(.22,1,.36,1);box-shadow:18px 0 48px rgba(2,6,23,.5)}
.sidebar.open{transform:translateX(0)}
.sb-header{padding:18px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.sb-logo{font-size:17px;font-weight:900;color:var(--text);display:flex;align-items:center;gap:8px}
.sb-close{background:var(--bg3);border:1px solid var(--border);border-radius:9px;width:32px;height:32px;color:var(--muted);font-size:16px;cursor:pointer;display:grid;place-items:center;transition:.18s}
.sb-close:hover{color:var(--text);border-color:var(--accent-cyan)}
.sb-nav{padding:16px 12px;flex:1;overflow-y:auto}
.sb-section{font-size:10.5px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;color:var(--muted);padding:6px 12px 10px}
.sb-link{display:flex;align-items:center;gap:11px;padding:11px 14px;border-radius:12px;text-decoration:none;color:var(--muted);font-size:14.5px;font-weight:600;margin-bottom:5px;transition:background .18s,color .18s,transform .15s}
.sb-link:hover{background:var(--bg3);color:var(--text);transform:translateX(2px)}
.sb-link.active{background:var(--accent-grad);color:#fff;font-weight:700;box-shadow:0 6px 18px var(--accent-glow)}
.sb-icon{width:22px;flex:0 0 22px;text-align:center;line-height:1;font-size:17px}
.sb-footer{padding:14px 12px;border-top:1px solid var(--border)}
.sb-logout{display:flex;align-items:center;justify-content:center;gap:8px;padding:11px;border-radius:12px;text-align:center;text-decoration:none;color:var(--text);font-weight:700;font-size:13.5px;background:var(--bg3);border:1px solid var(--border);transition:.18s}
.sb-logout:hover{border-color:#f43f5e;color:#fb7185;background:rgba(244,63,94,.08)}

/* ── Shared App Containers ── */
.main{padding:18px 4% 44px;max-width:1400px;margin:0 auto}
.search-box{background:var(--card);border:1px solid var(--border);padding:16px;border-radius:16px;margin-bottom:20px;box-shadow:var(--panel-shadow)}

/* ── Legacy Stat Utilities ── */
.search-zone{padding:16px 4% 0;background:transparent}
.search-row{display:flex;gap:10px;flex-wrap:wrap}
.search-wrap{flex:1;position:relative;min-width:200px}
.s-icon{position:absolute;left:15px;top:50%;transform:translateY(-50%);color:var(--muted)}
.search-input{width:100%;background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:12px 15px 12px 42px;color:var(--text);font-size:15px;outline:0}
.search-btn{background:var(--accent-grad);color:#fff;border:0;border-radius:10px;padding:12px 24px;font-weight:700;cursor:pointer}
.stats-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-bottom:30px}
.scard{background:var(--card);padding:24px;border-radius:16px;position:relative;box-shadow:var(--panel-shadow);border:1px solid var(--border);transition:0.25s}
.scard:hover{transform:translateY(-3px);border-color:var(--accent-cyan)}
.scard-label{font-size:12px;font-weight:700;color:var(--muted);margin-bottom:10px;text-transform:uppercase;letter-spacing:1px}
.scard-val{font-size:36px;font-weight:900;color:var(--text);margin-bottom:8px;font-family:'JetBrains Mono',monospace}
.scard-sub{font-size:13px;color:var(--muted);display:flex;justify-content:space-between;align-items:center}
.big-stat{background:linear-gradient(135deg,var(--card) 0%,var(--bg2) 100%);padding:40px 20px;border-radius:16px;text-align:center;margin-bottom:30px;border:1px solid var(--border);box-shadow:var(--panel-shadow)}
.big-stat-val{font-size:64px;font-weight:900;color:var(--accent-cyan);margin-bottom:10px;letter-spacing:-1px;font-family:'JetBrains Mono',monospace}
.big-stat-label{font-size:14px;color:var(--muted);font-weight:700;letter-spacing:2.5px;text-transform:uppercase}
.custom-progress-container{width:100%;height:6px;background:var(--bg4);border-radius:999px;margin:12px 0 6px;overflow:hidden}
.custom-progress-bar{height:100%;border-radius:999px;transition:width 1s cubic-bezier(0.4,0,0.2,1)}
.custom-progress-bar.primary-fill{background:#6366f1;width:var(--primary-p)}
.custom-progress-bar.cloud_fill{background:#06b6d4;width:var(--cloud-p)}
.custom-progress-bar.archive-fill{background:#a855f7;width:var(--archive-p)}
.mode-none .poster-box{display:none}

/* ── Empty State & Toast ── */
.empty{text-align:center;padding:80px 20px;color:var(--muted);grid-column:1/-1}
.empty-icon{font-size:42px;margin-bottom:14px}
.toast{position:fixed;bottom:22px;right:22px;background:var(--accent-grad);color:#fff;padding:12px 22px;border-radius:999px;font-weight:700;font-size:13px;z-index:300;transform:translateX(150%);transition:.3s cubic-bezier(.22,1,.36,1);box-shadow:0 10px 30px rgba(6,182,212,.35)}
.toast.show{transform:translateX(0)}
.toast.error{background:#0f172a;border:1px solid #f43f5e;color:#fda4af;box-shadow:0 10px 30px rgba(244,63,94,.25)}

/* ── Auth Portal (Pure CSS Aurora Cyber-Cinema Mesh — Zero External Stock URLs) ── */
.login-bg{
  background-color:var(--bg);
  background-image:
    radial-gradient(circle at 18% 18%,rgba(99,102,241,.28) 0%,transparent 45%),
    radial-gradient(circle at 82% 22%,rgba(6,182,212,.24) 0%,transparent 46%),
    radial-gradient(circle at 50% 88%,rgba(168,85,247,.16) 0%,transparent 50%),
    linear-gradient(rgba(142,164,203,.05) 1px,transparent 1px),
    linear-gradient(90deg,rgba(142,164,203,.05) 1px,transparent 1px);
  background-size:100% 100%,100% 100%,100% 100%,38px 38px,38px 38px;
  min-height:100vh;
  display:flex;
  flex-direction:column;
}
.light .login-bg{
  background-color:var(--bg);
  background-image:
    radial-gradient(circle at 18% 18%,rgba(79,70,229,.15) 0%,transparent 45%),
    radial-gradient(circle at 82% 22%,rgba(2,132,199,.14) 0%,transparent 46%),
    linear-gradient(rgba(15,23,42,.04) 1px,transparent 1px),
    linear-gradient(90deg,rgba(15,23,42,.04) 1px,transparent 1px);
  background-size:100% 100%,100% 100%,38px 38px,38px 38px;
}
.login-wrap{flex:1;display:flex;align-items:center;justify-content:center;padding:88px 20px 36px;min-height:100vh}
.login-card{position:relative;overflow:hidden;background:rgba(12,21,44,.86);backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px);padding:42px 38px;border-radius:22px;width:100%;max-width:450px;box-shadow:0 24px 64px rgba(2,6,23,.55);border:1px solid var(--border)}
.light .login-card{background:rgba(255,255,255,.92);box-shadow:0 20px 52px rgba(15,23,42,.10)}
.login-card::before{content:"";position:absolute;top:0;left:0;right:0;height:4px;background:var(--accent-grad)}
.auth-kicker{display:inline-flex;align-items:center;gap:6px;font-size:10.5px;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;color:var(--accent-cyan);background:rgba(6,182,212,.1);border:1px solid rgba(6,182,212,.25);padding:4px 10px;border-radius:999px;margin-bottom:12px}
.login-card h2{font-size:30px;font-weight:800;letter-spacing:-.4px;margin-bottom:10px;color:var(--text)}
.auth-sub{color:var(--muted);font-size:13.5px;line-height:1.55;margin-bottom:22px}
.login-card input{width:100%;background:var(--bg);border:1px solid var(--border);padding:14px 16px;color:var(--text);margin-bottom:14px;border-radius:12px;outline:none;font-family:inherit;font-size:14px;transition:border-color .2s,box-shadow .2s}
.login-card input:focus{border-color:var(--accent-cyan);box-shadow:0 0 0 3px var(--accent-glow)}
.login-card .submit-btn{width:100%;background:var(--accent-grad);color:#fff;border:0;padding:15px;font-family:'Outfit','Plus Jakarta Sans',sans-serif;font-size:15px;font-weight:800;letter-spacing:.3px;margin-top:10px;border-radius:12px;cursor:pointer;box-shadow:0 10px 26px var(--accent-glow);transition:transform .18s,filter .18s}
.login-card .submit-btn:hover{transform:translateY(-1px);filter:brightness(1.08)}
.login-card .submit-btn.alt{background:var(--bg3);color:var(--text);border:1px solid var(--border);box-shadow:none}
.login-card .submit-btn.alt:hover{border-color:var(--accent-cyan);background:var(--bg4)}
.auth-links{margin-top:20px;display:flex;justify-content:space-between;align-items:center;font-size:13.5px}
.auth-link-muted{color:var(--muted);text-decoration:none;font-weight:600;transition:color .18s}
.auth-link-muted:hover{color:var(--text)}
.auth-link-strong{color:var(--accent-cyan);text-decoration:none;font-weight:800}
.auth-link-strong:hover{text-decoration:underline}
.err-box{background:rgba(245,158,11,.15);border:1px solid rgba(245,158,11,.45);color:#fbbf24;padding:11px 16px;border-radius:10px;margin-bottom:16px;font-size:13px;font-weight:600}
.light .err-box{color:#b45309;background:rgba(245,158,11,.12)}
.success-box{background:rgba(16,185,129,.15);border:1px solid rgba(16,185,129,.45);color:#34d399;padding:11px 16px;border-radius:10px;margin-bottom:16px;font-size:13px;font-weight:600}
.light .success-box{color:#047857;background:rgba(16,185,129,.12)}

/* ── Modals & File Editor ── */
.edit-modal{position:fixed;inset:0;background:rgba(2,6,23,.82);backdrop-filter:blur(8px);z-index:200;display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;transition:.2s;overflow-y:auto;padding:20px 10px}
.edit-modal.open{opacity:1;pointer-events:all}
.em-card{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:25px;width:100%;max-width:480px;box-shadow:0 24px 64px rgba(2,6,23,.65);position:relative;margin:auto}
.em-close{position:absolute;top:15px;right:20px;background:0 0;border:0;color:var(--muted);font-size:24px;cursor:pointer;z-index:10}
.em-title{font-size:18px;font-weight:800;margin-bottom:20px;display:flex;align-items:center;gap:8px}
.em-input{width:100%;background:var(--bg);border:1px solid var(--border);padding:12px;color:var(--text);margin-bottom:15px;border-radius:10px;outline:none;font-size:14px;transition:border-color .2s}
.em-input:focus{border-color:var(--accent-cyan)}
.thumb-preview-box{width:100%;aspect-ratio:16/9;background:var(--bg3);border:1px solid var(--border);border-radius:10px;margin-bottom:15px;overflow:hidden;position:relative;display:flex;align-items:center;justify-content:center}
.t-prev-img{max-width:100%;max-height:100%;object-fit:contain}
.em-upload-btn{display:block;text-align:center;background:var(--bg4);border:1px dashed var(--border);padding:12px;border-radius:10px;cursor:pointer;font-weight:700;font-size:13px;margin-bottom:20px;transition:0.2s}
.em-upload-btn:hover{background:var(--bg3);border-color:var(--accent-cyan)}
.em-save-btn{width:100%;background:var(--accent-grad);color:#fff;border:0;padding:14px;font-weight:800;border-radius:10px;cursor:pointer;font-size:15px;transition:0.2s;box-shadow:0 6px 20px var(--accent-glow)}
.em-save-btn:hover{filter:brightness(1.08)}
.em-save-btn:disabled{opacity:.5;cursor:not-allowed;box-shadow:none}
.cropper-container-box{width:100%;aspect-ratio:16/9;margin-bottom:15px;border-radius:10px;overflow:hidden;display:none;background:#000;position:relative}
.cropper-container-box cropper-canvas{position:absolute;inset:0;width:100%;height:100%}

/* Shared destination group preview */
.target-preview{border:1px solid rgba(6,182,212,.45);border-radius:12px;background:var(--bg3);padding:12px;margin-top:10px;color:var(--text)}
.target-head{display:flex;align-items:flex-start;gap:12px;min-width:0}.target-image-wrap{flex:0 0 96px;min-width:0;text-align:center}
.target-image{position:relative;display:flex;align-items:center;justify-content:center;aspect-ratio:16/9;border-radius:8px;overflow:hidden;background:var(--bg4);color:var(--muted);font-size:22px}
.target-image img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.target-image-wrap small{display:block;color:var(--muted);font-size:10px;margin-top:4px}
.target-overline{display:block;color:var(--accent-cyan);font-size:10px;font-weight:800;letter-spacing:.7px;text-transform:uppercase;margin-bottom:4px}
.target-meta{min-width:0;flex:1}.target-name{font-size:15px;font-weight:800;line-height:1.35;overflow-wrap:anywhere}.target-badges{display:flex;flex-wrap:wrap;gap:5px;margin-top:7px}
.target-badge{border-radius:6px;background:var(--bg4);color:var(--text);padding:4px 7px;font-size:10px;font-weight:800;overflow-wrap:anywhere}.target-badge.id{background:rgba(99,102,241,.2);color:#c7d2fe}.target-badge.kind{background:rgba(6,182,212,.18);color:#a5f3fc}
@media(max-width:480px){.target-image-wrap{flex-basis:76px}}

/* File editor — scoped */
#editCombinedModal .file-editor{max-width:760px;max-height:calc(100dvh - 32px);overflow-y:auto;padding:0;border-radius:20px;background:var(--bg2);box-shadow:0 28px 80px rgba(2,6,23,.65)}
.file-editor-head{padding:25px 28px 21px;border-bottom:1px solid var(--border);background:linear-gradient(115deg,rgba(99,102,241,.14),rgba(6,182,212,.06) 55%,transparent 80%)}
.file-editor-kicker{font-size:10px;letter-spacing:1.5px;text-transform:uppercase;font-weight:900;color:var(--accent-cyan)}
.file-editor-head .em-title{margin:7px 38px 5px 0;font-size:22px;line-height:1.2}.file-editor-head p,.file-editor-help{font-size:12px;line-height:1.55;color:var(--muted)}
#editCombinedModal .em-close{top:17px;right:18px;width:36px;height:36px;border:1px solid var(--border);border-radius:10px;background:var(--bg3);font-size:18px}
.file-editor-content{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px;padding:24px 28px}
.file-editor-section{min-width:0}.file-editor-section-head{display:flex;gap:10px;align-items:flex-start;margin-bottom:17px}.file-editor-number{display:grid;place-items:center;flex:none;width:29px;height:29px;border-radius:9px;background:rgba(99,102,241,.16);color:var(--accent-cyan);font-size:11px;font-weight:900;border:1px solid rgba(99,102,241,.3)}.file-editor-section-head h3{font-size:14px;line-height:1.3}.file-editor-section-head p{font-size:11px;color:var(--muted);margin-top:3px;line-height:1.4}
.file-editor-field{display:block;margin-bottom:15px;font-size:12px;font-weight:700;color:var(--text)}.file-editor-field .em-input{margin:7px 0 0;border-radius:10px;font-family:inherit;line-height:1.4}.file-editor-field small{display:block;margin-top:6px;color:var(--muted);font-weight:400;line-height:1.45}.file-editor-field select{cursor:pointer}
.file-editor-art{padding:16px;border:1px solid var(--border);border-radius:14px;background:var(--card)}.file-editor-art .thumb-preview-box,.file-editor-art .cropper-container-box{border-radius:10px;margin-bottom:12px}.file-editor-art .thumb-preview-box{color:var(--muted);font-size:12px;text-align:center}.file-editor-art .em-upload-btn{position:relative;overflow:hidden;margin:0;padding:11px;border-radius:10px;background:var(--bg3)}.file-editor-art .em-upload-btn:focus-within{outline:2px solid var(--accent-cyan);outline-offset:2px}.file-editor-art input[type=file]{position:absolute;inset:0;width:100%;height:100%;opacity:0;cursor:pointer}.file-editor-art .file-editor-help{margin-top:9px;overflow-wrap:anywhere}
.file-editor-group{border-top:1px solid var(--border);padding:20px 28px}.file-editor-group-row{display:flex;gap:8px;align-items:flex-end}.file-editor-group-row label{flex:1;min-width:0;margin:0}.file-editor-group button,.file-editor-retry{border:1px solid var(--border);border-radius:10px;background:var(--bg3);color:var(--text);padding:11px 14px;font-family:inherit;font-size:12px;font-weight:700;cursor:pointer}.file-editor-group button:disabled,.file-editor-retry:disabled{opacity:.5;cursor:not-allowed}.file-editor-group-status{font-size:12px;line-height:1.5;color:var(--muted);margin-top:9px;overflow-wrap:anywhere}.file-editor-group-status.error,.file-editor-load.error{color:#f43f5e}.file-editor-group-confirm{display:flex;gap:8px;align-items:flex-start;font-size:12px;line-height:1.5;margin:10px 0}.file-editor-group-confirm input{margin-top:3px}.file-editor-group-preview[hidden],.file-editor-group-confirm[hidden],.file-editor-retry[hidden]{display:none}.file-editor-load{font-size:12px;color:var(--muted);margin-top:8px}.file-editor-retry{margin-top:8px}
.file-editor-footer{display:flex;align-items:center;justify-content:flex-end;gap:10px;padding:16px 28px;border-top:1px solid var(--border)}.file-editor-footer button{font-family:inherit}.file-editor-cancel{background:var(--bg3);border:1px solid var(--border);border-radius:10px;padding:12px 18px;color:var(--text);font-size:13px;font-weight:700;cursor:pointer}.file-editor-footer .em-save-btn{width:auto;min-width:150px;border-radius:10px;padding:12px 20px;font-size:13px}
@media(max-width:600px){#editCombinedModal .file-editor{max-height:calc(100dvh - 20px)}.file-editor-head{padding:21px 18px 17px}.file-editor-content{grid-template-columns:1fr;gap:8px;padding:20px 18px}.file-editor-group{padding:18px}.file-editor-footer{padding:14px 18px}.file-editor-footer .em-save-btn{flex:1;min-width:0}}

/* --- Global Admin Edit Buttons --- */
.poster-admin{position:absolute;bottom:0;left:0;right:0;display:flex;gap:6px;padding:8px;opacity:0;visibility:hidden;transform:translateY(8px);transition:opacity .2s ease,transform .22s ease;pointer-events:none;z-index:4}
.file-card.admin-active .poster-admin{opacity:1;visibility:visible;transform:translateY(0);pointer-events:all}
.text-admin-row{display:none;gap:5px;padding:6px 12px 0;flex-wrap:wrap}
.file-card.admin-active .text-admin-row{display:flex}
.text-file-trigger:focus-visible,.grp-textinfo[role=button]:focus-visible,.grp-openhead[data-text-trigger]:focus-visible{outline:2px solid var(--accent-cyan);outline-offset:-3px}
.file-poster-trigger,.group-poster-trigger{position:absolute;inset:0;z-index:3;width:100%;height:100%;border:0;padding:0;background:transparent;cursor:pointer}
.file-poster-trigger:focus-visible,.group-poster-trigger:focus-visible{outline:3px solid var(--accent-cyan);outline-offset:-4px}
.fc-name:focus-visible{outline:2px solid var(--accent-cyan);outline-offset:2px}
.btn-edit,.btn-del{flex:1;padding:6px 0;border-radius:8px;font-size:11px;font-weight:700;cursor:pointer;transition:background .14s,transform .1s;border:none}
.btn-edit{background:rgba(255,255,255,.18);backdrop-filter:blur(10px);color:var(--text);border:1px solid rgba(255,255,255,.34)}
.btn-edit:hover{background:rgba(255,255,255,.30);border-color:rgba(255,255,255,.55)}
.btn-del{background:rgba(244,63,94,.88);backdrop-filter:blur(10px);color:#fff;border:1px solid rgba(255,255,255,.22)}
.btn-del:hover{background:#e11d48;border-color:#e11d48}
/* Light theme: frosted-white edit controls, solid accent destructive controls. */
.light .btn-edit{background:rgba(255,255,255,.96);color:var(--text);border-color:rgba(11,19,43,.16);box-shadow:0 2px 8px rgba(15,23,42,.10)}
.light .btn-edit:hover{background:var(--bg3);color:var(--accent);border-color:var(--accent)}
.light .btn-del{background:var(--accent);color:#fff;border-color:var(--accent)}
.light .btn-del:hover{background:var(--accent-hover);border-color:var(--accent-hover)}

/* ── MASTER UNIVERSAL ASSET CARD & GRID ── */
.res-grid{display:grid;grid-template-columns:1fr;gap:8px;margin-bottom:26px}
@media(min-width:600px){.res-grid{grid-template-columns:repeat(3,1fr);gap:16px}}
.res-grid.mode-none .poster-box{display:none}

.file-card{background:var(--card);border-radius:15px;overflow:hidden;border:1px solid var(--border);display:flex;flex-direction:column;transition:all .28s cubic-bezier(.22,1,.36,1);cursor:pointer;position:relative;box-shadow:0 6px 20px rgba(2,6,23,.24)}
.light .file-card{box-shadow:0 4px 16px rgba(15,23,42,.06)}
.file-card:hover{transform:translateY(-5px) scale(1.015);border-color:var(--accent-cyan);box-shadow:0 18px 38px rgba(2,6,23,.52),0 0 20px var(--accent-glow);z-index:2}
.file-card:active{transform:scale(.97);transition:transform .1s}

@keyframes cardEnter{
  0%  {opacity:0;transform:translateY(30px) scale(0.95)}
  60% {opacity:1;transform:translateY(-3px) scale(1.01)}
  100%{opacity:1;transform:translateY(0) scale(1)}
}
.card-enter{opacity:0}
.card-enter.card-visible{animation:cardEnter .55s cubic-bezier(.22,1,.36,1) forwards}

.poster-box{position:relative;padding-top:56.25%;background:linear-gradient(90deg,var(--bg3) 0px,var(--bg4) 50%,var(--bg3) 100%);background-size:200% 100%;animation:shimmer 1.6s infinite linear;overflow:hidden;width:100%}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}

.fc-poster{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0;transition:opacity .3s ease,transform .5s cubic-bezier(.22,1,.36,1)}
.fc-poster.loaded{opacity:1}
.file-card:hover .fc-poster{transform:scale(1.07)}

.thumb-error{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:var(--bg3);z-index:2}
.poster-top{position:absolute;top:0;left:0;right:0;display:flex;align-items:center;gap:5px;padding:8px;z-index:3;background:linear-gradient(to bottom,rgba(5,9,20,.65),transparent)}
.type-chip{background:rgba(131,24,67,.85);color:#fbcfe8;border:1px solid rgba(236,72,153,.55);border-radius:6px;padding:3px 9px;font-size:10px;font-weight:800;letter-spacing:.7px;line-height:1.4;backdrop-filter:blur(6px)}
.size-chip{background:rgba(49,46,129,.86);color:#c7d2fe;border:1px solid rgba(129,140,248,.5);border-radius:6px;padding:3px 8px;font-size:10px;font-weight:800;line-height:1.4;backdrop-filter:blur(6px)}
.dur-chip{background:rgba(15,118,110,.86);color:#99f6e4;border:1px solid rgba(45,212,191,.5);border-radius:6px;padding:3px 8px;font-size:10px;font-weight:800;letter-spacing:.3px;line-height:1.4;font-variant-numeric:tabular-nums;backdrop-filter:blur(6px)}
.dur-chip::before{content:"\\23F1\\00a0";font-size:9px;opacity:.8}
.tc-dur{background:rgba(15,118,110,.16);color:#2dd4bf;border:1px solid rgba(45,212,191,.38);border-radius:6px;padding:2px 8px;font-size:11px;font-weight:800;line-height:1.5;font-variant-numeric:tabular-nums}
.light .tc-dur{color:#0f766e;background:rgba(15,118,110,.10)}
.tc-dur::before{content:"\\23F1\\00a0";font-size:10px}
.res-chip{background:rgba(8,47,73,.88);color:#7dd3fc;border-radius:6px;padding:3px 8px;font-size:10px;font-weight:800;letter-spacing:.3px;border:1px solid rgba(56,189,248,.5);line-height:1.4;backdrop-filter:blur(6px)}
.tc-res{background:rgba(2,132,199,.15);color:#38bdf8;border:1px solid rgba(56,189,248,.38);border-radius:6px;padding:2px 8px;font-size:11px;font-weight:800;line-height:1.5}
.light .tc-res{color:#0369a1;background:rgba(2,132,199,.10)}
.res-chip,.tc-res{max-width:100%;min-width:0;overflow-wrap:anywhere}
.source-pill{margin-left:auto;border-radius:999px;padding:3px 8px;font-size:9px;font-weight:800;letter-spacing:.4px;display:inline-flex;align-items:center;gap:4px;backdrop-filter:blur(8px)}
.source-pill.primary{background:rgba(20,83,45,.85);color:#86efac;border:1px solid rgba(34,197,94,.55)}
.source-pill.cloud{background:rgba(30,58,138,.85);color:#93c5fd;border:1px solid rgba(96,165,250,.55)}
.source-pill.archive{background:rgba(124,45,18,.85);color:#fdba74;border:1px solid rgba(251,146,60,.55)}
.light .source-pill.primary{background:rgba(22,163,74,.14);color:#15803d}
.light .source-pill.cloud{background:rgba(37,99,235,.14);color:#1d4ed8}
.light .source-pill.archive{background:rgba(234,88,12,.14);color:#c2410c}
.source-dot{width:5px;height:5px;border-radius:50%;flex-shrink:0}
.primary .source-dot{background:#22c55e;box-shadow:0 0 4px #22c55e}
.cloud .source-dot{background:#60a5fa;box-shadow:0 0 4px #60a5fa}
.archive .source-dot{background:#fb923c;box-shadow:0 0 4px #fb923c}

.fc-body{padding:11px 13px 13px;flex:1;display:flex;flex-direction:column;justify-content:center}
.fc-name{color:var(--text);font-family:inherit;font-size:13px;font-weight:700;line-height:1.45;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;cursor:pointer;transition:color .18s;text-decoration:none;text-align:left;border:0;padding:0;background:none;width:fit-content;max-width:100%}
.fc-name:hover{color:var(--accent-cyan);text-decoration:underline;text-decoration-color:var(--accent-cyan);text-underline-offset:2px}

.fc-text-info{display:flex;align-items:center;gap:6px;padding:11px 13px 0;flex-wrap:wrap;margin-bottom:2px}
.tc-type{background:rgba(236,72,153,.15);color:#f472b6;border:1px solid rgba(236,72,153,.38);border-radius:6px;padding:2px 8px;font-size:10px;font-weight:800;letter-spacing:.7px}
.light .tc-type{color:#be185d;background:rgba(236,72,153,.10)}
.tc-size{background:rgba(99,102,241,.15);color:#a5b4fc;border:1px solid rgba(99,102,241,.38);border-radius:6px;padding:2px 8px;font-size:11px;font-weight:800;line-height:1.5}
.light .tc-size{color:#4338ca;background:rgba(79,70,229,.10)}

.spin-wrap{display:flex;flex-direction:column;align-items:center;gap:16px;padding:60px 20px;color:var(--muted);grid-column:1/-1}
.spinner{width:36px;height:36px;border:3px solid var(--border);border-top-color:var(--accent-cyan);border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

.pagination{display:none;align-items:center;justify-content:center;gap:12px;margin-top:10px;padding-bottom:22px}
.pg-btn{background:var(--bg4);color:var(--text);border:1px solid var(--border);border-radius:10px;padding:8px 18px;font-size:12px;font-weight:700;cursor:pointer;transition:background .18s,transform .15s,box-shadow .18s}
.pg-btn:disabled{background:var(--bg3);color:var(--muted);cursor:not-allowed;opacity:.45}
.pg-btn:not(:disabled):hover{background:var(--accent-grad);color:#fff;border-color:transparent;box-shadow:0 6px 18px var(--accent-glow)}
.pg-btn:not(:disabled):active{transform:scale(.95);box-shadow:none}
.pg-info{color:var(--muted);font-size:12px;font-weight:700}

/* ── DIRECTORY CATALOG CARD ── */
.act-card{background:var(--card);border:1px solid var(--border);border-radius:16px;overflow:hidden;transition:transform .25s cubic-bezier(.22,1,.36,1),border-color .22s,box-shadow .25s;cursor:pointer;box-shadow:0 6px 20px rgba(2,6,23,.22)}
.light .act-card{box-shadow:0 4px 16px rgba(15,23,42,.06)}
.act-card:hover{transform:translateY(-6px);border-color:var(--accent-cyan);box-shadow:0 16px 34px rgba(2,6,23,.48),0 0 18px var(--accent-glow)}
.act-card:active{transform:scale(0.96);transition:transform .1s}
.act-poster{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .45s cubic-bezier(.22,1,.36,1)}
.act-card:hover .act-poster{transform:scale(1.08)}
.act-text-card:active{transform:scale(0.97);transition:transform .1s}
"""

JS = """
(function(){if(localStorage.getItem('theme')==='light')document.documentElement.classList.add('light')})();
function toggleThemeFixed(){var l=document.documentElement.classList.toggle('light');localStorage.setItem('theme',l?'light':'dark');}
function openSidebar(){document.getElementById('sidebar').classList.add('open');document.getElementById('sbOverlay').classList.add('open');document.getElementById('hamBtn').classList.add('open');}
function closeSidebar(){document.getElementById('sidebar').classList.remove('open');document.getElementById('sbOverlay').classList.remove('open');document.getElementById('hamBtn').classList.remove('open');}
// One validated lookup and one compact preview for every group move surface.
async function fetchGroupPreview(id,signal){
    var r=await fetch('/api/group/preview?id='+encodeURIComponent(id),{cache:'no-store',signal:signal});
    var d={};try{d=await r.json();}catch(e){}
    if(!r.ok||d.error){var err=new Error(d.error||('HTTP '+r.status));err.status=r.status;throw err;}
    var g=d.group;
    if(!g||String(g.id)!==id||!(/^[0-9a-f]{64}$/).test(g.signature||''))throw new Error('Could not verify this group. Please try again.');
    return g;
}
function targetEscape(value){
    return String(value == null ? '' : value).replace(/[&<>"']/g,function(c){return '&#'+c.charCodeAt(0)+';';});
}
function targetPreviewHtml(g){
    var url=String(g.cover||''),safe=url.indexOf('/api/thumb?')===0||url.indexOf('/api/group/thumb?')===0;
    var image=safe?'<img src="'+targetEscape(url)+'" alt="Group thumbnail" onerror="this.hidden=true;this.parentElement.nextElementSibling.textContent=&quot;No image&quot;">':'';
    var kind=g.group_type==='series'?'Series / episodes':'Quality versions';
    return '<div class="target-preview"><div class="target-head"><div class="target-image-wrap">'+
        '<div class="target-image"><span aria-hidden="true">&#127916;</span>'+image+'</div><small>'+targetEscape(safe?(g.cover_label||'Preview'):'No image')+'</small></div>'+
        '<div class="target-meta"><span class="target-overline">Destination group</span><div class="target-name">'+targetEscape(g.name||'Untitled group')+'</div>'+
        '<div class="target-badges"><span class="target-badge id">GROUP #'+targetEscape(g.id)+'</span><span class="target-badge kind">'+targetEscape(kind)+'</span>'+
        '<span class="target-badge">'+targetEscape(g.count)+' files</span></div></div></div></div>';
}
var activeFid = '', activeCol = '', cropperInstance = null, fileSaveInProgress = false, fileImageReading = false;
var fileEditorSeq=0,fileEditorLoaded=false,fileGroupReady=false,fileEditorGroup='',fileEditorTarget=null,fileGroupSeq=0,fileGroupAbort=null;

var _thumbRetries = {};
function handleThumbError(fileId) {
    var img = document.getElementById('img-poster-' + fileId);
    var tries = _thumbRetries[fileId] || 0;
    if (img && tries < 8) {
        _thumbRetries[fileId] = tries + 1;
        var oldErr = document.getElementById('thumb-err-' + fileId);
        if (oldErr) oldErr.remove();
        img.style.opacity = '0';
        var col = 'primary';
        try { col = new URL(img.src, window.location.origin).searchParams.get('col') || 'primary'; } catch (e) {}
        setTimeout(function () {
            var current = document.getElementById('img-poster-' + fileId);
            if (current) current.src = freshThumbUrl(fileId, col);
        }, Math.min(15000, 2000 + tries * 2000));
        return;
    }
    if (img) { img.style.opacity = '0'; }
    var errBox = document.getElementById('thumb-err-' + fileId);
    if (!errBox) {
        var box = document.getElementById('poster-box-' + fileId);
        if (box) {
            var div = document.createElement('div');
            div.id = 'thumb-err-' + fileId;
            div.className = 'thumb-error';
            div.innerHTML = '<div style="position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; background:var(--bg3); padding:10px;"><span style="font-size:11px; color:var(--muted); text-align:center;">Poster unavailable</span></div>';
            box.appendChild(div);
        }
    }
}

function freshThumbUrl(fileId, col) {
    return '/api/thumb?file_id='+encodeURIComponent(fileId)+'&col='+encodeURIComponent(col||'primary')+'&v='+Date.now()+'-'+Math.random().toString(36).slice(2);
}
var _tt;
function showToast(m,t){
    t=t||'success';
    var x=document.getElementById('toast');
    if(!x){x=document.createElement('div');x.id='toast';x.className='toast';document.body.appendChild(x);}
    x.textContent=m;x.className='toast '+t+' show';
    clearTimeout(_tt);
    _tt=setTimeout(function(){x.classList.remove('show');},3000);
}

function setFileMenu(card,open){
    card.classList.toggle('admin-active',open);
    var trigger=card.querySelector('.file-poster-trigger')||card.querySelector('.text-file-trigger')||(card.matches('.text-file-trigger')?card:null);
    if(trigger)trigger.setAttribute('aria-expanded',open?'true':'false');
}
function setGroupMenu(card,open){
    card.classList.toggle('grp-active',open);
    card.querySelectorAll('.group-poster-trigger,.grp-textinfo[role=button],.grp-openhead[data-text-trigger]').forEach(function(b){b.setAttribute('aria-expanded',open?'true':'false');});
}
function toggleAdminBtns(card,e){
    if(e)e.stopPropagation();if(!card)return;
    var isActive=card.classList.contains('admin-active');
    document.querySelectorAll('.grp-card.grp-active').forEach(function(c){setGroupMenu(c,false);});
    document.querySelectorAll('.file-card.admin-active').forEach(function(c){setFileMenu(c,false);});
    if(!isActive)setFileMenu(card,true);
}
function textFileClick(card,e){
    if(e.target.closest('.fc-name,.text-admin-row'))return;
    toggleAdminBtns(card,e);
}
function textFileKey(card,e){
    if(e.target!==card||!(e.key==='Enter'||e.key===' '))return;
    e.preventDefault();e.stopPropagation();
    if(typeof selMode!=='undefined'&&selMode&&typeof toggleSel==='function')toggleSel(card);
    else toggleAdminBtns(card,e);
}

document.addEventListener('click',function(){
    document.querySelectorAll('.file-card.admin-active').forEach(function(c){setFileMenu(c,false);});
});

async function deleteFile(fid,col){
    if(!confirm('Move this file to the Recycle Bin? Admin can restore it later.'))return;
    try{
        var r=await fetch('/api/delete',{method:'POST',body:JSON.stringify({file_id:fid,collection:col}),headers:{'Content-Type':'application/json'}});
        var res=await r.json();
        if(res.success){ showToast('♻️ File moved to Recycle Bin'); refreshGridAfterEdit(); }
        else{ showToast(res.error||'Delete failed!','error'); }
    }catch(e){showToast('Delete failed','error');}
}

function setFileEditPreview(fid,col){
    var box=document.getElementById('emPreviewBox');box.style.display='flex';box.textContent='';
    var img=document.createElement('img');img.className='t-prev-img';img.alt='Current thumbnail';
    img.onerror=function(){box.textContent='No thumbnail available';};img.src=freshThumbUrl(fid,col);box.appendChild(img);
}
function editFile(fid, col, encName, encCaption){
    if(fileSaveInProgress)return;
    var currentName=decodeURIComponent(encName);
    var currentCaption=(encCaption&&encCaption!=='undefined')?decodeURIComponent(encCaption):'';
    activeFid=fid;activeCol=col;
    if(cropperInstance){cropperInstance.destroy();cropperInstance=null;}
    document.getElementById('emName').value=currentName;
    document.getElementById('emFile').value='';fileImageReading=false;
    document.getElementById('emImageHelp').textContent='Optional · Choose a new image and adjust its crop.';
    document.getElementById('cropContainer').style.display='none';
    if(document.getElementById('emMoveCol'))document.getElementById('emMoveCol').value=col;
    if(document.getElementById('emAddCaption'))document.getElementById('emAddCaption').value=currentCaption;
    setFileEditPreview(fid,col);
    document.getElementById('editCombinedModal').classList.add('open');
    document.getElementById('emQuality').value='';
    document.getElementById('emGroupId').value='';
    fileEditorGroup='';fileGroupChanged();loadFileEditorDetails();
}

function closeCombinedModal(){
    if(fileSaveInProgress){showToast('Please wait for the save to finish.');return;}
    document.getElementById('editCombinedModal').classList.remove('open');
    ++fileEditorSeq;++fileGroupSeq;if(fileGroupAbort){fileGroupAbort.abort();fileGroupAbort=null;}
    if(cropperInstance){cropperInstance.destroy();cropperInstance=null;}
}

function fileEditorStatus(message,error){var el=document.getElementById('emEditorStatus');el.textContent=message;el.classList.toggle('error',!!error);}
async function loadFileEditorDetails(){
    var seq=++fileEditorSeq,fid=activeFid,col=activeCol;
    fileEditorLoaded=false;fileGroupReady=false;document.getElementById('emSaveBtn').disabled=true;
    document.getElementById('emGroupCheck').disabled=true;document.getElementById('emEditorRetry').hidden=true;
    fileEditorStatus('Loading current quality and group…',false);
    try{
        var r=await fetch('/api/file/editor?file_id='+encodeURIComponent(fid)+'&collection='+encodeURIComponent(col),{cache:'no-store'});
        var d=await r.json().catch(function(){return {};});if(!r.ok)throw new Error(d.error||'Could not load file details.');
        if(seq!==fileEditorSeq)return;
        fileEditorGroup=String(d.group_id||'');document.getElementById('emCurrentGroup').textContent=fileEditorGroup?'Current group: #'+fileEditorGroup:'Current group: None';
        document.getElementById('emQuality').value=d.quality_override||'';
        document.getElementById('emQualityHelp').textContent='Leave blank to use detected quality'+(d.detected_quality?' ('+d.detected_quality+')':'')+'.';
        fileEditorLoaded=true;fileGroupReady=true;document.getElementById('emSaveBtn').disabled=false;document.getElementById('emGroupCheck').disabled=false;
        fileEditorStatus('',false);
    }catch(e){if(seq!==fileEditorSeq)return;fileEditorStatus(e.message||'Could not load file details.',true);document.getElementById('emEditorRetry').hidden=false;}
}
function fileGroupStatus(message,error){var el=document.getElementById('emGroupStatus');el.textContent=message;el.classList.toggle('error',!!error);}
function fileGroupId(){return document.getElementById('emGroupId').value.trim().replace(/^#/,'').trim();}
function fileGroupChanged(){
    ++fileGroupSeq;if(fileGroupAbort){fileGroupAbort.abort();fileGroupAbort=null;}fileEditorTarget=null;
    document.getElementById('emGroupPreview').hidden=true;document.getElementById('emGroupConfirmWrap').hidden=true;
    document.getElementById('emGroupConfirm').checked=false;document.getElementById('emGroupMove').disabled=true;
    fileGroupStatus('Enter a destination ID and check the group before moving.',false);
}
async function checkFileGroup(){
    if(!fileEditorLoaded||!fileGroupReady||fileSaveInProgress)return;
    fileGroupChanged();var id=fileGroupId(),seq=fileGroupSeq;
    if(!/^[0-9]{1,64}$/.test(id)){fileGroupStatus('Enter a valid numeric group ID.',true);return;}
    if(id===fileEditorGroup){fileGroupStatus('This file is already in group #'+id+'.',true);return;}
    fileGroupStatus('Looking up group #'+id+'…',false);
    var controller=new AbortController();fileGroupAbort=controller;
    try{
        var d=await fetchGroupPreview(id,controller.signal);
        if(seq!==fileGroupSeq||fileGroupId()!==id)return;
        fileEditorTarget=d;
        var preview=document.getElementById('emGroupPreview');preview.innerHTML=targetPreviewHtml(d);
        preview.hidden=false;document.getElementById('emGroupConfirmWrap').hidden=false;
        fileGroupStatus('Review the destination before moving. If the old group has fewer than two files left, it will be dissolved.',false);
    }catch(e){if(e.name!=='AbortError'&&seq===fileGroupSeq)fileGroupStatus(e.message||'Could not load group.',true);}
    finally{if(fileGroupAbort===controller)fileGroupAbort=null;}
}
function fileGroupConfirmChanged(){document.getElementById('emGroupMove').disabled=!(fileEditorTarget&&fileGroupId()===fileEditorTarget.id&&document.getElementById('emGroupConfirm').checked&&!fileSaveInProgress);}
async function moveFileFromEditor(){
    var target=fileEditorTarget;if(fileSaveInProgress||!fileEditorLoaded||!target||fileGroupId()!==target.id||!document.getElementById('emGroupConfirm').checked)return;
    fileSaveInProgress=true;document.getElementById('emSaveBtn').disabled=true;document.getElementById('emGroupCheck').disabled=true;document.getElementById('emGroupMove').disabled=true;document.getElementById('emGroupId').disabled=true;document.getElementById('emGroupConfirm').disabled=true;
    try{
        var r=await fetch('/api/group/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({group_id:target.id,items:[{id:activeFid}],expected_target:target.signature})});
        var d=await r.json().catch(function(){return {};});if(!r.ok||!d.success)throw new Error(d.code==='target_changed'?'Destination changed. Check the group again.':(d.error||'Move failed.'));
        fileEditorGroup=String(d.group_id||target.id);document.getElementById('emCurrentGroup').textContent='Current group: #'+fileEditorGroup;
        document.getElementById('emGroupId').value='';fileGroupChanged();fileGroupStatus('Moved to group #'+fileEditorGroup+'. Other edits still need to be saved.',false);refreshGridAfterEdit();
    }catch(e){
        fileGroupChanged();fileGroupReady=false;refreshGridAfterEdit();
        try{
            var state=await fetch('/api/file/editor?file_id='+encodeURIComponent(activeFid)+'&collection='+encodeURIComponent(activeCol),{cache:'no-store'});
            var current=await state.json();if(!state.ok)throw new Error('Lookup failed');
            fileEditorGroup=String(current.group_id||'');document.getElementById('emCurrentGroup').textContent=fileEditorGroup?'Current group: #'+fileEditorGroup:'Current group: None';fileGroupReady=true;
            fileGroupStatus((e.message||'Move failed.')+' Check the latest group before retrying.',true);
        }catch(syncError){fileGroupStatus((e.message||'Move failed.')+' Could not refresh membership; close and reopen this editor before trying another move.',true);}
    }
    finally{fileSaveInProgress=false;document.getElementById('emSaveBtn').disabled=false;document.getElementById('emGroupCheck').disabled=!fileGroupReady;document.getElementById('emGroupId').disabled=false;document.getElementById('emGroupConfirm').disabled=false;}
}

function createThumbCropper(img){
    var lib=window.Cropper;
    if(!lib||typeof lib.Cropper!=='function'||!lib.DEFAULT_TEMPLATE)return null;
    var template=lib.DEFAULT_TEMPLATE.replace('initial-coverage="0.5" movable resizable',
        'aspect-ratio="1.7777777777777777" movable resizable keyboard');
    var cropper=new lib.Cropper(img,{template:template});
    var selection=cropper.getCropperSelection(),image=cropper.getCropperImage(),canvas=cropper.getCropperCanvas();
    if(!selection||!image||!canvas){cropper.destroy();throw new Error('Could not initialize crop tool.');}
    function contains(rect,sel){return sel.x>=rect.x-1&&sel.y>=rect.y-1&&sel.x+sel.width<=rect.x+rect.width+1&&sel.y+sel.height<=rect.y+rect.height+1;}
    cropper.thumbReady=image.$ready().then(function(){return new Promise(function(resolve){requestAnimationFrame(resolve);});}).then(function(){
        if(!canvas.isConnected)return;
        var ir=image.getBoundingClientRect(),cr=canvas.getBoundingClientRect();
        var width=Math.min(ir.width,ir.height*16/9,cr.width,cr.height*16/9)*0.8,height=width*9/16;
        if(width<1||height<1)throw new Error('The image is not ready to crop. Please try again.');
        selection.$change(ir.left-cr.left+(ir.width-width)/2,ir.top-cr.top+(ir.height-height)/2,width,height);
        selection.addEventListener('change',function(e){
            var r=image.getBoundingClientRect(),c=canvas.getBoundingClientRect();
            if(!contains({x:r.left-c.left,y:r.top-c.top,width:r.width,height:r.height},e.detail))e.preventDefault();
        });
        image.addEventListener('change',function(e){
            if(selection.width&&selection.height&&!contains(e.detail,selection))e.preventDefault();
        });
    });
    cropper.thumbReady.catch(function(){});
    return cropper;
}
async function exportThumbCrop(cropper){
    var selection=cropper.getCropperSelection(),image=cropper.getCropperImage();
    if(!selection||!image)throw new Error('The image is not ready to crop. Please try again.');
    await cropper.thumbReady;
    if(!selection.width||!selection.height)throw new Error('The image is not ready to crop. Please try again.');
    var canvas=await selection.$toCanvas({width:1280,height:720});
    if(!canvas)throw new Error('Could not prepare the thumbnail.');
    var output=document.createElement('canvas');output.width=1280;output.height=720;
    output.getContext('2d').drawImage(canvas,0,0,1280,720);
    var blob=await new Promise(function(resolve){output.toBlob(resolve,'image/jpeg',0.9);});
    if(!blob)throw new Error('Could not prepare the thumbnail.');
    return blob;
}
function handleLocalPreview(input){
    if(!input.files||!input.files[0])return;
    var selected=input.files[0],reader=new FileReader();fileImageReading=true;
    document.getElementById('emImageHelp').textContent='Selected: '+selected.name;
    reader.onload=function(e){
        if(!input.files||input.files[0]!==selected||!document.getElementById('editCombinedModal').classList.contains('open'))return;
        fileImageReading=false;
        if(cropperInstance){cropperInstance.destroy();cropperInstance=null;}
        var img=document.createElement('img');img.id='cropImage';img.alt='Selected thumbnail';img.style.maxWidth='100%';img.src=e.target.result;
        if(window.Cropper&&typeof window.Cropper.Cropper==='function'){
            document.getElementById('emPreviewBox').style.display='none';
            var cropWrap=document.getElementById('cropContainer');cropWrap.style.display='block';cropWrap.replaceChildren(img);
            cropperInstance=createThumbCropper(img);
        }else{
            var box=document.getElementById('emPreviewBox');box.style.display='flex';box.replaceChildren(img);
            showToast('Crop tool unavailable; the original image will be uploaded.');
        }
    };
    reader.onerror=function(){if(input.files&&input.files[0]===selected){fileImageReading=false;input.value='';showToast('Could not read the selected image.','error');}};
    reader.readAsDataURL(selected);
}

async function saveAllChanges(){
    if(fileSaveInProgress||!fileEditorLoaded)return;
    if(fileImageReading){showToast('Please wait for the image to load.','error');return;}
    var fid=activeFid,col=activeCol,newName=document.getElementById('emName').value.trim();
    var caption=document.getElementById('emAddCaption').value.trim(),moveCol=document.getElementById('emMoveCol').value;
    if(!newName){showToast('File name cannot be empty!','error');return;}
    var btn=document.getElementById('emSaveBtn'),fileInput=document.getElementById('emFile');
    var thumbUpdated=false,writeAttempted=false,finished=false;
    fileSaveInProgress=true;btn.disabled=true;btn.textContent='Saving…';
    try{
        if(fileInput.files&&fileInput.files[0]){
            var blob=fileInput.files[0];
            if(cropperInstance){
                blob=await exportThumbCrop(cropperInstance);
            }
            var fd=new FormData();fd.append('file_id',fid);fd.append('collection',col);fd.append('image',blob,'poster.jpg');
            writeAttempted=true;
            var upRes=await fetch('/api/upload_thumb',{method:'POST',body:fd});
            var upData=await upRes.json().catch(function(){return {};});
            if(upData.success||upData.partial){
                thumbUpdated=true;
                if(cropperInstance){cropperInstance.destroy();cropperInstance=null;}
                fileInput.value='';document.getElementById('emImageHelp').textContent='Optional · Choose a new image and adjust its crop.';document.getElementById('cropContainer').style.display='none';setFileEditPreview(fid,col);
            }
            if(!upRes.ok||!upData.success)throw new Error(upData.error||'Thumbnail upload failed.');
        }
        var payload={file_id:fid,collection:col,new_name:newName,add_caption:caption,target_collection:moveCol,quality_override:document.getElementById('emQuality').value.trim()};
        writeAttempted=true;
        var r=await fetch('/api/edit_name',{method:'POST',body:JSON.stringify(payload),headers:{'Content-Type':'application/json'}});
        var res=await r.json().catch(function(){return {};});
        if(!r.ok||!res.success)throw new Error(res.error||'Metadata update failed.');
        finished=true;fileSaveInProgress=false;closeCombinedModal();
        showToast('✨ File updated successfully!');
    }catch(e){
        showToast((thumbUpdated?'Thumbnail saved, but other changes failed: ':'')+(e.message||'Network error. Please retry.'),'error');
    }finally{
        fileSaveInProgress=false;btn.disabled=false;btn.textContent='Save Changes';
        if(writeAttempted||finished)refreshGridAfterEdit();
    }
}

function refreshGridAfterEdit() {
    if(typeof doSearch==='function')return doSearch(curOff,true,true);
    if(typeof triggerActorSearchAjax==='function')return triggerActorSearchAjax();
    window.location.reload();
}
function staggerCards(container){
    var cards=container.querySelectorAll('.card-enter');
    if(!cards.length) return;
    var seen=0;
    var obs=new IntersectionObserver(function(entries){
        entries.forEach(function(entry){
            if(!entry.isIntersecting) return;
            var c=entry.target;
            var delay=Math.min(seen,10)*0.08; seen++;
            c.style.animationDelay=delay+'s';
            c.classList.add('card-visible');
            var totalDur=(0.6+delay)*1000;
            setTimeout(function(){ c.classList.remove('card-enter','card-visible'); c.style.animationDelay=''; },totalDur);
            obs.unobserve(c);
        });
    },{threshold:0.08});
    cards.forEach(function(c){ obs.observe(c); });
}
"""

def _h(html): return web.Response(text=html.encode('utf-8','replace').decode('utf-8'), content_type='text/html', charset='utf-8')

async def get_auth(req):
    s_user = req.cookies.get('user_session')
    session = temp.USER_SESSIONS.get(s_user) if s_user else None
    if s_user and not session:
        try:
            session = await web_db.get_session(s_user)
            if session:
                temp.USER_SESSIONS[s_user] = session
        except Exception:
            session = None
    if session and session['expiry'] > time.time():
        tg_id = session['tg_id']
        if tg_id in ADMINS: return 'admin', tg_id
        return 'user', tg_id
    return None, None

async def require_active_plan(role, tg_id):
    if role != 'user':
        return True
    mp = await user_db.get_plan(tg_id)
    return bool(mp.get("premium"))

NAV_MENU = (
    ("dash", "/dashboard", "🏠", "Home"),
    ("posts", "/posts", "🎬", "Posts"),
    ("actors", "/actors", "🎭", "Actors"),
    ("stats", "/stats", "🛰️", "Database Stats"),
    ("recycle", "/admin/recycle", "♻️", "Recycle Bin"),
    ("profile", "/profile", "⚙️", "Profile Settings"),
)

_HEAD_PRE = '<!DOCTYPE html><html><head>'
_HEAD_POST = (
    '</title><meta name="viewport" content="width=device-width,initial-scale=1">'
    '<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@600;700&family=Outfit:wght@600;700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
    f'<style>{CSS}{BRAND_CSS}</style>'
    '<script src="https://cdn.jsdelivr.net/npm/cropperjs@2.3.1/dist/cropper.min.js"></script>'
    f'<script>{MEDIA_CARD_JS}{JS}</script></head>'
)

_ADMIN_MODALS = """
    <div class="edit-modal" id="editCombinedModal" role="dialog" aria-modal="true" aria-labelledby="fileEditorTitle" onclick="if(event.target===this)closeCombinedModal()">
        <div class="em-card file-editor">
            <button class="em-close" type="button" aria-label="Close file editor" onclick="closeCombinedModal()">&#10005;</button>
            <header class="file-editor-head"><h2 class="em-title" id="fileEditorTitle">Edit file</h2></header>
            <div class="file-editor-content">
                <section class="file-editor-section" aria-labelledby="fileDetailsTitle">
                    <div class="file-editor-section-head"><span class="file-editor-number">01</span><div><h3 id="fileDetailsTitle">File details</h3></div></div>
                    <label class="file-editor-field" for="emName">File name<input type="text" id="emName" class="em-input" autocomplete="off"></label>
                    <label class="file-editor-field" for="emAddCaption">Search tags <span style="color:var(--muted);font-weight:400">(optional)</span><input type="text" id="emAddCaption" class="em-input" placeholder="e.g. actor, 1080p, comedy"><small>Saved as the file caption and used for search.</small></label>
                    <label class="file-editor-field" for="emQuality">Quality <span style="color:var(--muted);font-weight:400">(optional override)</span><input type="text" id="emQuality" class="em-input" maxlength="40" placeholder="e.g. 720p, 1080p, 4K"><small id="emQualityHelp">Leave blank to use detected quality.</small></label>
                    <label class="file-editor-field" for="emMoveCol">Collection<select id="emMoveCol" class="em-input"><option value="primary">🟢 Primary</option><option value="cloud">🔵 Cloud</option><option value="archive">🟠 Archive</option></select><small>Choose where this file belongs.</small></label>
                </section>
                <section class="file-editor-section" aria-labelledby="fileArtworkTitle">
                    <div class="file-editor-section-head"><span class="file-editor-number">02</span><div><h3 id="fileArtworkTitle">Thumbnail</h3></div></div>
                    <div class="file-editor-art"><div class="thumb-preview-box" id="emPreviewBox"></div><div class="cropper-container-box" id="cropContainer"></div>
                    <label class="em-upload-btn">Choose image<input type="file" id="emFile" accept="image/*" onchange="handleLocalPreview(this)"></label><p class="file-editor-help" id="emImageHelp">Optional · Choose a new image and adjust its crop.</p></div>
                </section>
            </div>
            <section class="file-editor-group" aria-labelledby="fileGroupTitle">
                <div class="file-editor-section-head"><span class="file-editor-number">03</span><div><h3 id="fileGroupTitle">Group</h3><p id="emCurrentGroup">Current group: Loading…</p></div></div>
                <div class="file-editor-group-row"><label class="file-editor-field" for="emGroupId">Destination group ID<input class="em-input" id="emGroupId" type="text" inputmode="numeric" maxlength="65" placeholder="e.g. 17" oninput="fileGroupChanged()"></label><button type="button" id="emGroupCheck" onclick="checkFileGroup()" disabled>Check</button></div>
                <p class="file-editor-group-status" id="emGroupStatus" role="status" aria-live="polite"></p>
                <div class="file-editor-group-preview" id="emGroupPreview" aria-label="Destination group details" hidden></div>
                <label class="file-editor-group-confirm" id="emGroupConfirmWrap" hidden><input type="checkbox" id="emGroupConfirm" onchange="fileGroupConfirmChanged()"><span>I checked this destination and want to move the file.</span></label>
                <button type="button" id="emGroupMove" onclick="moveFileFromEditor()" disabled>Move to this group</button>
                <p class="file-editor-help">The move is saved separately. Save other file edits using Save Changes.</p>
                <p class="file-editor-load" id="emEditorStatus" role="status" aria-live="polite"></p><button class="file-editor-retry" id="emEditorRetry" type="button" onclick="loadFileEditorDetails()" hidden>Retry loading file details</button>
            </section>
            <footer class="file-editor-footer"><button class="file-editor-cancel" type="button" onclick="closeCombinedModal()">Cancel</button><button class="em-save-btn" id="emSaveBtn" type="button" onclick="saveAllChanges()" disabled>Save Changes</button></footer>
        </div>
    </div>
    """

_NAV_SHELL = ('<div class="sidebar-overlay" id="sbOverlay" onclick="closeSidebar()"></div>'
    '<div class="sidebar" id="sidebar"><div class="sb-header"><div class="sb-logo">'
    + BRAND_MARKUP + '</div>'
    '<button class="sb-close" onclick="closeSidebar()">&#10005;</button></div>'
    '<nav class="sb-nav">{links}</nav>'
    '<div class="sb-footer"><a href="/logout" class="sb-logout"><span aria-hidden="true">🚪</span> Sign Out</a></div></div>'
    '<div class="topbar"><button class="ham-btn" id="hamBtn" onclick="openSidebar()">'
    '<span class="ham-line"></span><span class="ham-line"></span><span class="ham-line"></span></button>'
    '<a class="logo" href="/dashboard" aria-label="RdxTv home">' + BRAND_MARKUP + '</a>'
    '<nav class="tb-nav" aria-label="Primary navigation">{tb_links}</nav>'
    '<div class="topbar-right"><button class="theme-btn" onclick="toggleThemeFixed()"><span aria-hidden="true">🌗</span> Theme</button></div></div>')

_NAV_GUEST = ('<div class="topbar" style="position:absolute; width:100%; box-shadow:none; background:transparent; border-bottom-color:transparent; backdrop-filter:none;">'
    '<a class="logo guest-brand" href="/" aria-label="RdxTv home">' + BRAND_MARKUP + '</a>'
    '<div class="topbar-right"><button class="theme-btn" onclick="toggleThemeFixed()"><span aria-hidden="true">🌗</span> Theme</button></div></div>')


def build_page(title, body, cls="", active_tab="", role=None):
    if role:
        visible = [
            (tab, href, icon, label)
            for tab, href, icon, label in NAV_MENU
            if role == "admin" or tab not in ("stats", "recycle")
        ]
        links = "".join(
            f'<a href="{href}" class="sb-link {"active" if active_tab == tab else ""}"><span class="sb-icon" aria-hidden="true">{icon}</span><span>{label}</span></a>'
            for tab, href, icon, label in visible
        )
        short_labels = {"stats": "Stats", "recycle": "Recycle", "profile": "Profile"}
        tb_links = "".join(
            f'<a href="{href}" class="tb-nav-link {"active" if active_tab == tab else ""}"><span aria-hidden="true">{icon}</span><span>{short_labels.get(tab, label)}</span></a>'
            for tab, href, icon, label in visible
        )
        nav = _NAV_SHELL.format(links=links, tb_links=tb_links)
    else:
        nav = _NAV_GUEST

    modals = _ADMIN_MODALS if role == 'admin' else ""

    player = PLAYER_UI if role else ""
    return _h(_HEAD_PRE + '<title>' + html.escape(str(title)) + _HEAD_POST
              + f'<body class="{cls}">' + nav + body + modals + player + '</body></html>')


def form_wrapper(title, content, err="", msg=""):
    e = f'<div class="err-box">{html.escape(str(err))}</div>' if err else ""
    m = f'<div class="success-box">{html.escape(str(msg))}</div>' if msg else ""
    return f'<div class="login-wrap"><div class="login-card"><h2>{html.escape(str(title))}</h2>{e}{m}{content}</div></div>'
