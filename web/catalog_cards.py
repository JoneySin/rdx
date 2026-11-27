"""Shared post and profile catalogue card markup for initial and search results."""
import html
from urllib.parse import quote
from web.post_editor import post_image_src


def render_catalog_card(item, kind, mode='poster'):
    ident = quote(str(item.get('_id', '')), safe='')
    if kind == 'actor':
        category = str(item.get('category') or 'actor')
        icon = {'actor': '🎭', 'app': '📱'}.get(category, '🌐')
        label = html.escape(category.capitalize())
        title = html.escape(str(item.get('name') or ''))
        revision = item.get('photo_revision') or int(item.get('photo_updated_at') or item.get('created_at') or 0)
        image = f'/api/actor/photo?id={ident}&v={quote(str(revision), safe="")}'
        path = 'actor'
    elif kind == 'post':
        label = html.escape(str(item.get('category') or 'Uncategorized'))
        title = html.escape(str(item.get('title') or 'Untitled'))
        image = html.escape(post_image_src(item.get('cover_image', '')), quote=True)
        icon, path = '🎬', 'post'
    else:
        raise ValueError('Unknown catalogue card kind')
    if kind == 'actor' and mode == 'text':
        return f'''<div class="act-text-card" style="background:var(--card); border:1px solid var(--border); padding:15px 18px; border-radius:14px; display:flex; justify-content:space-between; align-items:center; cursor:pointer; transition:0.2s;" onclick="window.location.href='/actor/{ident}'" onmouseover="this.style.borderColor='var(--accent-cyan)'" onmouseout="this.style.borderColor='var(--border)'"><div style="font-weight:800; color:var(--text); font-size:14px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:65%;">{title}</div><div style="background:var(--bg3); padding:5px 11px; border-radius:999px; font-size:11px; font-weight:800; color:var(--accent-cyan); white-space:nowrap; border:1px solid var(--border);">{icon} {label}</div></div>'''
    return f'''<div class="act-card card-enter" onclick="window.location.href='/{path}/{ident}'">
        <div class="poster-wrap" style="position:relative; padding-top:135%; background:var(--bg3); overflow:hidden;">
            <img src="{image}" class="act-poster" loading="lazy" decoding="async">
            <div style="position:absolute; top:9px; left:9px; background:var(--accent-grad); color:#fff; font-size:10px; padding:4px 9px; border-radius:7px; font-weight:800; backdrop-filter:blur(6px); z-index:2; text-transform:uppercase; letter-spacing:0.4px; box-shadow:0 4px 14px rgba(2,6,23,0.55); border:1px solid rgba(255,255,255,0.22);">{icon} {label}</div>
            <div style="position:absolute; bottom:0; left:0; right:0; background:linear-gradient(to top, rgba(5,9,20,0.96) 0%, rgba(5,9,20,0.72) 45%, transparent 100%); padding:32px 12px 13px 12px; z-index:2; text-align:center;"><div style="font-family:'Outfit','Plus Jakarta Sans',sans-serif; font-size:15px; font-weight:800; color:#fff; text-overflow:ellipsis; overflow:hidden; white-space:nowrap; text-shadow:0 2px 8px rgba(0,0,0,0.9); letter-spacing:0.3px;">{title}</div></div>
        </div>
        <div class="card-body"><div style="font-family:'Outfit','Plus Jakarta Sans',sans-serif; font-size:14.5px; font-weight:800; color:var(--text); text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">{title}</div><div style="font-size:11px; color:var(--accent-cyan); font-weight:700; margin-top:4px;">{icon} {label}</div></div>
    </div>'''
