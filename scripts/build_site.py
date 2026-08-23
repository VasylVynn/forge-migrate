#!/usr/bin/env python3
"""Static site generator: landing, radar table, per-app readiness pages. No deps."""
import json, os, re, html, datetime, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'site'); DATA = os.path.join(ROOT, 'data')
CFG = json.load(open(os.path.join(DATA, 'site_config.json')))
EOS = datetime.date(2027, 1, 31); TODAY = datetime.date.today()
DAYS_LEFT = (EOS - TODAY).days
apps = [a for a in json.load(open(os.path.join(DATA, 'fast_apps.json'))) if a.get('status') == 'public']
connect = [a for a in apps if a.get('connect')]
maps = {}
mp = os.path.join(DATA, 'migration_maps.json')
if os.path.exists(mp): maps = json.load(open(mp))

def esc(s): return html.escape(str(s if s is not None else ''))
def slug(a): return re.sub(r'[^a-z0-9]+', '-', (a['name'] or a['key']).lower()).strip('-')[:60] + '-' + str(a['id'])
def fmt(n): return f"{n:,}" if isinstance(n, int) else esc(n)

def layout(title, body, desc='', canonical=''):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">{f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ''}
<link rel="stylesheet" href="{CFG['base']}/style.css"><link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔥</text></svg>">
</head><body><header class="top"><a class="brand" href="{CFG['base']}/">{esc(CFG['brand'])}</a><nav><a href="{CFG['base']}/radar/">Connect Radar</a><a href="{CFG['base']}/#pricing">Pricing</a><a href="{CFG['base']}/private-apps/">Private apps</a><a class="cta" href="{CFG['base']}/#contact">Get a migration map</a></nav></header>
<main>{body}</main>
<footer><p>{esc(CFG['brand'])} · Independent Atlassian Forge migration studio · Not affiliated with Atlassian. Data from the public Atlassian Marketplace API, refreshed {TODAY.isoformat()}.</p><p><a href="mailto:{esc(CFG['email'])}">{esc(CFG['email'])}</a> · <a href="{esc(CFG['github'])}">GitHub</a></p></footer></body></html>"""

def write(path, content):
    p = os.path.join(OUT, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w').write(content)

def badge(a):
    rd = a.get('release_date') or ''
    if rd < '2025-06-01': return '<span class="b red">Stale Connect</span>'
    return '<span class="b amber">Connect</span>'

def rev_share_line(a):
    if a.get('paymentModel') != 'atlassian': return ''
    return f"<p class=\"note\">Paid via Atlassian: after 1 Oct 2026 Connect listings pay <b>25% revenue share</b>; a native Forge version pays <b>0%</b> up to $1M lifetime.</p>"

def app_page(a):
    m = maps.get(a['key'])
    name = a['name']; inst = a.get('installs') or 0
    plan = ''
    if m:
        rows = ''.join(f"<tr><td><code>{esc(r['connect'])}</code>{' ×'+str(r['count']) if r.get('count',1)>1 else ''}</td><td>{esc(r['forge'])}</td><td><span class='b {r['status']}'>{esc(r['status'])}</span></td><td>{esc(r.get('note',''))}</td></tr>" for r in m['modules'])
        plan = f"""<h2>Migration map</h2><p>Generated from the app's public Connect descriptor ({m['module_count']} modules, {m['scope_count']} scopes{', remote backend at '+esc(m['base_host']) if m.get('base_host') else ''}).</p>
<table class="map"><thead><tr><th>Connect module</th><th>Forge equivalent</th><th>Status</th><th>Notes</th></tr></thead><tbody>{rows}</tbody></table>
<div class="est"><div><b>Forge Wrap</b> (Connect-on-Forge, keeps your remote)<br>{esc(m['wrap_days'])} · fixed <b>{esc(m['wrap_price'])}</b></div><div><b>Forge Native</b> (Runs on Atlassian, 0% rev share)<br>{esc(m['native_days'])} · from <b>{esc(m['native_price'])}</b></div></div>
{('<p class="warn">⚠ ' + esc(m['warnings']) + '</p>') if m.get('warnings') else ''}"""
    else:
        plan = f"""<h2>Migration map</h2><p>We generate a module-by-module map from the public Connect descriptor on request. <a href="mailto:{esc(CFG['email'])}?subject={esc('Migration map: '+name)}">Request the map for {esc(name)}</a> — free, no call needed.</p>"""
    body = f"""<article class="app"><p class="crumb"><a href="{CFG['base']}/radar/">Connect Radar</a> › {esc(a.get('vendor'))}</p>
