"""The unified RdxTv brand identity, shared across every web surface."""

BRAND_MARKUP = '''<span class="brand-mark" aria-hidden="true">R</span><span class="brand-word">Rdx<span class="brand-tv">Tv</span></span>'''

# Signature RdxTv squircle prism badge + geometric dual-tone wordmark, kept in
# one place so dashboard, sidebar, landing, watch page and mini app stay unified.
BRAND_CSS = """
.brand-mark{display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;background:linear-gradient(135deg,#6366f1 0%,#06b6d4 100%);color:#fff;padding:3px 8px;border-radius:8px;font-family:'Outfit','Plus Jakarta Sans',sans-serif;font-size:18px;font-weight:900;line-height:1;letter-spacing:0;box-shadow:0 4px 14px rgba(6,182,212,.32),inset 0 1px 0 rgba(255,255,255,.28)}
.brand-word{color:inherit;font-family:'Outfit','Plus Jakarta Sans',sans-serif;font-size:inherit;font-weight:900;letter-spacing:.4px;white-space:nowrap;text-transform:none}
.brand-tv{color:#06b6d4;margin-left:1px}
.light .brand-tv,html.light .brand-tv{color:#0284c7}
.guest-brand{font-size:24px!important}
.guest-brand .brand-mark{font-size:22px;border-radius:10px;padding:4px 9px}
.sb-logo .brand-mark{font-size:16px;padding:3px 7px;border-radius:7px}
.tb .brand-mark{font-size:15px;line-height:1.2;padding:2px 7px;border-radius:7px}
.landing-brand .brand-mark{font-size:22px;padding:4px 10px;border-radius:10px}
.watch-brand .brand-mark{font-size:22px;padding:4px 9px;border-radius:10px}
@media(max-width:768px){.watch-brand .brand-mark{font-size:18px;padding:3px 7px;border-radius:8px}}
@media(max-width:600px){.landing-brand .brand-mark{font-size:18px;padding:3px 8px;border-radius:8px}}
@media(max-width:400px){
  .topbar{gap:6px;padding:0 10px}
  .topbar .theme-btn{padding:6px 9px;white-space:nowrap}
  .landing-brand + .header-actions{gap:6px}
  .landing-brand + .header-actions .theme-btn,.landing-brand + .header-actions .admin-btn{padding:6px 10px}
}
"""
