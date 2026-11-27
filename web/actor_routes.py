import io, time, html, re, uuid
from urllib.parse import urlencode, urlsplit
from aiohttp import web
from bson.objectid import ObjectId
from utils import temp
from info import MAX_WEB_RESULTS, ACTOR_STORAGE_CHANNEL
from database.ia_filterdb import actors, get_actor_search_results, delete_actor_profile, delete_gallery_image_by_index
# ✅ DRY: fast_json + DIRECTORY_CSS अब web_assets से आते हैं (पहले दोनों यहाँ copy थे)
from web.web_assets import build_page, get_auth, require_active_plan, fast_json, DIRECTORY_CSS, DEFAULT_CATALOG_MODE, DEFAULT_MEDIA_MODE
from web.search_api import _build_results_list, _annotate_raw_groups, group_results, _manual_map
from web.catalog_cards import render_catalog_card
from web.catalog_search import CATALOG_PAGE_SIZE, catalog_page

actor_routes = web.RouteTableDef()

ACTOR_MEDIA_SCRIPT = r'''<script>
var actorMediaFiles={};
function actorPlayFile(card){var f=actorMediaFiles[card.dataset.fid];if(f)openInlinePlayer(f.file_id,f.name);}
function actorEditFile(card){var f=actorMediaFiles[card.dataset.fid];if(f)editFile(f.file_id,f.raw_collection||'primary',encodeURIComponent(f.name||'').replace(/'/g,'%27'),encodeURIComponent(f.caption||'').replace(/'/g,'%27'));}
function actorDeleteFile(card){var f=actorMediaFiles[card.dataset.fid];if(f)deleteFile(f.file_id,f.raw_collection||'primary');}
function renderActorMediaCard(f,mode,isAdmin){
    actorMediaFiles[f.file_id]=f;
    var actions=isAdmin?`<button class="btn-edit" onclick="event.stopPropagation();actorEditFile(this.closest('.file-card'))">&#9999; Edit</button><button class="btn-del" onclick="event.stopPropagation();actorDeleteFile(this.closest('.file-card'))">&#128465; Delete</button>`:'';
    return renderMediaFile(f,mode,{admin:isAdmin,actions:actions,play:"actorPlayFile(this.closest('.file-card'))"});
}
function actorEsc(x){return String(x==null?'':x).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}
function actorGroupIdChip(id){return id?'<span class="group-id-chip" title="Saved group ID">GROUP #'+actorEsc(id)+'</span>':'';}
function actorGroupHtml(g,mode,isAdmin){
    actorMediaFiles[g.key]=g;
    g.variants.forEach(function(v){actorMediaFiles[v.file_id]=v;});
    var series=g.group_type==='series',chips='';
    if(series){
        g.variants.slice(0,3).forEach(function(v,i){
            chips+='<span class="episode-chip">'+actorEsc(v.episode_label||('File '+(v.episode_position||i+1)))+'</span>';
        });
        if(g.count>3)chips+='<span class="episode-chip">+'+(g.count-3)+' more</span>';
    }else{
        (g.chips||[]).forEach(function(c){
            chips+='<span class="grp-chip">'+actorEsc(c.label)+(c.count>1?' <i>×'+c.count+'</i>':'')+'</span>';
        });
    }
    var srcs=(g.sources&&g.sources.length)?g.sources:[(g.source||'primary').toLowerCase()];
    var sc=srcs.length>1?'mixed':srcs[0];
    if(!['primary','cloud','archive','mixed'].includes(sc))sc='primary';
    var pill='<span class="source-pill '+sc+'" title="'+actorEsc(srcs.join(' + ').toUpperCase())+'"><span class="source-dot"></span>'+sc.toUpperCase()+'</span>';
    var dur=!series&&g.duration?'<span class="dur-chip">'+actorEsc(g.duration)+'</span>':'';
    var idChip=actorGroupIdChip(g.num||g.gid);
    var badge='<span class="grp-badge">'+(series?(g.episode_count==null?g.count:g.episode_count):g.count)+(series?' EPISODES':' QUALITY')+'</span>';
    var poster='';
    if(mode!=='none'){
        poster='<div class="poster-box">'+
            (g.tg_thumb?'<img src="'+g.tg_thumb+'" class="fc-poster" onload="this.classList.add(\'loaded\')" onerror="this.style.display=\'none\'" loading="lazy" decoding="async">':'')+
            '<div class="poster-top">'+idChip+badge+dur+pill+'</div>'+
            '<div class="grp-bottom">'+chips+'</div>'+
            '<button type="button" class="group-poster-trigger" aria-label="Open group" onclick="toggleActorGroup(this.closest(\'.grp-card\'))"></button>'+
        '</div>';
    }
    var textInfo='<div class="grp-textinfo">'+idChip+badge+dur+chips+pill+'</div>';
    var inner='';
    g.variants.forEach(function(v){inner+=renderActorMediaCard(v,mode,isAdmin);});
    return '<div class="grp-card card-enter" data-gk="'+g.key+'">'+
        '<div class="grp-master">'+poster+
            '<div class="grp-body"><button type="button" class="grp-title grp-title-button" onclick="event.stopPropagation();toggleActorGroup(this.closest(\'.grp-card\'))">'+g.title+'</button>'+textInfo+'</div>'+
        '</div>'+
        '<div class="grp-openhead" role="button" tabindex="0" onclick="toggleActorGroup(this.parentNode)">'+idChip+badge+dur+'<button type="button" class="grp-title grp-open-title" onclick="event.stopPropagation();toggleActorGroup(this.closest(\'.grp-card\'))">'+g.title+'</button><span class="grp-arrow">&#9662;</span></div>'+
        '<div class="grp-variants">'+inner+'</div>'+
    '</div>';
}
function toggleActorGroup(card){
    if(!card)return;
    card.classList.toggle('open');
}
</script><style>.poster-top{flex-wrap:wrap;align-content:flex-start}
.grp-card{background:var(--card);border:1px solid var(--border);border-radius:15px;overflow:hidden;display:flex;flex-direction:column;position:relative;cursor:pointer;box-shadow:0 6px 20px rgba(2,6,23,.24);transition:all .28s cubic-bezier(.22,1,.36,1)}
.light .grp-card{box-shadow:0 4px 16px rgba(15,23,42,.06)}
.grp-card.open{border-color:var(--accent-cyan);grid-column:1/-1;box-shadow:0 14px 38px rgba(2,6,23,.48);cursor:default}
.grp-card:not(.open):hover{transform:translateY(-5px) scale(1.015);border-color:var(--accent-cyan);box-shadow:0 18px 38px rgba(2,6,23,.52),0 0 20px var(--accent-glow);z-index:2}
.grp-card:not(.open):active{transform:scale(.97);transition:transform .1s}
.grp-card:not(.open) .grp-title{transition:color .18s;text-decoration:none}
.grp-card:not(.open) .grp-title:hover{color:var(--accent-cyan);text-decoration:underline;text-decoration-color:var(--accent-cyan);text-underline-offset:2px}
.grp-card:not(.open):hover .grp-master .fc-poster{transform:scale(1.07)}
.group-id-chip{display:inline-flex;align-items:center;gap:3px;background:rgba(57,35,11,.88);color:#ffd58a;border:1px solid rgba(217,155,59,.55);border-radius:6px;padding:3px 7px;font-size:10px;font-weight:800;letter-spacing:.3px;line-height:1.4;white-space:nowrap}
.episode-chip{background:rgba(49,46,129,.88);color:#e0e7ff;border:1px solid rgba(129,140,248,.55);border-radius:6px;padding:3px 7px;font-size:10px;font-weight:800;line-height:1.4}
.grp-badge{background:var(--accent-grad);color:#fff;border-radius:6px;padding:3px 9px;font-size:10px;font-weight:800;letter-spacing:.4px;border:1px solid rgba(255,255,255,.22);line-height:1.4;white-space:nowrap;box-shadow:0 4px 12px var(--accent-glow)}
.grp-bottom{position:absolute;left:0;right:0;bottom:0;display:flex;flex-wrap:wrap;gap:5px;padding:28px 8px 8px;background:linear-gradient(transparent,rgba(5,9,20,.92));z-index:3}
.grp-chip{background:rgba(8,47,73,.88);color:#7dd3fc;border:1px solid rgba(56,189,248,.5);border-radius:6px;font-size:10px;font-weight:800;padding:2px 8px;line-height:1.5;text-shadow:none;max-width:100%;min-width:0;overflow-wrap:anywhere}
.grp-chip i{font-style:normal;color:#e0f2fe;opacity:1;margin-left:2px}
.grp-body{padding:12px 13px 14px}
.grp-title{color:var(--text);font-size:13px;font-weight:700;line-height:1.45;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.grp-title-button{width:fit-content;max-width:100%;padding:0;border:0;background:none;font-family:inherit;text-align:left;cursor:pointer}
.grp-title-button:focus-visible{outline:2px solid var(--accent-cyan);outline-offset:4px;border-radius:2px}
.grp-card.open .grp-title{-webkit-line-clamp:unset}
.grp-textinfo{display:none;align-items:center;gap:6px;flex-wrap:wrap;margin-top:8px}
.res-grid.mode-none .grp-textinfo{display:flex}
.grp-openhead{display:none;align-items:center;gap:10px;flex-wrap:wrap;padding:13px 16px;cursor:pointer;background:linear-gradient(120deg,rgba(99,102,241,.08),transparent 65%)}
.grp-openhead .grp-title{min-width:0}
.grp-arrow{margin-left:auto;color:var(--muted);font-size:13px;transform:rotate(180deg)}
.grp-card.open .grp-openhead{display:flex}
.grp-card.open .grp-master{display:none}
.grp-open-title{flex:0 1 auto;width:fit-content;max-width:100%;padding:0;border:0;background:none;color:var(--text);font:inherit;text-align:left;cursor:pointer}
.grp-variants{display:none;border-top:1px solid var(--border)}
.grp-card.open .grp-variants{display:grid;grid-template-columns:1fr;gap:10px;padding:12px}
@media(min-width:600px){.grp-card.open .grp-variants{grid-template-columns:repeat(3,1fr)}}
.source-pill.mixed{background:rgba(180,83,9,.85);color:#fef08a;border:1px solid rgba(245,158,11,.55)}
.source-pill.mixed .source-dot{background:#fcd34d}
</style>'''