<h1>{esc(name)}</h1><p class="meta">{badge(a)} · by {esc(a.get('vendor'))} · {fmt(inst)} installs · last release {esc(a.get('release_date') or 'unknown')} · {esc(a.get('paymentModel'))} · <a href="https://marketplace.atlassian.com{esc(a.get('listing_href','').split('?')[0])}" rel="nofollow">Marketplace listing</a></p>
<div class="countdown"><b>{DAYS_LEFT} days</b> until Atlassian Connect end of support (31 Jan 2027). This app is still built on Connect.</div>
<h2>What your customers already see</h2><p>Since 28 May 2026, Jira and Confluence admins see a warning banner on <i>Connected apps</i> for every app that still uses Connect modules, and Connect apps cannot ship updates. After 31 Jan 2027 Atlassian only addresses critical security issues in Connect.</p>
{rev_share_line(a)}
{plan}
<h2>Two ways forward</h2><ul><li><b>Forge Wrap</b> — Connect-on-Forge in 3 business days. Same app key, all installs and reviews preserved, your backend stays where it is. Unblocks updates.</li><li><b>Forge Native</b> — full rewrite on Forge (UI Kit / Custom UI, Forge storage). Eligible for <i>Runs on Atlassian</i> and the 0% revenue share.</li></ul>
<p class="cta-row"><a class="btn" href="mailto:{esc(CFG['email'])}?subject={esc('Migration: '+name)}">Talk about {esc(name)} →</a> <a class="btn ghost" href="{CFG['base']}/#pricing">See pricing</a></p>
<p class="small">Data from the public Atlassian Marketplace API. If you are the vendor and this is out of date, <a href="mailto:{esc(CFG['email'])}">tell us</a> and we'll fix it.</p></article>"""
    return layout(f"{name} — Connect → Forge migration readiness", body, f"{name} by {a.get('vendor')} still runs on Atlassian Connect ({inst:,} installs). Migration map, options and fixed prices.", f"{CFG['url']}/apps/{slug(a)}/")

def radar_page():
    rows = sorted(connect, key=lambda a: -(a.get('installs') or 0))
    trs = ''.join(f"<tr data-paid='{1 if a.get('paymentModel')=='atlassian' else 0}' data-stale='{1 if (a.get('release_date') or '')<'2025-06-01' else 0}'><td><a href='{CFG['base']}/apps/{slug(a)}/'>{esc(a['name'])}</a></td><td>{esc(a.get('vendor'))}</td><td class='n'>{fmt(a.get('installs') or 0)}</td><td>{esc(a.get('release_date') or '')}</td><td>{esc(a.get('paymentModel'))}</td><td>{esc(', '.join(a.get('apps') or []))}</td></tr>" for a in rows)
    paid = sum(1 for a in connect if a.get('paymentModel')=='atlassian'); stale = sum(1 for a in connect if (a.get('release_date') or '')<'2025-06-01')
    body = f"""<h1>Connect Radar</h1><p class="lead">{len(connect):,} of {len(apps):,} Atlassian cloud apps still run on Connect as of {TODAY.isoformat()}. {paid:,} are paid; {stale:,} have had no release since June 2025. <b>{DAYS_LEFT} days</b> to end of support.</p>
<div class="filters"><input id="q" placeholder="Filter by app or vendor…"><label><input type="checkbox" id="paid"> paid only</label><label><input type="checkbox" id="stale"> no release since Jun 2025</label><span id="count"></span></div>
<div class="tablewrap"><table id="t"><thead><tr><th>App</th><th>Vendor</th><th class="n">Installs</th><th>Last release</th><th>Payment</th><th>Product</th></tr></thead><tbody>{trs}</tbody></table></div>
<script>const q=document.getElementById('q'),p=document.getElementById('paid'),s=document.getElementById('stale'),rows=[...document.querySelectorAll('#t tbody tr')],c=document.getElementById('count');function f(){{const v=q.value.toLowerCase();let n=0;rows.forEach(r=>{{const ok=(!v||r.textContent.toLowerCase().includes(v))&&(!p.checked||r.dataset.paid==='1')&&(!s.checked||r.dataset.stale==='1');r.style.display=ok?'':'none';if(ok)n++}});c.textContent=n+' apps'}}[q,p,s].forEach(e=>e.addEventListener('input',f));f();</script>"""
    return layout("Connect Radar — every Atlassian app still on Connect", body, f"{len(connect)} Atlassian Marketplace apps still on Connect, with installs, last release and migration readiness.", f"{CFG['url']}/radar/")

def main():
    for d in ('apps', 'radar', 'private-apps'):
        shutil.rmtree(os.path.join(OUT, d), ignore_errors=True)
    write('radar/index.html', radar_page())
    for a in connect: write(f"apps/{slug(a)}/index.html", app_page(a))
    tpl = open(os.path.join(ROOT, 'site', 'templates', 'index.html')).read() if os.path.exists(os.path.join(ROOT,'site','templates','index.html')) else '<h1>TODO</h1>'
    write('index.html', layout(CFG['title'], tpl.replace('{{DAYS_LEFT}}', str(DAYS_LEFT)).replace('{{N_CONNECT}}', f"{len(connect):,}").replace('{{BASE}}', CFG['base']).replace('{{EMAIL}}', CFG['email']), CFG['description'], CFG['url']+'/'))
    pa = open(os.path.join(ROOT,'site','templates','private-apps.html')).read() if os.path.exists(os.path.join(ROOT,'site','templates','private-apps.html')) else '<h1>TODO</h1>'
    write('private-apps/index.html', layout("Private Connect apps: what to do before 31 Jan 2027", pa.replace('{{DAYS_LEFT}}', str(DAYS_LEFT)).replace('{{EMAIL}}', CFG['email']).replace('{{BASE}}', CFG['base']), "Your internal Connect app shows a LEGACY banner. Options, costs and timeline to move it to Forge.", CFG['url']+'/private-apps/'))
    # sitemap
    urls = [CFG['url']+'/', CFG['url']+'/radar/', CFG['url']+'/private-apps/'] + [f"{CFG['url']}/apps/{slug(a)}/" for a in connect]
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{esc(u)}</loc></url>' for u in urls) + '</urlset>')
    write('robots.txt', f"User-agent: *\nAllow: /\nSitemap: {CFG['url']}/sitemap.xml\n")
    print(f"built: {len(connect)} app pages, radar, index, private-apps")
if __name__ == '__main__': main()
