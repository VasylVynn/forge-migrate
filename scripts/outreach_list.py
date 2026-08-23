#!/usr/bin/env python3
"""Merge targets + contacts + migration maps → private outreach list (CSV + JSON), grouped by vendor."""
import json, csv, os, re, collections, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIV = os.path.join(os.path.dirname(ROOT), 'forge-migrate-private')
CFG = json.load(open(os.path.join(ROOT, 'data', 'site_config.json')))
contacts_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PRIV, 'contacts.jsonl')
maps = json.load(open(os.path.join(ROOT, 'data', 'migration_maps.json')))
apps = {a['key']: a for a in json.load(open(os.path.join(ROOT, 'data', 'fast_apps.json')))}
contacts = {}
for l in open(contacts_path):
    r = json.loads(l); contacts[r['key']] = r
def slug(a): return re.sub(r'[^a-z0-9]+', '-', (a['name'] or a['key']).lower()).strip('-')[:60] + '-' + str(a['id'])
byv = collections.defaultdict(list)
for key, c in contacts.items():
    a = apps.get(key); 
    if not a: continue
    m = maps.get(key)
    byv[a['vendor']].append({'key': key, 'name': a['name'], 'installs': a.get('installs') or 0, 'release': a.get('release_date'), 'email': c.get('email'), 'tier': c.get('tier'), 'website': c.get('website'),
        'map_url': f"{CFG['url']}/apps/{slug(a)}/", 'n_modules': (sum(r['count'] for r in m['modules']) if m else None),
        'n_direct': sum(r['count'] for r in m['modules'] if r['status']=='direct') if m else None,
        'n_partial': sum(r['count'] for r in m['modules'] if r['status'] in ('partial','preview')) if m else None,
        'n_none': sum(r['count'] for r in m['modules'] if r['status']=='none') if m else None,
        'wrap_price': m['wrap_price'] if m else None, 'native_price': m['native_price'] if m else None, 'top_warning': (m['warnings'].split(' · ')[0] if m and m['warnings'] else 'Connect-on-Forge keeps your remote but stays on the 25% Connect revenue share; only native Forge modules qualify for 0%.')})
rows = []
SKIP = {'Apps+'}
NO_COLD = ('.de', '.at', '.pl')  # UWG/GDPR: no cold email, use LinkedIn/community
KNOWN_DE = {'Seibert', 'Aura Apps (Seibert - appanvil)', 'Actonic', 'catworkx', 'resolution', 'CraftCoders', 'KontextWork', 'APTIS', 'Ease Solutions', 'MOEWE', 'UGUBI', 'Softlist', 'weweave'}
for vendor, lst in byv.items():
    if any(k.lower() in (vendor or '').lower() for k in ('apps+', 'seibert', 'glintech', 'valiantys')): continue
    lst.sort(key=lambda x: -x['installs'])
    emails = [x['email'] for x in lst if x['email']]
    tier = next((x['tier'] for x in lst if x['tier']), None)
    alive = any((x['release'] or '') >= '2025-06-01' for x in lst)
    inst = sum(x['installs'] for x in lst)
    # priority: small vendors first (no tier / silver), alive, installs
    score = (0 if tier in (None, 'SILVER') else 1, 0 if alive else 1, -inst)
    email = emails[0] if emails else ''
    dom = email.split('@')[-1] if email else ''
    website = next((x['website'] for x in lst if x.get('website')), '') or ''
    no_cold = any((dom.endswith(t) or (website and re.search(r'\.' + t.lstrip('.') + r'(/|$)', website))) for t in NO_COLD) or any(k.lower() in (vendor or '').lower() for k in KNOWN_DE) or bool(re.search(r'\b(gmbh|sp\.? ?z ?o\.?o\.?|s\.r\.o\.|ug\b)', (vendor or ''), re.I))
    service_desk = dom.endswith('atlassian.net')
    connect_bound = all(True for x in lst)  # placeholder, refined below
    rows.append({'vendor': vendor, 'email': email, 'tier': tier or '', 'alive': alive, 'apps': len(lst), 'installs': inst, 'top_app': lst[0]['name'], 'no_cold_email': no_cold, 'needs_founder_enrichment': service_desk, 'maps': ' | '.join(x['map_url'] for x in lst[:4]), 'wave': '', '_apps': lst, '_score': score})
rows.sort(key=lambda r: r['_score'])
for i, r in enumerate(rows): r['wave'] = 1 if i < 40 else (2 if i < 80 else 3)
os.makedirs(PRIV, exist_ok=True)
with open(os.path.join(PRIV, 'outreach_list.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['wave', 'vendor', 'email', 'tier', 'alive', 'apps', 'installs', 'top_app', 'no_cold_email', 'needs_founder_enrichment', 'maps']); w.writeheader()
    for r in rows: w.writerow({k: r[k] for k in w.fieldnames})
json.dump(rows, open(os.path.join(PRIV, 'outreach_list.json'), 'w'), default=str)
print(f"vendors {len(rows)} | with email {sum(1 for r in rows if r['email'])} | wave1 {sum(1 for r in rows if r['wave']==1)} | no-tier/silver {sum(1 for r in rows if r['tier'] in ('','SILVER'))} | alive {sum(1 for r in rows if r['alive'])}")
for r in rows[:12]: print(f"  w{r['wave']} {r['vendor'][:28]:<28} {r['tier'] or '-':<8} apps={r['apps']:<3} inst={r['installs']:<6} {r['email'] or 'NO EMAIL'}")