# ─────────────────────────────────────────────────────────
# 🌐 MAIN HOMEPAGE: UNIVERSAL DIRECTORY WITH SEARCH & FILTERS
# ─────────────────────────────────────────────────────────
@actor_routes.get('/actors')
async def actors_directory_page(req):
    role, tg_id = await get_auth(req)
    if not role: return web.HTTPFound('/login')
    if not await require_active_plan(role, tg_id): return web.HTTPFound('/premium_expired')
    
    all_actors, has_next_init = await catalog_page(actors, {})
    
    admin_btn = '''<button onclick="window.location.href='/admin/create_actor'" style="background:var(--accent-grad); color:#fff; border:none; padding:10px 16px; border-radius:10px; font-weight:800; cursor:pointer; font-size:13px; flex:1; min-width:130px; box-shadow:0 6px 18px var(--accent-glow); transition:0.2s;">➕ Create Profile</button>''' if role == 'admin' else ""
    
    search_ui = f'''
    {DIRECTORY_CSS}
    <div class="search-box">
        <div class="s-row-1" id="dirSearchRow">
            <input type="text" id="dir_q" class="s-input" placeholder="Search actors, creators, apps, networks...">
            <span class="s-spinner" id="dirSpinner"></span>
        </div>
        <div class="s-row-2">
            <div class="cdd-wrap" onclick="toggleDirCDD('cat', event)">
                <span id="dir_cat_lbl">All</span> <span class="cdd-arrow" aria-hidden="true">▼</span>
                <div class="cdd-menu" id="dir_cat_menu">
                    <div class="cdd-item" onclick="pickDirCat('all', 'All', event)">All</div>
                    <div class="cdd-item" onclick="pickDirCat('actor', '🎭 Actor', event)">🎭 Actor</div>
                    <div class="cdd-item" onclick="pickDirCat('app', '📱 App', event)">📱 App</div>
                    <div class="cdd-item" onclick="pickDirCat('website', '🌐 Website', event)">🌐 Website</div>
                </div>
            </div>
            <div class="cdd-wrap" onclick="toggleDirCDD('mode', event)">
                <span id="dir_mode_lbl">{'📄 Text' if DEFAULT_CATALOG_MODE == 'text' else '🖼️ Poster'}</span> <span class="cdd-arrow" aria-hidden="true">▼</span>
                <div class="cdd-menu" id="dir_mode_menu">
                    <div class="cdd-item" onclick="pickDirMode('poster', '🖼️ Poster', event)">🖼️ Poster</div>
                    <div class="cdd-item" onclick="pickDirMode('text', '📄 Text', event)">📄 Text</div>
                </div>
            </div>
            {admin_btn}
        </div>
    </div>
    '''

    act_items = ''.join(render_catalog_card(a, 'actor', DEFAULT_CATALOG_MODE) for a in all_actors)

    dir_grid_style = ' style="display:flex; flex-direction:column; gap:10px;"' if DEFAULT_CATALOG_MODE == "text" else ""
    initial_grid = f'<div id="dir_grid_container" class="dir-grid"{dir_grid_style}>{act_items}</div>' if all_actors else '<div id="dir_grid_container" style="color:var(--muted); text-align:center; padding:60px 20px;">📇 No profiles found.</div>'
    
    has_nxt_str = "true" if has_next_init else "false"

    js_logic = f'''
    <div class="pg-bar" id="dir_pg_box" style="display:none;">
        <button class="pg-btn" id="dir_pBtn" onclick="prevDir()" disabled>Previous</button>
        <span class="pg-info" id="dir_pgInfo">Page 1</span>
        <button class="pg-btn" id="dir_nBtn" onclick="nextDir()">Next</button>
    </div>

    <script>
    var dirOffset = 0; var dirLimit = {CATALOG_PAGE_SIZE}; var dirPage = 1;
    var hasNext = {has_nxt_str};
    var currentCat = 'all'; var currentMode = MediaView.get('{DEFAULT_CATALOG_MODE}');
    var lastQ = "", lastCat = "all", lastMode = "{DEFAULT_CATALOG_MODE}", lastOffset = 0;
    var dirReqId = 0;
    
    document.addEventListener("DOMContentLoaded", () => {{ 
        if(sessionStorage.getItem('ff_dir_state')) {{
            document.getElementById('dir_q').value = sessionStorage.getItem('ff_dir_q') || "";
            currentCat = sessionStorage.getItem('ff_dir_cat') || "all";
            currentMode = MediaView.get('{DEFAULT_CATALOG_MODE}');
            dirOffset = parseInt(sessionStorage.getItem('ff_dir_off') || "0");
            dirPage = parseInt(sessionStorage.getItem('ff_dir_page') || "1");
            
            const catMap = {{'all':'All', 'actor':'🎭 Actor', 'app':'📱 App', 'website':'🌐 Website'}};
            const modeMap = {{'poster':'🖼️ Poster', 'text':'📄 Text'}};
            document.getElementById('dir_cat_lbl').innerText = catMap[currentCat] || 'All';
            document.getElementById('dir_mode_lbl').innerText = modeMap[currentMode] || modeMap['{DEFAULT_CATALOG_MODE}'];
            
            searchDirectory(true);
        }} else {{
            document.getElementById('dir_mode_lbl').innerText = currentMode === 'text' ? '📄 Text' : '🖼️ Poster';
            if(currentMode !== '{DEFAULT_CATALOG_MODE}') {{ searchDirectory(true); return; }}
            updatePgUI();
            staggerCards(document.getElementById('dir_grid_container'));
        }}
    }});

    MediaView.subscribe(function(value) {{
        if(value===currentMode)return;
        currentMode=value;document.getElementById('dir_mode_lbl').innerText=value==='text'?'📄 Text':'🖼️ Poster';
        resetDir();searchDirectory(true);
    }});

    function closeAllDirCDD() {{ document.getElementById('dir_cat_menu').style.display='none'; document.getElementById('dir_mode_menu').style.display='none'; }}
    document.addEventListener('click', closeAllDirCDD);

    function toggleDirCDD(type, e) {{
        e.stopPropagation();
        var menu = document.getElementById('dir_' + type + '_menu');
        var isVis = menu.style.display === 'block';
        closeAllDirCDD();
        if (!isVis) menu.style.display = 'block';
    }}

    function pickDirCat(val, lbl, e) {{ e.stopPropagation(); currentCat = val; document.getElementById('dir_cat_lbl').innerText = lbl; closeAllDirCDD(); resetDir(); searchDirectory(); }}
    function pickDirMode(val, lbl, e) {{ e.stopPropagation(); currentMode = MediaView.set(val); document.getElementById('dir_mode_lbl').innerText = lbl; closeAllDirCDD(); resetDir(); searchDirectory(); }}

    async function searchDirectory(forceRestore = false) {{
        var q = document.getElementById('dir_q').value.trim();
        
        if (!forceRestore && q === lastQ && currentCat === lastCat && currentMode === lastMode && dirOffset === lastOffset) {{ return; }}
        
        lastQ = q; lastCat = currentCat; lastMode = currentMode; lastOffset = dirOffset;
        
        sessionStorage.setItem('ff_dir_state', '1');
        sessionStorage.setItem('ff_dir_q', q);
        sessionStorage.setItem('ff_dir_cat', currentCat);
        sessionStorage.setItem('ff_dir_mode', currentMode);
        sessionStorage.setItem('ff_dir_off', dirOffset);
        sessionStorage.setItem('ff_dir_page', dirPage);

        var myReq = ++dirReqId;
        var grid = document.getElementById('dir_grid_container');
        var row = document.getElementById('dirSearchRow');
        var loadTimer = setTimeout(function() {{
            if (myReq !== dirReqId) return;
            if (row) row.classList.add('loading');
        }}, 150);
        
        try {{
            var res = await fetch('/api/directory/search?q=' + encodeURIComponent(q) + '&cat=' + currentCat + '&mode=' + currentMode + '&offset=' + dirOffset);
            if (myReq !== dirReqId) {{ clearTimeout(loadTimer); return; }}
            clearTimeout(loadTimer);
            if (row) row.classList.remove('loading');
            if (!res.ok) throw new Error("HTTP " + res.status);
            var data = await res.json();
            if (myReq !== dirReqId) return;
            grid.innerHTML = data.html;
            // Stagger entrance animation
            staggerCards(grid);
            hasNext = data.has_next;
            
            if(currentMode === 'text') {{
                grid.style.display = 'flex'; grid.style.flexDirection = 'column'; grid.style.gap = '10px';
            }} else {{
                grid.style.display = 'grid'; grid.style.gap = '';
            }}
            updatePgUI();
        }} catch(e) {{ clearTimeout(loadTimer); if (myReq !== dirReqId) return; if (row) row.classList.remove('loading'); lastQ = null; grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; color:var(--accent); font-weight:bold;">Search Error! Please retry.</div>'; }}
    }}
    
    function updatePgUI() {{
        var box = document.getElementById('dir_pg_box');
        if (dirOffset === 0 && !hasNext) {{ box.style.display = 'none'; }} else {{ box.style.display = 'flex'; }}
        document.getElementById('dir_pBtn').disabled = (dirOffset === 0);
        document.getElementById('dir_nBtn').disabled = !hasNext;
        document.getElementById('dir_pgInfo').innerText = 'Page ' + dirPage;
    }}
    
    function resetDir() {{ dirOffset = 0; dirPage = 1; }}
    function nextDir() {{ if(hasNext) {{ dirOffset += dirLimit; dirPage++; searchDirectory(); window.scrollTo(0, 50); }} }}
    function prevDir() {{ if(dirOffset > 0) {{ dirOffset = Math.max(0, dirOffset - dirLimit); dirPage--; searchDirectory(); window.scrollTo(0, 50); }} }}
    document.getElementById('dir_q').addEventListener('keydown', function(e) {{ if(e.key === 'Enter') {{ clearTimeout(dirLiveTimer); resetDir(); searchDirectory(); }} }});
    var dirLiveTimer;
    document.getElementById('dir_q').addEventListener('input', function() {{
        clearTimeout(dirLiveTimer);
        dirLiveTimer = setTimeout(function() {{ resetDir(); searchDirectory(); }}, 350);
    }});
    </script>
    '''

    page_body = f'''<div class="main" style="padding-top:20px; max-width:1100px; margin:0 auto; padding-left:20px; padding-right:20px;">{search_ui}{initial_grid}{js_logic}</div>'''
    return build_page("Directory Catalog - RdxTv", page_body, "", "actors", role)

# ─────────────────────────────────────────────────────────
# 🔍 API: DIRECTORY UNIVERSAL SEARCH (WITH PAGINATION)
# ─────────────────────────────────────────────────────────
@actor_routes.get('/api/directory/search')
async def api_directory_search(req):
    role, tg_id = await get_auth(req)
    if not role or not await require_active_plan(role, tg_id):
        return web.json_response({"error": "Access denied."}, status=403, dumps=fast_json)

    q = req.query.get("q", "").strip()
    cat = req.query.get("cat", "all")
    mode = req.query.get("mode", DEFAULT_CATALOG_MODE)
    offset = req.query.get("offset", 0)
    
    query = {}
    if cat != "all": query["category"] = cat
    if q: 
        safe_q = re.escape(q)
        query["name"] = {"$regex": safe_q, "$options": "i"}
        
    try:
        docs, has_next = await catalog_page(actors, query, offset)
    except Exception:
        return web.json_response({"error": "Profile search temporarily unavailable."}, status=503, dumps=fast_json)
    
    if not docs:
        return web.json_response({"html": '<div style="grid-column:1/-1; color:var(--muted); text-align:center; padding:60px 20px;">📇 No profiles matching your filters found.</div>', "has_next": False}, dumps=fast_json)
        
    html_out = ''.join(render_catalog_card(a, 'actor', mode) for a in docs)

    return web.json_response({"html": html_out, "has_next": has_next}, dumps=fast_json)


# ─────────────────────────────────────────────────────────
# 🧩 SHARED PROFILE FORM (Create + Edit दोनों इसी से बनते हैं)
#    नया फ़ील्ड जोड़ना हो तो सिर्फ यहाँ जोड़ें — दोनों फॉर्म में अपने-आप आ जाएगा।
# ─────────────────────────────────────────────────────────
def _clean_link(v):
    """Accept web links only, including scheme-less domains; never truncate URLs."""
    if not isinstance(v, str):
        return ""
    v = v.strip()
    if not v or len(v) > 8192 or "\\" in v or re.search(r"[\s\x00-\x1f\x7f]", v):
        return ""
    if not re.match(r"^https?://", v, re.I):
        # Permit example.com:8080 but reject javascript:, data:, ftp:, etc.
        if re.match(r"^[a-z][a-z0-9+.\-]*:", v, re.I) and not re.match(r"^[^/:]+:\d+(?:[/?#]|$)", v):
            return ""
        v = "https://" + v
    try:
        parsed = urlsplit(v)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
            return ""
        _ = parsed.port  # Reject malformed ports.
    except ValueError:
        return ""
    return v


_LEGACY_LINK_LABELS = {"instagram": "Instagram", "youtube": "YouTube", "twitter": "Twitter / X"}


def _profile_links(actor):
    """Read the new ordered links, or legacy social links without discarding them."""
    saved = actor.get("profile_links")
    if isinstance(saved, list):
        candidates = saved
    else:
        legacy = actor.get("social_links") or {}
        candidates = [{"label": _LEGACY_LINK_LABELS.get(str(k).lower(), str(k)), "url": v}
                      for k, v in legacy.items()] if isinstance(legacy, dict) else []
    result = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        url = _clean_link(item.get("url"))
        if url:
            label = str(item.get("label") or "").strip() or urlsplit(url).hostname
            result.append({"label": label, "url": url})
    return result


def _parse_profile_links(labels, urls):
    """Validate all rows before writing; preserve ordering and duplicate URLs."""
    if len(labels) != len(urls):
        raise ValueError("Each link must have a matching name and URL.")
    links = []
    for label, raw in zip(labels, urls):
        if not isinstance(label, str) or not isinstance(raw, str):
            raise ValueError("Invalid link fields.")
        label, raw = label.strip(), raw.strip()
        if not label and not raw:
            continue
        if len(label) > 200:
            raise ValueError("Link names must be at most 200 characters.")
        url = _clean_link(raw)
        if not url:
            raise ValueError("Enter a valid http or https URL for each link.")
        links.append({"label": label or urlsplit(url).hostname, "url": url})
    return links


ACTOR_FORM_CSS = '''<style>
.profile-studio{max-width:880px;margin:0 auto;padding:22px 20px 60px}
.profile-studio-head{display:flex;align-items:center;gap:14px;margin-bottom:18px}
.profile-back,.profile-cancel{color:var(--text);text-decoration:none;border:1px solid var(--border);background:var(--bg3);border-radius:10px;padding:9px 14px;font-size:13px;font-weight:700;white-space:nowrap;cursor:pointer;transition:.18s}
.profile-back:hover,.profile-cancel:hover{border-color:var(--accent-cyan);color:var(--accent-cyan)}
.profile-studio-head h1{font-size:24px;line-height:1.2;margin:0}
.profile-help{font-size:12px;line-height:1.5;color:var(--muted)}
.profile-section{background:var(--bg2);border:1px solid var(--border);border-radius:16px;padding:18px;margin-bottom:14px}
.profile-section-head{margin-bottom:14px}.profile-section-head h2{font-size:15.5px;margin:0}
.profile-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.profile-field{display:flex;flex-direction:column;gap:7px;min-width:0;color:var(--text);font-size:12px;font-weight:800}
.profile-field.full{grid-column:1/-1}.profile-field .em-input{margin:0;padding:12px;background:var(--bg);font-family:inherit;font-weight:500;line-height:1.4;border-radius:10px}
.profile-field textarea{min-height:104px;resize:vertical}.profile-field small{font-weight:500;color:var(--muted);line-height:1.4}
.profile-links{display:flex;flex-direction:column;gap:10px}.profile-link-row{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,2fr) auto;gap:10px;align-items:end;padding:12px;background:var(--bg);border:1px solid var(--border);border-radius:12px}
.profile-link-row .em-input{background:var(--bg2)}.profile-link-remove,.profile-link-add{border:1px solid var(--border);border-radius:10px;background:var(--bg3);color:var(--text);padding:10px 14px;font-family:inherit;font-size:12px;font-weight:700;cursor:pointer;transition:.18s}.profile-link-add{margin-top:12px}.profile-link-remove:hover{border-color:#f43f5e;color:#fb7185}.profile-link-add:hover{border-color:var(--accent-cyan);color:var(--accent-cyan)}
.profile-media{display:flex;gap:16px;align-items:center}.profile-photo{width:92px;aspect-ratio:3/4;flex:none;border:1px solid var(--border);border-radius:12px;background:var(--bg3);display:grid;place-items:center;overflow:hidden;color:var(--muted);font-size:26px}
.profile-photo img{width:100%;height:100%;object-fit:cover}.profile-photo img[hidden]{display:none}.profile-photo img:not([hidden])+span{display:none}
.profile-media-copy{flex:1;min-width:0}.profile-file{display:block;max-width:100%;margin:8px 0;color:var(--muted);font:inherit;font-size:12px}.profile-file::file-selector-button{border:1px solid var(--border);background:var(--bg3);color:var(--text);padding:8px 12px;border-radius:9px;font:inherit;font-weight:700;cursor:pointer;margin-right:10px}
.profile-form-actions{display:flex;gap:10px;align-items:center;justify-content:flex-end;margin-top:18px}.profile-form-actions .em-save-btn{width:auto;min-width:160px}
.profile-modal-card{max-width:700px!important;max-height:calc(100dvh - 30px);overflow:auto;padding:22px!important;border-radius:20px!important;box-shadow:0 28px 80px rgba(2,6,23,.68)}.profile-modal-card .profile-section{background:var(--bg3);padding:15px;border-radius:14px}.profile-modal-card .profile-section:last-of-type{margin-bottom:0}
.profile-modal-card .em-title{padding-right:36px;margin-bottom:14px}
@media(max-width:600px){.profile-studio{padding:16px 12px 48px}.profile-studio-head h1{font-size:20px}.profile-section{padding:14px}.profile-fields{grid-template-columns:1fr}.profile-field.full{grid-column:auto}.profile-photo{width:76px}.profile-modal-card{padding:16px!important}.profile-form-actions .em-save-btn{flex:1;min-width:0}.profile-link-row{grid-template-columns:1fr}.profile-link-remove{justify-self:start}}
@media(hover:none){.gallery-del-btn{opacity:1!important}}
</style>'''

PROFILE_FORM_JS = r'''<script>
(function(){
    document.querySelectorAll('form[data-profile-form]').forEach(function(form){
        var button=form.querySelector('button[type=submit]'),notice=form.querySelector('.profile-form-error'),label=button.textContent;
        var modal=form.closest('#actorEditModal'),avatar=modal&&modal.querySelector('.profile-file');
        var list=form.querySelector('[data-profile-links]'),add=form.querySelector('[data-link-add]');
        if(list&&add){
            add.addEventListener('click',function(){
                var row=document.createElement('div');row.className='profile-link-row';
                row.innerHTML='<label class="profile-field">Name <span>(optional)</span><input class="em-input" name="link_label" maxlength="200" placeholder="Website, Instagram, shop…"></label><label class="profile-field">URL<input class="em-input" name="link_url" inputmode="url" placeholder="https://example.com"></label><button class="profile-link-remove" type="button" data-link-remove>Remove</button>';
                list.appendChild(row);row.querySelector('[name=link_url]').focus();
            });
            list.addEventListener('click',function(event){var remove=event.target.closest('[data-link-remove]');if(remove)remove.closest('.profile-link-row').remove();});
        }
        form.addEventListener('submit',async function(event){
            event.preventDefault();if(button.disabled)return;form.dataset.saving='true';button.disabled=true;button.textContent='Saving…';notice.hidden=true;if(avatar)avatar.disabled=true;
            try{
                var response=await fetch(form.action,{method:'POST',body:new FormData(form),headers:{'Accept':'application/json'}});
                var data=await response.json().catch(function(){return {};});
                if(!response.ok||!data.success)throw new Error(data.error||'Could not confirm the save. Please retry.');
                if(typeof data.redirect!=='string'||data.redirect[0]!=='/'||data.redirect[1]==='/')throw new Error('Saved, but could not open the result.');
                window.location.assign(data.redirect);return;
            }catch(error){form.dataset.saving='false';notice.textContent=error.message||'Could not confirm the save. Check your connection before retrying.';notice.hidden=false;notice.scrollIntoView({block:'nearest'});button.disabled=false;button.textContent=label;if(avatar)avatar.disabled=false;}
        });
        window.addEventListener('pageshow',function(){form.dataset.saving='false';button.disabled=false;button.textContent=label;if(avatar)avatar.disabled=false;});
    });
})();
</script>'''


def _actor_result(req, destination, error=None, status=400):
    if 'application/json' in req.headers.get('Accept', ''):
        return web.json_response({'error': error} if error else {'success': True, 'redirect': destination},
                                 status=status if error else 200, dumps=fast_json)
    if error:
        return web.HTTPFound(destination + ('&' if '?' in destination else '?') + urlencode({'err': error}))
    return web.HTTPFound(destination)


def actor_form_fields(name="", category="actor", bio="", tags="", links=None):
    """Shared, escaped fields keep create and edit forms in sync."""
    links = links or []
    esc = lambda value: html.escape(str(value or ""), quote=True)

    def opt(val, label):
        return f'<option value="{val}"{" selected" if category == val else ""}>{label}</option>'

    link_rows = ''.join(
        '<div class="profile-link-row"><label class="profile-field">Name <span>(optional)</span>'
        f'<input class="em-input" name="link_label" maxlength="200" value="{esc(link.get("label"))}" placeholder="Website, Instagram, shop…"></label>'
        '<label class="profile-field">URL'
        f'<input class="em-input" name="link_url" inputmode="url" value="{esc(link.get("url"))}" placeholder="https://example.com"></label>'
        '<button class="profile-link-remove" type="button" data-link-remove>Remove</button></div>'
        for link in links
    )
    legacy_category = f'<option value="{esc(category)}" selected>{esc(category)}</option>' if category and category not in ('actor', 'app', 'website') else ''
    return (
        '<section class="profile-section"><div class="profile-section-head"><h2>Profile details</h2></div>'
        '<div class="profile-fields">'
        f'<label class="profile-field">Display name<input type="text" name="name" value="{esc(name)}" placeholder="Name of actor, app or website" class="em-input" required></label>'
        '<label class="profile-field">Category<select name="category" class="em-input" required>'
        + legacy_category + opt("actor", "🎭 Actor") + opt("app", "📱 App") + opt("website", "🌐 Website") + '</select></label>'
        f'<label class="profile-field full">Biography<textarea name="bio" placeholder="Add a short introduction..." class="em-input" required>{esc(bio)}</textarea></label>'
        f'<label class="profile-field full">Search tags<input type="text" name="tags" value="{esc(tags)}" placeholder="e.g. Actor name, Alias, Genre" class="em-input"><small>Separate tags with commas.</small></label>'
        '</div></section>'
        '<section class="profile-section"><div class="profile-section-head"><h2>Links</h2></div>'
        '<input type="hidden" name="links_present" value="1">'
        f'<div class="profile-links" data-profile-links>{link_rows}</div>'
        '<button class="profile-link-add" type="button" data-link-add>+ Add link</button></section>'
    )


# ─────────────────────────────────────────────────────────
# 🛠️ ADMIN ROUTE: CREATE PROFILE PAGE
# ─────────────────────────────────────────────────────────
@actor_routes.get('/admin/create_actor')
async def create_actor_page(req):
    role, _ = await get_auth(req)
    if role != 'admin': return web.HTTPFound('/dashboard')
    err, msg = html.escape(req.query.get('err', '')), html.escape(req.query.get('msg', ''))
    notices = (f'<div class="err-box">{err}</div>' if err else '') + (f'<div class="success-box">{msg}</div>' if msg else '')
    content = ACTOR_FORM_CSS + f'''
    <main class="profile-studio">
      <header class="profile-studio-head"><a class="profile-back" href="/actors">← Back</a><div><h1>Create a profile</h1></div></header>
      {notices}
      <form action="/api/create_actor" method="post" enctype="multipart/form-data" data-profile-form>
        <div class="err-box profile-form-error" role="alert" hidden></div>
        <section class="profile-section"><div class="profile-section-head"><h2>Profile photo</h2></div>
          <div class="profile-media"><div class="profile-photo"><img id="newProfilePreview" alt="Selected profile image" hidden><span aria-hidden="true">♙</span></div>
          <div class="profile-media-copy"><label class="profile-field">Choose image <input id="newProfilePhoto" class="profile-file" type="file" name="photo" accept="image/*" required></label></div></div>
        </section>
        {actor_form_fields()}
        <div class="profile-form-actions"><a class="profile-cancel" href="/actors">Cancel</a><button class="em-save-btn" type="submit">Create profile</button></div>
      </form>
    </main>
    <script>document.getElementById('newProfilePhoto').addEventListener('change',function(){{var img=document.getElementById('newProfilePreview');if(img.dataset.objectUrl)URL.revokeObjectURL(img.dataset.objectUrl);if(this.files&&this.files[0]){{img.dataset.objectUrl=URL.createObjectURL(this.files[0]);img.src=img.dataset.objectUrl;img.hidden=false;}}else{{img.hidden=true;img.removeAttribute('src');}}}});</script>'''
    return build_page("Create New Profile - RdxTv", content + PROFILE_FORM_JS, "", "actors", role)

@actor_routes.post('/api/create_actor')
async def api_create_actor(req):
    role, _ = await get_auth(req)
    if role != 'admin': return web.json_response({"error": "Unauthorized"}, status=403, dumps=fast_json)
    try:
        reader = await req.multipart()
        name, bio, tags_raw, image_bytes, category = None, None, "", None, "actor"
        insta, yt, twitter = "", "", ""
        links_present, labels, urls = False, [], []
        while True:
            part = await reader.next()
            if part is None: break
            if part.name == 'name': name = (await part.read()).decode().strip()
            elif part.name == 'bio': bio = (await part.read()).decode().strip()
            elif part.name == 'tags': tags_raw = (await part.read()).decode().strip()
            elif part.name == 'category': category = (await part.read()).decode().strip()
            elif part.name == 'insta': insta = _clean_link((await part.read()).decode())
            elif part.name == 'yt': yt = _clean_link((await part.read()).decode())
            elif part.name == 'twitter': twitter = _clean_link((await part.read()).decode())
            elif part.name == 'links_present': links_present = True
            elif part.name == 'link_label': labels.append((await part.read()).decode())
            elif part.name == 'link_url': urls.append((await part.read()).decode())
            elif part.name == 'photo': image_bytes = await part.read()
            
        if not name or not bio or not image_bytes:
            return _actor_result(req, '/admin/create_actor', 'Name, biography and profile photo are required.')
        try:
            links = _parse_profile_links(labels, urls) if links_present else None
        except ValueError as exc:
            return _actor_result(req, '/admin/create_actor', str(exc))

        with io.BytesIO(image_bytes) as img_buffer:
            img_buffer.name = f"{name.replace(' ', '_')}.jpg"
            msg = await temp.BOT.send_photo(chat_id=ACTOR_STORAGE_CHANNEL, photo=img_buffer)
        if not msg or not msg.photo:
            return _actor_result(req, '/admin/create_actor', 'Profile photo upload failed. Please retry.', 500)
        
        tg_photo_id = msg.photo.sizes[-1].file_id if hasattr(msg.photo, "sizes") and msg.photo.sizes else msg.photo.file_id
        now_ts = int(time.time())
        profile = {"name": name, "bio": bio, "category": category, "tags": [t.strip() for t in tags_raw.split(",") if t.strip()], "photo_url": f"TG_ID:{tg_photo_id}", "is_actor_permanent": True, "photo_updated_at": now_ts, "photo_revision": uuid.uuid4().hex, "social_links": {"instagram": insta, "youtube": yt, "twitter": twitter}, "gallery": [], "is_gallery_permanent": True, "created_at": now_ts}
        if links is not None:
            profile["profile_links"] = links
        await actors.insert_one(profile)
        return _actor_result(req, '/actors?msg=Profile+created+successfully!')
    except Exception as e:
        return _actor_result(req, '/admin/create_actor', str(e) or 'Could not create the profile.', 500)


# ─────────────────────────────────────────────────────────
# 🖼️ PHOTO ENGINE (With Cache Control)
# ─────────────────────────────────────────────────────────
@actor_routes.get('/api/actor/photo')
async def get_actor_photo(req):
    actor_id, img_index = req.query.get("id"), req.query.get("gallery_idx")
    if not actor_id: return web.Response(status=400)
    try:
        doc = await actors.find_one({"_id": ObjectId(actor_id)})
        if not doc: return web.Response(status=404)
        if img_index is not None:
            raw_url = doc.get("gallery", [])[int(img_index)]
            headers = {"Cache-Control": "public, max-age=31536000, immutable", "Content-Disposition": 'inline; filename="photo.jpg"'}
        else:
            raw_url = doc.get("photo_url")
            headers = {"Cache-Control": "public, max-age=31536000, immutable", "Content-Disposition": 'inline; filename="avatar.jpg"'}
            
        if not raw_url or not raw_url.startswith("TG_ID:"): return web.Response(status=404)
        file_data = await temp.BOT.download_media(raw_url.replace("TG_ID:", ""), in_memory=True)
        if not file_data: return web.Response(status=404)
        
        body_bytes = file_data.getvalue()
        file_data.close()
        del file_data
        return web.Response(body=body_bytes, content_type="image/jpeg", headers=headers)
    except Exception: return web.Response(status=500)


ACTOR_PROFILE_CSS = '''<style>
.actor-page{max-width:1080px;margin:0 auto;padding:16px 18px 56px}
.actor-topbar{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-bottom:14px}
.actor-back{display:inline-flex;align-items:center;gap:7px;padding:8px 14px;border-radius:999px;background:var(--card);border:1px solid var(--border);color:var(--text);text-decoration:none;font-size:12.5px;font-weight:700;transition:.18s;box-shadow:0 4px 14px rgba(2,6,23,.18)}
.actor-back:hover{border-color:var(--accent-cyan);color:var(--accent-cyan);transform:translateX(-2px)}
.actor-actions{display:flex;align-items:center;flex-wrap:wrap;gap:8px}
.actor-actions button{font-family:inherit;font-size:12px;font-weight:800;border-radius:999px;padding:8px 14px;cursor:pointer;transition:.18s;display:inline-flex;align-items:center;gap:6px}
.actor-action-edit{background:var(--card);color:var(--text);border:1px solid var(--border)}
.actor-action-edit:hover{border-color:var(--accent-cyan);color:var(--accent-cyan)}
.actor-action-delete{background:rgba(244,63,94,.08);color:#fb7185;border:1px solid rgba(244,63,94,.28)}
.actor-action-delete:hover{background:#f43f5e;color:#fff;border-color:#f43f5e}

/* ── Star Hero Card with Ambient Portrait Blur ── */
.actor-header-wrap{position:relative;overflow:hidden;display:flex;flex-direction:row;align-items:center;gap:28px;padding:24px;border-radius:22px;margin-bottom:18px;background:var(--card);border:1px solid var(--border);box-shadow:var(--panel-shadow);isolation:isolate;transition:opacity .22s ease,margin .22s ease}
.actor-header-wrap::before{content:"";position:absolute;top:0;left:0;right:0;height:3px;background:var(--accent-grad);z-index:2}
.actor-backdrop{position:absolute;inset:-24px;background-size:cover;background-position:center 20%;filter:blur(46px) saturate(165%);opacity:.28;z-index:-2;pointer-events:none;transform:scale(1.12)}
.light .actor-backdrop{opacity:.14}
.actor-backdrop-tint{position:absolute;inset:0;background:radial-gradient(circle at 18% 30%,rgba(99,102,241,.18),transparent 58%),linear-gradient(135deg,rgba(5,9,20,.62),rgba(12,21,44,.86));z-index:-1;pointer-events:none}
.light .actor-backdrop-tint{background:radial-gradient(circle at 18% 30%,rgba(79,70,229,.10),transparent 58%),linear-gradient(135deg,rgba(255,255,255,.78),rgba(240,246,255,.92))}

.avatar-box-master{position:relative;width:240px;flex-shrink:0;aspect-ratio:3/4;border-radius:18px;overflow:hidden;background:var(--bg3);border:1px solid rgba(255,255,255,.14);box-shadow:0 18px 42px rgba(2,6,23,.48)}
.light .avatar-box-master{border-color:var(--border);box-shadow:0 14px 32px rgba(15,23,42,.14)}
.avatar-box-master img{display:block;width:100%;height:100%;object-fit:cover;transition:transform .35s ease}
.avatar-box-master:hover img{transform:scale(1.03)}
.avatar-cat-floating{position:absolute;top:10px;left:10px;padding:5px 10px;border-radius:999px;background:rgba(5,9,20,.72);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,.18);color:#fff;font-size:10px;font-weight:800;letter-spacing:.6px;z-index:2}

.actor-identity{flex:1;min-width:0;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:12px}
.actor-name-row{display:flex;align-items:center;gap:10px;flex-wrap:wrap;max-width:100%}
.actor-identity h1{font-size:clamp(24px,3.2vw,36px);font-weight:900;line-height:1.12;letter-spacing:-.6px;color:var(--text);margin:0;overflow-wrap:anywhere}
.actor-verified{display:inline-grid;place-items:center;width:24px;height:24px;border-radius:999px;background:var(--accent-grad);color:#fff;font-size:12px;font-weight:900;box-shadow:0 4px 12px var(--accent-glow);flex-shrink:0}

/* Header minimized on Video & Gallery tabs */
.actor-header-compact{padding:14px 18px;margin-bottom:14px;border-radius:18px;gap:16px}
.actor-header-compact .avatar-box-master{width:56px;height:72px;border-radius:12px;box-shadow:0 6px 18px rgba(2,6,23,.32)}
.actor-header-compact .avatar-cat-floating{display:none}
.actor-header-compact .actor-identity{gap:4px}
.actor-header-compact .actor-identity h1{font-size:18px}
.actor-header-compact .actor-quick-stats,.actor-header-compact .actor-chips,.actor-header-compact .actor-links{display:none}

.actor-quick-stats{display:flex;flex-wrap:wrap;gap:8px;max-width:100%}
.actor-stat-pill{display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:999px;background:rgba(99,102,241,.11);border:1px solid rgba(99,102,241,.26);color:var(--text);font-size:11.5px;font-weight:700;cursor:pointer;font-family:inherit;transition:.18s}
.actor-stat-pill:hover{border-color:var(--accent-cyan);color:var(--accent-cyan);transform:translateY(-1px)}

.actor-chips,.actor-links{display:flex;flex-wrap:wrap;gap:7px;max-width:100%}
.actor-category{padding:5px 11px;border-radius:999px;font-size:10.5px;font-weight:800;background:var(--accent-grad);color:#fff;letter-spacing:.4px}
.actor-tag{padding:5px 11px;border-radius:999px;font-size:11px;font-weight:700;border:1px solid var(--border);background:var(--bg3);color:var(--muted);cursor:pointer;transition:.16s;overflow-wrap:anywhere}
.actor-tag:hover{border-color:var(--accent-cyan);color:var(--accent-cyan);background:var(--bg4)}

.actor-link{display:inline-flex;align-items:center;gap:6px;color:var(--text);background:var(--bg3);border:1px solid var(--border);border-radius:999px;padding:7px 14px;text-decoration:none;font-size:12px;font-weight:700;overflow-wrap:anywhere;transition:.18s}
.actor-link:hover{border-color:var(--accent-cyan);background:var(--bg4);transform:translateY(-1px)}

/* ── Native App Segmented Pill Tabs ── */
.actor-tab-bar{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;background:var(--card);border:1px solid var(--border);padding:5px;border-radius:16px;margin-bottom:18px;box-shadow:0 6px 20px rgba(2,6,23,.16)}
.actor-tab{background:transparent;border:none;border-radius:11px;color:var(--muted);padding:11px 10px;font-size:13px;font-weight:800;cursor:pointer;transition:.2s;font-family:inherit;display:flex;align-items:center;justify-content:center;gap:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.actor-tab:hover{color:var(--text);background:var(--bg3)}
.actor-tab.active{background:var(--accent-grad);color:#fff!important;box-shadow:0 6px 18px var(--accent-glow)}
.actor-panel{display:none;animation:actorFadeIn .2s ease}.actor-panel.active{display:block!important}
@keyframes actorFadeIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}

/* ── Info Bio Card ── */
.actor-bio{position:relative;background:var(--card);border:1px solid var(--border);border-radius:18px;padding:22px 24px;box-shadow:var(--panel-shadow);overflow:hidden}
.actor-bio::before{content:"";position:absolute;top:0;bottom:0;left:0;width:4px;background:var(--accent-grad)}
.actor-bio-copy{line-height:1.8;color:var(--text);font-size:14.5px;white-space:pre-line;overflow-wrap:anywhere}

/* ── Linked Media Control Bar ── */
.search-zone-actor{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:14px;margin-bottom:18px;box-shadow:var(--panel-shadow)}
.search-row1-actor{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.search-row2-actor{display:flex;align-items:center;justify-content:flex-start;gap:8px;flex-wrap:wrap}
@media(max-width:767px){.search-row2-actor .cdd-wrap-actor{flex:1 1 0;min-width:0;display:flex}.search-row2-actor .cdd-btn-actor{width:100%;box-sizing:border-box;justify-content:center}}
@media(min-width:768px){.search-zone-actor{display:flex;align-items:center;gap:10px;flex-wrap:nowrap}.search-row1-actor{flex:1;margin-bottom:0}.search-row2-actor{flex-shrink:0}}
.search-wrap-actor{flex:1;min-width:0;display:flex;align-items:center;background:var(--bg3);border:1.5px solid var(--border);border-radius:12px;padding:0 10px 0 14px;gap:8px;min-height:40px;transition:border-color .18s}
.search-wrap-actor:focus-within{border-color:var(--accent-cyan)}
.search-spinner-actor{display:none;width:15px;height:15px;flex-shrink:0;border:2px solid var(--border);border-top-color:var(--accent-cyan);border-radius:50%;animation:searchSpinActor .6s linear infinite}
.search-wrap-actor.loading .search-spinner-actor{display:inline-block}
@keyframes searchSpinActor{to{transform:rotate(360deg)}}
.search-input-actor{flex:1;min-width:0;width:100%;background:transparent;border:none;outline:none;color:var(--text);font-size:14px;font-weight:600;padding:8px 0;font-family:inherit}
.search-input-actor::placeholder{color:var(--muted);font-weight:500}
.cdd-wrap-actor{flex:0 1 auto;min-width:0;position:relative;user-select:none}
.cdd-btn-actor{width:auto;background:var(--bg3);color:var(--text);border:1.5px solid var(--border);border-radius:10px;padding:9px 28px 9px 13px;font-size:12px;font-weight:700;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:5px;white-space:nowrap;transition:border-color .15s}
.cdd-btn-actor.open,.cdd-btn-actor:hover{border-color:var(--accent-cyan)}
.cdd-arrow-actor{position:absolute;right:11px;top:50%;transform:translateY(-50%);pointer-events:none;font-size:9px;color:var(--muted);transition:transform .2s}
.cdd-btn-actor.open+.cdd-arrow-actor{transform:translateY(-50%) rotate(180deg)}
.cdd-menu-actor{position:absolute;top:calc(100% + 7px);right:0;min-width:170px;background:var(--bg2);border:1.5px solid var(--border);border-radius:14px;overflow:hidden;z-index:9999;box-shadow:0 14px 38px rgba(2,6,23,.55);display:none}
.cdd-item-actor{display:flex;align-items:center;gap:10px;padding:11px 14px;font-size:12px;font-weight:700;color:var(--text);cursor:pointer;transition:background .12s;border-bottom:1px solid var(--border)}
.cdd-item-actor:last-child{border-bottom:none}.cdd-item-actor:hover{background:var(--bg3)}
.cdd-item-actor.selected{color:var(--accent-cyan)}
.cdd-radio-actor{width:15px;height:15px;border-radius:50%;border:2px solid var(--border);margin-left:auto;flex-shrink:0;display:flex;align-items:center;justify-content:center}
.cdd-item-actor.selected .cdd-radio-actor{border-color:var(--accent-cyan)}
.cdd-radio-dot-actor{width:6px;height:6px;border-radius:50%;background:var(--accent-cyan);display:none}
.cdd-item-actor.selected .cdd-radio-dot-actor{display:block}

/* ── Portrait Gallery Grid & Cinema Lightbox ── */
.actor-gallery-upload{display:flex;align-items:center;justify-content:space-between;gap:12px;background:var(--card);border:1px solid var(--border);border-radius:16px;padding:13px 16px;margin-bottom:16px}
.actor-gallery-upload strong{font-size:13.5px;display:flex;align-items:center;gap:7px}
.actor-gallery-choose{display:inline-flex;align-items:center;justify-content:center;gap:6px;position:relative;overflow:hidden;padding:9px 16px;background:var(--accent-grad);color:#fff;border-radius:999px;font-size:12px;font-weight:800;cursor:pointer;white-space:nowrap;box-shadow:0 6px 18px var(--accent-glow);transition:transform .16s}
.actor-gallery-choose:hover{transform:translateY(-1px)}
.actor-gallery-choose input{position:absolute;inset:0;width:100%;height:100%;opacity:0;cursor:pointer}
.actor-gallery-choose:focus-within{outline:2px solid var(--accent-cyan);outline-offset:3px}
.actor-gallery-empty{text-align:center;background:var(--card);border:1px dashed var(--border);border-radius:18px;padding:42px 20px;color:var(--muted)}
.actor-gallery-empty strong{display:block;font-size:14.5px;color:var(--text);margin-bottom:4px}
.actor-gallery-empty p{font-size:12.5px}
.gallery-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(145px,1fr));gap:12px}
@media(min-width:640px){.gallery-grid{grid-template-columns:repeat(auto-fill,minmax(185px,1fr));gap:15px}}
.gallery-item-wrap{position:relative;border-radius:14px;overflow:hidden;border:1px solid var(--border);aspect-ratio:3/4;cursor:pointer;background:var(--bg3);box-shadow:0 8px 22px rgba(2,6,23,.24)}
.gallery-item{width:100%;height:100%;object-fit:cover;transition:transform .3s cubic-bezier(.22,1,.36,1)}
.gallery-item-wrap:hover .gallery-item{transform:scale(1.05)}
.gallery-del-btn{position:absolute;bottom:10px;right:10px;background:rgba(15,23,42,.82);backdrop-filter:blur(8px);border:1px solid rgba(244,63,94,.45);color:#fb7185;padding:5px 10px;border-radius:999px;font-size:10.5px;font-weight:800;cursor:pointer;z-index:5;opacity:0;transition:.18s}
.gallery-del-btn:hover{background:#f43f5e;color:#fff;border-color:#f43f5e}
.gallery-item-wrap:hover .gallery-del-btn{opacity:1}

.lightbox{position:fixed;inset:0;background:rgba(3,7,18,.94);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);z-index:99999;display:none;align-items:center;justify-content:center;opacity:0;transition:opacity .2s ease}
.lightbox.open{display:flex;opacity:1}
.lightbox-img{max-width:90vw;max-height:86vh;object-fit:contain;border-radius:14px;box-shadow:0 20px 60px rgba(0,0,0,.85);transform:scale(.96);transition:transform .22s cubic-bezier(.22,1,.36,1)}
.lightbox.open .lightbox-img{transform:scale(1)}
.lightbox-close{position:absolute;top:18px;right:18px;width:40px;height:40px;border-radius:999px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);color:#fff;font-size:24px;cursor:pointer;display:grid;place-items:center;transition:.18s}
.lightbox-close:hover{background:#f43f5e;border-color:#f43f5e}
.lightbox-nav{position:absolute;top:50%;transform:translateY(-50%);width:44px;height:44px;border-radius:999px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);color:#fff;font-size:22px;font-weight:800;cursor:pointer;display:grid;place-items:center;transition:.18s}
.lightbox-nav:hover{background:var(--accent-grad);border-color:transparent}
.lightbox-nav.prev{left:16px}.lightbox-nav.next{right:16px}
.lightbox-counter{position:absolute;bottom:20px;left:50%;transform:translateX(-50%);padding:6px 14px;border-radius:999px;background:rgba(15,23,42,.78);border:1px solid rgba(255,255,255,.15);color:#fff;font-size:12px;font-weight:700}

@media(max-width:640px){
  .actor-page{padding:12px 10px 48px}
  .actor-header-wrap{flex-direction:column;align-items:center;text-align:center;gap:18px;padding:22px 16px;border-radius:20px}
  .avatar-box-master{width:100%;max-width:280px;min-width:240px;align-self:center;border-radius:18px}
  .actor-identity{align-items:center}
  .actor-name-row,.actor-quick-stats,.actor-chips,.actor-links{justify-content:center}
  .actor-identity h1{font-size:24px}
  .actor-header-compact{flex-direction:row;align-items:center;text-align:left;gap:14px;padding:12px 14px;border-radius:16px}
  .actor-header-compact .avatar-box-master{width:52px;min-width:52px;max-width:52px;height:68px;border-radius:10px}
  .actor-header-compact .actor-identity{align-items:flex-start}
  .actor-header-compact .actor-name-row{justify-content:flex-start}
  .actor-header-compact .actor-identity h1{font-size:17px}
  .actor-tab-bar{padding:4px;gap:4px;border-radius:14px}
  .actor-tab{padding:10px 6px;font-size:11.5px;gap:4px}
  .actor-bio{padding:18px}
  .cdd-menu-actor{left:0;right:auto}
  .lightbox-nav{width:38px;height:38px;font-size:18px}.lightbox-nav.prev{left:10px}.lightbox-nav.next{right:10px}
}
</style>'''


# ─────────────────────────────────────────────────────────
# 🌐 PROFILE VIEW: INDIVIDUAL DISPLAY & MEDIA
# ─────────────────────────────────────────────────────────
@actor_routes.get('/actor/{id}')
async def actor_profile_display(req):
    role, tg_id = await get_auth(req)
    if not role: return web.HTTPFound('/login')
    if not await require_active_plan(role, tg_id): return web.HTTPFound('/premium_expired')
    try:
        actor_id = req.match_info['id']
        actor = await actors.find_one({"_id": ObjectId(actor_id)})
        if not actor: return web.Response(text="Profile Not Found", status=404)
    except: return web.Response(text="Invalid ID", status=400)
        
    actor_name, tags_list, category = actor["name"], actor.get("tags", []), actor.get("category", "actor")
    links, gallery_list = _profile_links(actor), actor.get("gallery", [])
    
    cat_emoji = "🎭" if category == "actor" else "📱" if category == "app" else "🌐"
    cat_floating = f'<span class="avatar-cat-floating">{cat_emoji} {html.escape(str(category).upper())}</span>'
    t_html = "".join(
        f'<button type="button" class="actor-tag" onclick="jumpActorTag({html.escape(fast_json(t), quote=True)})">#{html.escape(t)}</button>'
        for t in tags_list
    )
    tags_chips_html = f'<div class="actor-chips">{t_html}</div>' if t_html else ''
    s_html = "".join(
        f'<a class="actor-link" href="{html.escape(link["url"], quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(link["label"])}</a>'
        for link in links
    )
    social_html = f'<div class="actor-links" aria-label="Profile links">{s_html}</div>' if s_html else ''

    gallery_v = actor.get("gallery_revision") or int(actor.get("gallery_updated_at") or actor.get("photo_updated_at") or actor.get("created_at") or 0)
    gallery_urls = [f"/api/actor/photo?id={actor_id}&gallery_idx={i}&v={gallery_v}" for i in range(len(gallery_list))]
    gallery_urls_json = html.escape(fast_json(gallery_urls), quote=True)

    gallery_grid_html = f'''<div class="actor-gallery-upload"><strong>📸 Photos ({len(gallery_list)})</strong><form action="/api/actor/gallery_upload" method="post" enctype="multipart/form-data"><input type="hidden" name="actor_id" value="{actor_id}"><label class="actor-gallery-choose">➕ Add Photos<input type="file" name="gallery_img" accept="image/*" multiple onchange="this.form.submit()"></label></form></div>''' if role == 'admin' else ""
    if not gallery_list:
        gallery_grid_html += '<div class="actor-gallery-empty"><strong>No photos yet</strong><p>Gallery images will appear here.</p></div>'
    else:
        g_items = "".join([f'<div class="gallery-item-wrap" onclick="openLightboxIdx({i})"><img src="{gallery_urls[i]}" class="gallery-item" loading="lazy">' + (f'<button class="gallery-del-btn" onclick="deleteGalleryImage(\'{actor_id}\', {i}, event)">🗑️ Delete</button>' if role=='admin' else "") + '</div>' for i in range(len(gallery_list))])
        gallery_grid_html += f'<div class="gallery-grid">{g_items}</div>'

    admin_actions_html = f'''<div class="actor-actions"><button type="button" class="actor-action-edit" onclick="openActorEditModal()">✏️ Edit Profile</button><button type="button" class="actor-action-delete" onclick="deleteActorProfile('{actor_id}')">🗑️ Delete</button></div>''' if role == 'admin' else ""

    tags_json_payload = html.escape(fast_json(tags_list))
    safe_bio = html.escape(actor.get("bio", ""))
    photo_v = actor.get("photo_revision") or int(actor.get("photo_updated_at") or actor.get("created_at") or 0)
    avatar_url = f"/api/actor/photo?id={actor_id}&v={photo_v}"
    safe_avatar_css = html.escape(avatar_url, quote=True)

    profile_edit_modal = f'''
    <div class="edit-modal" id="actorEditModal" role="dialog" aria-modal="true" aria-labelledby="actorEditTitle" onclick="if(event.target===this)closeActorEditModal()">
      <div class="em-card profile-modal-card"><button class="em-close" type="button" aria-label="Close" onclick="closeActorEditModal()">&#10005;</button>
        <h2 class="em-title" id="actorEditTitle">Edit profile</h2>
        <div class="profile-section"><div class="profile-media"><div class="profile-photo"><img id="actorEditPreview" src="/api/actor/photo?id={actor_id}&amp;v={html.escape(str(photo_v), quote=True)}" alt="Current profile photo"></div>
          <div class="profile-media-copy"><label class="profile-field">Profile photo<input class="profile-file" type="file" accept="image/*" onchange="updateActorAvatar('{actor_id}',this)"></label><div class="profile-help">Updated immediately when selected.</div></div></div></div>
        <form action="/api/actor/update_profile" method="post" data-profile-form><input type="hidden" name="actor_id" value="{actor_id}">
          <div class="err-box profile-form-error" role="alert" hidden></div>
          {actor_form_fields(actor_name, category, actor.get("bio", ""), ", ".join(tags_list), links)}
          <div class="profile-form-actions"><button class="profile-cancel" type="button" onclick="closeActorEditModal()">Cancel</button><button class="em-save-btn" type="submit">Save changes</button></div>
        </form>
      </div>
    </div>''' if role == 'admin' else ""
    
    ap_mode_tg_lbl = "🖼️ Poster"
    ap_mode_none_lbl = "📄 Text"
    ap_mode_lbl = ap_mode_none_lbl if DEFAULT_MEDIA_MODE == "none" else ap_mode_tg_lbl
    ap_sel_tg = " selected" if DEFAULT_MEDIA_MODE == "tg" else ""
    ap_sel_none = " selected" if DEFAULT_MEDIA_MODE == "none" else ""

    quick_stats_html = (
        '<div class="actor-quick-stats">'
        '<button type="button" class="actor-stat-pill" onclick="activateActorTab(\'tab-video\')">🎬 Videos</button>'
        f'<button type="button" class="actor-stat-pill" onclick="activateActorTab(\'tab-gallery\')">📸 {len(gallery_list)} Photos</button>'
        '</div>'
    )

    page_html = f'''{ACTOR_PROFILE_CSS}<main class="actor-page"><div class="actor-topbar"><a class="actor-back" href="/actors">← Back</a>{admin_actions_html}</div><div class="actor-header-wrap" id="actorHeaderWrap"><div class="actor-backdrop" id="actorHeroBackdrop" style="background-image:url('{safe_avatar_css}')"></div><div class="actor-backdrop-tint"></div><div class="avatar-box-master">{cat_floating}<img id="actorMasterAvatarImage" src="{avatar_url}" alt="{html.escape(actor_name, quote=True)} profile photo"></div><div class="actor-identity"><div class="actor-name-row"><h1>{html.escape(actor_name)}</h1><span class="actor-verified" aria-hidden="true">✓</span></div>{quick_stats_html}{tags_chips_html}{social_html}</div></div><div class="actor-tab-bar"><button class="actor-tab active" data-tab-target="tab-info" onclick="switchActorTab(event,'tab-info')">ℹ️ Info</button><button class="actor-tab" data-tab-target="tab-video" onclick="switchActorTab(event,'tab-video')">🎬 Linked Media</button><button class="actor-tab" data-tab-target="tab-gallery" onclick="switchActorTab(event,'tab-gallery')">🖼️ Gallery</button></div><div id="tab-info" class="actor-panel active"><section class="actor-bio"><div class="actor-bio-copy">{safe_bio}</div></section></div><div id="tab-video" class="actor-panel"><div class="search-zone-actor"><div class="search-row1-actor"><div class="search-wrap-actor" id="actMovieWrap"><input type="text" id="actor_movie_q" value="" placeholder="Search inside this profile..." class="search-input-actor"><span class="search-spinner-actor" id="actMovieSpinner"></span></div><div class="cdd-wrap-actor gf-wrap" id="cddGfWrapActor" onclick="toggleActorCdd('gf',event)"><button type="button" class="cdd-btn-actor" id="cddGfBtnActor" aria-label="Group filter: All" aria-expanded="false"><span id="cddGfLabelActor">All</span></button><span class="cdd-arrow-actor" aria-hidden="true">&#9660;</span><div class="cdd-menu-actor" id="cddGfMenuActor" style="display:none"><div class="cdd-item-actor selected" data-val="all" onclick="pickActorGF('all','All',this,event)">All<span class="cdd-radio-actor"><span class="cdd-radio-dot-actor"></span></span></div><div class="cdd-item-actor" data-val="group" onclick="pickActorGF('group','Group',this,event)">Group<span class="cdd-radio-actor"><span class="cdd-radio-dot-actor"></span></span></div><div class="cdd-item-actor" data-val="single" onclick="pickActorGF('single','UnGroup',this,event)">UnGroup<span class="cdd-radio-actor"><span class="cdd-radio-dot-actor"></span></span></div></div></div></div><div class="search-row2-actor"><div class="cdd-wrap-actor"><div class="cdd-btn-actor" id="cddColBtnActor" onclick="toggleActorCdd('col',event)"><span id="cddColLabelActor">All</span></div><span class="cdd-arrow-actor">&#9660;</span><div class="cdd-menu-actor" id="cddColMenuActor"><div class="cdd-item-actor selected" data-val="all" onclick="pickActorCol('all','All',this,event)">All<span class="cdd-radio-actor"><span class="cdd-radio-dot-actor"></span></span></div><div class="cdd-item-actor" data-val="primary" onclick="pickActorCol('primary','🟢 Primary',this,event)">🟢 Primary<span class="cdd-radio-actor"><span class="cdd-radio-dot-actor"></span></span></div><div class="cdd-item-actor" data-val="cloud" onclick="pickActorCol('cloud','🔵 Cloud',this,event)">🔵 Cloud<span class="cdd-radio-actor"><span class="cdd-radio-dot-actor"></span></span></div><div class="cdd-item-actor" data-val="archive" onclick="pickActorCol('archive','🟠 Archive',this,event)">🟠 Archive<span class="cdd-radio-actor"><span class="cdd-radio-dot-actor"></span></span></div></div></div><div class="cdd-wrap-actor"><div class="cdd-btn-actor" id="cddModeBtnActor" onclick="toggleActorCdd('mode',event)"><span id="cddModeLabelActor">{ap_mode_lbl}</span></div><span class="cdd-arrow-actor">&#9660;</span><div class="cdd-menu-actor" id="cddModeMenuActor"><div class="cdd-item-actor{ap_sel_tg}" data-val="tg" onclick="pickActorMode('tg','🖼️ Poster',this,event)">🖼️ Poster<span class="cdd-radio-actor"><span class="cdd-radio-dot-actor"></span></span></div><div class="cdd-item-actor{ap_sel_none}" data-val="none" onclick="pickActorMode('none','📄 Text',this,event)">📄 Text<span class="cdd-radio-actor"><span class="cdd-radio-dot-actor"></span></span></div></div></div></div></div><div id="actor_video_results" class="res-grid"></div><div class="pagination" id="actor_page_box" style="display:none"><button class="pg-btn" id="actor_pBtn" onclick="actorPagePrev()" disabled>Previous</button><span class="pg-info" id="actor_pgInfo">Page 1</span><button class="pg-btn" id="actor_nBtn" onclick="actorPageNext()">Next</button></div></div><div id="tab-gallery" class="actor-panel">{gallery_grid_html}</div></main><div id="actorLightboxModal" class="lightbox" onclick="closeLightbox()"><button type="button" class="lightbox-close" aria-label="Close preview" onclick="closeLightbox()">&times;</button><button type="button" class="lightbox-nav prev" id="lbPrevBtn" aria-label="Previous photo" onclick="stepLightbox(-1,event)">&#8249;</button><img id="lightboxTargetImg" class="lightbox-img" src="" onclick="event.stopPropagation()"><button type="button" class="lightbox-nav next" id="lbNextBtn" aria-label="Next photo" onclick="stepLightbox(1,event)">&#8250;</button><div class="lightbox-counter" id="lbCounter"></div></div><input type="hidden" id="actor_master_tags_payload" value="{tags_json_payload}">{profile_edit_modal}<script>var actCurPage=1,actOffset=0,actNextOffset="",actLimit={MAX_WEB_RESULTS},actCol="all",actGF="all",actMode=MediaView.media("{DEFAULT_MEDIA_MODE}"),actMovieReqId=0,actGalleryUrls={gallery_urls_json},actLbIdx=0;document.getElementById('cddModeLabelActor').textContent=actMode==='none'?'📄 Text':'🖼️ Poster';document.querySelectorAll('#cddModeMenuActor .cdd-item-actor').forEach(i=>i.classList.toggle('selected',i.dataset.val===actMode));MediaView.subscribe(function(value){{var mode=value==='text'?'none':'tg';if(mode===actMode)return;actMode=mode;document.getElementById('cddModeLabelActor').textContent=mode==='none'?'📄 Text':'🖼️ Poster';document.querySelectorAll('#cddModeMenuActor .cdd-item-actor').forEach(i=>i.classList.toggle('selected',i.dataset.val===mode));resetActorSearchPage();if(document.getElementById('actor_video_results').innerHTML)triggerActorSearchAjax();}});function closeActorCdds(){{['cddCol','cddMode','cddGf'].forEach(function(k){{var m=document.getElementById(k+'MenuActor'),b=document.getElementById(k+'BtnActor');if(m)m.style.display='none';if(b)b.classList.remove('open');}});}}function toggleActorCdd(w,e){{if(e)e.stopPropagation();var map={{col:'cddCol',mode:'cddMode',gf:'cddGf'}};var target=map[w]||'cddCol';['cddCol','cddMode','cddGf'].forEach(function(k){{if(k!==target){{var m=document.getElementById(k+'MenuActor'),b=document.getElementById(k+'BtnActor');if(m)m.style.display='none';if(b)b.classList.remove('open');}}}});var tm=document.getElementById(target+'MenuActor'),tb=document.getElementById(target+'BtnActor');if(tm.style.display==='block'){{tm.style.display='none';tb.classList.remove('open');}}else{{tm.style.display='block';tb.classList.add('open');}}}}function pickActorCol(v,l,el,e){{if(e)e.stopPropagation();actCol=v;document.getElementById('cddColLabelActor').textContent=l;document.querySelectorAll('#cddColMenuActor .cdd-item-actor').forEach(i=>i.classList.remove('selected'));el.classList.add('selected');closeActorCdds();resetActorSearchPage();triggerActorSearchAjax();}}function pickActorGF(v,l,el,e){{if(e)e.stopPropagation();actGF=v;document.getElementById('cddGfLabelActor').textContent=l;var b=document.getElementById('cddGfBtnActor');if(b)b.setAttribute('aria-label','Group filter: '+l);document.querySelectorAll('#cddGfMenuActor .cdd-item-actor').forEach(i=>i.classList.remove('selected'));el.classList.add('selected');closeActorCdds();resetActorSearchPage();triggerActorSearchAjax();}}function pickActorMode(v,l,el,e){{if(e)e.stopPropagation();actMode=v;MediaView.set(v);document.getElementById('cddModeLabelActor').textContent=l;document.querySelectorAll('#cddModeMenuActor .cdd-item-actor').forEach(i=>i.classList.remove('selected'));el.classList.add('selected');closeActorCdds();resetActorSearchPage();triggerActorSearchAjax();}}document.addEventListener('click',closeActorCdds);function _paintLightbox(){{var u=actGalleryUrls[actLbIdx]||'';document.getElementById('lightboxTargetImg').src=u;var c=document.getElementById('lbCounter'),p=document.getElementById('lbPrevBtn'),n=document.getElementById('lbNextBtn');var multi=actGalleryUrls.length>1;if(c){{c.textContent=actGalleryUrls.length?(actLbIdx+1)+' / '+actGalleryUrls.length:'';c.style.display=actGalleryUrls.length?'block':'none';}}if(p)p.style.display=multi?'grid':'none';if(n)n.style.display=multi?'grid':'none';}}function openLightboxIdx(idx){{actLbIdx=Math.max(0,Math.min(idx,actGalleryUrls.length-1));_paintLightbox();var lb=document.getElementById('actorLightboxModal');lb.style.display='flex';setTimeout(()=>lb.classList.add('open'),10);}}function openLightbox(s){{var idx=actGalleryUrls.indexOf(s);if(idx>=0){{openLightboxIdx(idx);return;}}document.getElementById('lightboxTargetImg').src=s;document.getElementById('lbPrevBtn').style.display='none';document.getElementById('lbNextBtn').style.display='none';document.getElementById('lbCounter').style.display='none';var lb=document.getElementById('actorLightboxModal');lb.style.display='flex';setTimeout(()=>lb.classList.add('open'),10);}}function stepLightbox(d,e){{if(e)e.stopPropagation();if(!actGalleryUrls.length)return;actLbIdx=(actLbIdx+d+actGalleryUrls.length)%actGalleryUrls.length;_paintLightbox();}}function closeLightbox(){{var lb=document.getElementById('actorLightboxModal');lb.classList.remove('open');setTimeout(()=>lb.style.display='none',200);}}document.addEventListener('keydown',function(e){{var lb=document.getElementById('actorLightboxModal');if(!lb||!lb.classList.contains('open'))return;if(e.key==='Escape')closeLightbox();else if(e.key==='ArrowLeft')stepLightbox(-1);else if(e.key==='ArrowRight')stepLightbox(1);}});function activateActorTab(tId){{document.querySelectorAll('.actor-panel').forEach(p=>p.classList.remove('active'));document.querySelectorAll('.actor-tab').forEach(t=>t.classList.toggle('active',t.dataset.tabTarget===tId));document.getElementById(tId).classList.add('active');var head=document.getElementById('actorHeaderWrap');if(head){{if(tId==='tab-info')head.classList.remove('actor-header-compact');else head.classList.add('actor-header-compact');}}if(tId==='tab-video'&&!document.getElementById('actor_video_results').innerHTML)triggerActorSearchAjax();}}function switchActorTab(ev,tId){{activateActorTab(tId);}}function jumpActorTag(tag){{var inp=document.getElementById('actor_movie_q');if(inp)inp.value=tag;activateActorTab('tab-video');resetActorSearchPage();triggerActorSearchAjax();}}function openActorEditModal(){{document.getElementById('actorEditModal').classList.add('open');}}function closeActorEditModal(){{var m=document.getElementById('actorEditModal'),f=m&&m.querySelector('form[data-profile-form]');if(f&&f.dataset.saving==='true'){{showToast('Please wait for the save to finish.');return;}}if(m)m.classList.remove('open');}}function resetActorSearchPage(){{actCurPage=1;actOffset=0;}}async function triggerActorSearchAjax(){{var q=document.getElementById('actor_movie_q').value.trim(),grid=document.getElementById('actor_video_results');var wrap=document.getElementById('actMovieWrap');var myReq=++actMovieReqId;var loadTimer=setTimeout(function(){{if(myReq!==actMovieReqId)return;if(wrap)wrap.classList.add('loading');}},150);try{{var r=await fetch('/api/actor/search?q='+encodeURIComponent(q)+'&offset='+actOffset+'&col='+actCol+'&gf='+actGF+'&mode='+actMode+'&id={actor_id}');if(myReq!==actMovieReqId){{clearTimeout(loadTimer);return;}}clearTimeout(loadTimer);if(wrap)wrap.classList.remove('loading');if(!r.ok)throw new Error('HTTP '+r.status);var d=await r.json();if(myReq!==actMovieReqId)return;grid.className='res-grid mode-'+actMode;if(!d.results||!d.results.length){{grid.innerHTML='<div class="empty"><p>No video assets matching filters found.</p></div>';document.getElementById('actor_page_box').style.display='none';return;}}var h='',isAdmin=document.getElementById('editCombinedModal')!==null;d.results.forEach(f=>{{if(f.group){{h+=actorGroupHtml(f,actMode,isAdmin);}}else{{h+=renderActorMediaCard(f,actMode,isAdmin);}}}});grid.innerHTML=h;staggerCards(grid);actNextOffset=d.next_offset;document.getElementById('actor_page_box').style.display='flex';document.getElementById('actor_pBtn').disabled=(actOffset===0);document.getElementById('actor_nBtn').disabled=!actNextOffset;document.getElementById('actor_pgInfo').textContent='Page '+actCurPage;}}catch(e){{clearTimeout(loadTimer);if(myReq!==actMovieReqId)return;if(wrap)wrap.classList.remove('loading');grid.innerHTML='<div class="empty"><p>Could not load linked videos. Please retry.</p></div>';}}}}var actorAvatarInProgress=false;async function updateActorAvatar(aid,input){{var field=input,f=field&&field.files[0];if(!f)return;if(actorAvatarInProgress){{field.value='';showToast('Please wait for the current photo upload.');return;}}actorAvatarInProgress=true;var save=document.querySelector('#actorEditModal button[type=submit]'),oldLabel=save&&save.textContent;if(save){{save.disabled=true;save.textContent='Uploading photo…';}}var fd=new FormData();fd.append('actor_id',aid);fd.append('photo',f);field.disabled=true;try{{var r=await fetch('/api/actor/update_avatar',{{method:'POST',body:fd}}),d=await r.json();if(!r.ok||!d.success)throw new Error(d.error||'Upload failed');var src='/api/actor/photo?id='+encodeURIComponent(aid)+'&v='+encodeURIComponent(d.photo_revision||Date.now());document.getElementById('actorMasterAvatarImage').src=src;var bd=document.getElementById('actorHeroBackdrop');if(bd)bd.style.backgroundImage='url("'+src+'")';var preview=document.getElementById('actorEditPreview');if(preview)preview.src=src;showToast('Profile photo updated.');}}catch(e){{showToast(e.message||'Network update error','error');}}finally{{field.value='';field.disabled=false;actorAvatarInProgress=false;if(save){{save.disabled=false;save.textContent=oldLabel;}}}}}}async function deleteGalleryImage(aid,idx,e){{if(e)e.stopPropagation();if(!confirm("Delete this photo from gallery permanently?"))return;try{{var r=await fetch('/api/actor/gallery_delete',{{method:'POST',body:JSON.stringify({{actor_id:aid,index:idx}}),headers:{{'Content-Type':'application/json'}}}}),d=await r.json();if(d.success){{alert("Image removed from gallery!");window.location.reload();}}else alert(d.error||"Delete failed!");}}catch(e){{alert("Network deletion error!");}}}}async function deleteActorProfile(id){{if(!confirm("Are you sure you want to permanently delete this profile?"))return;try{{var r=await fetch('/api/actor/delete?id='+id,{{method:'POST'}}),d=await r.json();if(d.success){{alert("Profile deleted successfully!");window.location.href='/actors';}}else alert(d.error||"Deletion failed!");}}catch(e){{alert("Network communication error!");}}}}function actorPageNext(){{if(actNextOffset){{actCurPage++;actOffset=actNextOffset;triggerActorSearchAjax();window.scrollTo(0,350);}}}}function actorPagePrev(){{if(actCurPage>1){{actCurPage--;actOffset=Math.max(0,actOffset-actLimit);triggerActorSearchAjax();window.scrollTo(0,350);}}}}document.getElementById('actor_movie_q').addEventListener('keydown',function(e){{if(e.key==='Enter'){{clearTimeout(actMovieLiveTimer);resetActorSearchPage();triggerActorSearchAjax();}}}});var actMovieLiveTimer;document.getElementById('actor_movie_q').addEventListener('input',function(){{clearTimeout(actMovieLiveTimer);actMovieLiveTimer=setTimeout(function(){{resetActorSearchPage();triggerActorSearchAjax();}},350);}});</script>'''
    
    return build_page(f"{actor_name} - RdxTv Profile", ACTOR_FORM_CSS + page_html + ACTOR_MEDIA_SCRIPT + PROFILE_FORM_JS, "", "actors", role)

# ─────────────────────────────────────────────────────────
# ⚙️ PROFILE PAGE: INTERNAL FILE SEARCH API
# ─────────────────────────────────────────────────────────
@actor_routes.get('/api/actor/search')
async def api_actor_search_handler(req):
    role, tg_id = await get_auth(req)
    if not role or not await require_active_plan(role, tg_id):
        return web.json_response({"error": "Unauthorized"}, status=403, dumps=fast_json)
    actor_id, q_custom = req.query.get("id"), req.query.get("q", "").strip()
    # नोट: `mode` query-param अब पढ़ा नहीं जाता — इस handler में thumbnail हमेशा
    # tg_thumb के तौर पर भेजा जाता है, इसलिए variable bind करना dead code था।
    off, col = req.query.get("offset", "0"), req.query.get("col", "all").lower()
    
    if not actor_id: return web.json_response({"results": []}, dumps=fast_json)
    try: off = max(0, int(off))
    except: off = 0
        
    if not ObjectId.is_valid(actor_id):
        return web.json_response({"error": "Invalid profile ID"}, status=400, dumps=fast_json)
    actor = await actors.find_one({"_id": ObjectId(actor_id)})
    if not actor: return web.json_response({"results": []}, dumps=fast_json)
    
    tags_list = actor.get("tags", [])
    search_query, final_tags = (q_custom, []) if q_custom else (tags_list[0] if tags_list else "", tags_list)
    if not search_query: return web.json_response({"results": [], "next_offset": ""}, dumps=fast_json)
        
    lim = MAX_WEB_RESULTS
    all_m, next_offset = await get_actor_search_results(search_query, final_tags, max_results=lim, offset=off, collection_type=col)
    
    # Use the same thumbnail revision and file-reference logic as the dashboard.
    results_list = await _annotate_raw_groups(_build_results_list(all_m, "tg"))
    
    gf = req.query.get("gf", "all").lower()
    if gf in ("group", "single"):
        manual = await _manual_map(results_list)
        grouped_cards = group_results(results_list, manual)
        if gf == "group":
            results_list = [c for c in grouped_cards if c.get("group")]
        elif gf == "single":
            results_list = [c for c in grouped_cards if not c.get("group")]
        
    return web.json_response({"results": results_list, "next_offset": next_offset}, dumps=fast_json)

# ─────────────────────────────────────────────────────────
# ⚙️ PROFILE: UPDATE PROFILE DATA
# ─────────────────────────────────────────────────────────
@actor_routes.post('/api/actor/update_profile')
async def api_actor_update_profile(req):
    role, _ = await get_auth(req)
    if role != 'admin': return web.json_response({"error": "Unauthorized"}, status=403, dumps=fast_json)
    try:
        d = await req.post()
        actor_id, name, bio = d.get('actor_id'), d.get('name', '').strip(), d.get('bio', '').strip()
        category = d.get('category', 'actor').strip()
        if not actor_id or not name or not bio:
            return _actor_result(req, '/actors', 'Name and biography are required.')
        oid = ObjectId(actor_id)
        existing = await actors.find_one({"_id": oid})
        if not existing:
            return _actor_result(req, '/actors', 'Profile not found.', 404)
        updates = {"name": name, "bio": bio, "category": category,
                   "tags": [t.strip() for t in d.get('tags', '').strip().split(",") if t.strip()]}
        if 'links_present' in d:
            try:
                updates['profile_links'] = _parse_profile_links(d.getall('link_label', []), d.getall('link_url', []))
            except ValueError as exc:
                return _actor_result(req, f'/actor/{actor_id}', str(exc))
        else:
            # Old clients can still update the three original fields. Requests
            # that omit them must not erase any existing or new links.
            fields = {'insta': 'instagram', 'yt': 'youtube', 'twitter': 'twitter'}
            supplied = {key: d[field] for field, key in fields.items() if field in d}
            if supplied:
                legacy = dict(existing.get('social_links') or {})
                for key, value in supplied.items():
                    legacy[key] = _clean_link(value)
                updates['social_links'] = legacy
                if isinstance(existing.get('profile_links'), list):
                    links = _profile_links(existing)
                    for key, value in supplied.items():
                        label = _LEGACY_LINK_LABELS[key]
                        links = [link for link in links if link['label'].casefold() != label.casefold()]
                        if _clean_link(value):
                            links.append({'label': label, 'url': _clean_link(value)})
                    updates['profile_links'] = links
        result = await actors.update_one({"_id": oid}, {"$set": updates})
        if not result.matched_count:
            return _actor_result(req, '/actors', 'Profile not found.', 404)
        return _actor_result(req, f'/actor/{actor_id}?msg=Profile+updated+successfully!')
    except Exception as e:
        return _actor_result(req, '/actors', str(e) or 'Could not update the profile.', 500)

# ─────────────────────────────────────────────────────────
# ⚙️ PROFILE: UPDATE AVATAR
# ─────────────────────────────────────────────────────────
@actor_routes.post('/api/actor/update_avatar')
async def api_actor_update_avatar(req):
    role, _ = await get_auth(req)
    if role != 'admin': return web.json_response({"error": "Unauthorized"}, status=403, dumps=fast_json)
    try:
        data = await req.post()
        if not data.get("actor_id") or not data.get("photo"): return web.json_response({"success": False, "error": "Invalid assets data"}, dumps=fast_json)
            
        with io.BytesIO(data.get("photo").file.read()) as img_buffer:
            img_buffer.name = f"avatar_{data.get('actor_id')}_{int(time.time())}.jpg"
            # ✅ UPGRADE: पुराने मिक्स्ड 'BIN_CHANNEL' के बजाय पृथक 'ACTOR_STORAGE_CHANNEL' का उपयोग
            msg = await temp.BOT.send_photo(chat_id=ACTOR_STORAGE_CHANNEL, photo=img_buffer)
            
        if not msg or not msg.photo: return web.json_response({"success": False, "error": "Telegram upload failed"}, dumps=fast_json)
        tg_photo_id = msg.photo.sizes[-1].file_id if hasattr(msg.photo, "sizes") and msg.photo.sizes else msg.photo.file_id
        
        revision, updated_at = uuid.uuid4().hex, int(time.time())
        result = await actors.update_one({"_id": ObjectId(data.get("actor_id"))}, {"$set": {
            "photo_url": f"TG_ID:{tg_photo_id}", "is_actor_permanent": True,
            "photo_updated_at": updated_at, "photo_revision": revision}})
        if not result.matched_count:
            return web.json_response({"success": False, "error": "Profile not found"}, status=404, dumps=fast_json)
        return web.json_response({"success": True, "photo_updated_at": updated_at, "photo_revision": revision}, dumps=fast_json)
    except Exception as e: return web.json_response({"success": False, "error": str(e)}, dumps=fast_json)

# ─────────────────────────────────────────────────────────
# ⚙️ PROFILE: GALLERY UPLOAD
# ─────────────────────────────────────────────────────────
@actor_routes.post('/api/actor/gallery_upload')
async def api_actor_gallery_upload(req):
    role, _ = await get_auth(req)
    if role != 'admin': return web.json_response({"error": "Unauthorized"}, status=403, dumps=fast_json)
    try:
        reader = await req.multipart()
        actor_id, image_bytes_list = None, []
        while True:
            part = await reader.next()
            if part is None: break
            if part.name == 'actor_id':
                actor_id = (await part.read()).decode().strip()
            elif part.name == 'gallery_img':
                image_bytes = await part.read()
                if image_bytes:
                    # With the `multiple` input attribute the browser sends one
                    # multipart part per selected image, all with the same name.
                    image_bytes_list.append(image_bytes)
            
        if not actor_id or not image_bytes_list:
            return web.HTTPFound('/actors?err=Assets reading packet failure')

        # Upload each selected image and keep the resulting Telegram IDs in the
        # same order in which the user selected them.
        tg_photo_ids = []
        for image_number, image_bytes in enumerate(image_bytes_list, start=1):
            with io.BytesIO(image_bytes) as img_buffer:
                img_buffer.name = f"gallery_{actor_id}_{int(time.time())}_{image_number}.jpg"
                # ✅ UPGRADE: पुराने मिक्स्ड 'BIN_CHANNEL' के बजाय पृथक 'ACTOR_STORAGE_CHANNEL' का उपयोग
                msg = await temp.BOT.send_photo(chat_id=ACTOR_STORAGE_CHANNEL, photo=img_buffer)

            if not msg or not msg.photo:
                return web.HTTPFound(f'/actor/{actor_id}?err=Telegram Node Gallery Upload Failed ({image_number}/{len(image_bytes_list)})')
            tg_photo_id = msg.photo.sizes[-1].file_id if hasattr(msg.photo, "sizes") and msg.photo.sizes else msg.photo.file_id
            tg_photo_ids.append(f"TG_ID:{tg_photo_id}")
        
        # Add all uploaded images atomically so one multi-photo submission is
        # stored as one ordered batch instead of overwriting earlier images.
        await actors.update_one(
            {"_id": ObjectId(actor_id)},
            {"$push": {"gallery": {"$each": tg_photo_ids}}, "$set": {"is_gallery_permanent": True, "gallery_updated_at": int(time.time()), "gallery_revision": uuid.uuid4().hex}}
        )
        return web.HTTPFound(f'/actor/{actor_id}?msg={len(tg_photo_ids)} portrait(s) uploaded successfully to star gallery!')
    except Exception as e: return web.HTTPFound(f'/actors?err=System core crash: {str(e)}')

# ─────────────────────────────────────────────────────────
# ⚙️ PROFILE: GALLERY DELETE
# ─────────────────────────────────────────────────────────
@actor_routes.post('/api/actor/gallery_delete')
async def api_actor_gallery_delete(req):
    role, _ = await get_auth(req)
    if role != 'admin': return web.json_response({"error": "Unauthorized"}, status=403, dumps=fast_json)
    try:
        body = await req.json()
        actor_id, index = body.get("actor_id"), body.get("index")
        if not actor_id or index is None:
            return web.json_response({"success": False, "error": "Missing actor_id/index"}, dumps=fast_json)
        # The DB helper deletes one index using an atomic compare-and-set.
        ok = await delete_gallery_image_by_index(actor_id, int(index))
        if not ok:
            return web.json_response({"success": False, "error": "Profile or gallery changed. Refresh and try again."}, dumps=fast_json)
        return web.json_response({"success": True}, dumps=fast_json)
    except Exception as e: return web.json_response({"success": False, "error": str(e)}, dumps=fast_json)

# ─────────────────────────────────────────────────────────
# ⚙️ PROFILE: DELETE WHOLE PROFILE
# ─────────────────────────────────────────────────────────
@actor_routes.post('/api/actor/delete')
async def api_actor_delete(req):
    role, _ = await get_auth(req)
    if role != 'admin': return web.json_response({"error": "Unauthorized"}, status=403, dumps=fast_json)
    if not req.query.get("id"): return web.json_response({"error": "Missing ID"}, status=400, dumps=fast_json)
    try:
        # ✅ DUPLICATION FIX: database/ia_filterdb.py का delete_actor_profile()
        # पहले से मौजूद था, यहाँ दोबारा actors.delete_one() लिखने की जरूरत नहीं।
        ok = await delete_actor_profile(req.query.get("id"))
        if not ok: return web.json_response({"error": "Actor not found"}, status=404, dumps=fast_json)
        return web.json_response({"success": True}, dumps=fast_json)
    except Exception as e: return web.json_response({"error": str(e)}, status=500, dumps=fast_json)
