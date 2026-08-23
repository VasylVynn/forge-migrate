#!/usr/bin/env python3
"""Generate ready-to-send wave-1 emails into ../forge-migrate-private/emails/ . A/B: first 15 -> no-offer probe, rest -> full pitch."""
import json, os, re, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIV = os.path.join(os.path.dirname(ROOT), 'forge-migrate-private')
rows = json.load(open(os.path.join(PRIV, 'outreach_list.json')))
CFG = json.load(open(os.path.join(ROOT, 'data', 'site_config.json')))
out = os.path.join(PRIV, 'emails'); os.makedirs(out, exist_ok=True)
# merge vendors sharing one inbox (Bilith x3)
byemail = collections.OrderedDict()
for r in rows:
    if r['wave'] != 1 or not r['email'] or r.get('no_cold_email'): continue
    byemail.setdefault(r['email'], []).append(r)
def fname(v): return re.sub(r'[^a-zA-Z0-9]+', '_', v)[:40]
probe_n = 0
for i, (email, group) in enumerate(byemail.items()):
    vendor = group[0]['vendor'].split(' (')[0]
    apps = [a for r in group for a in r['_apps']]
    apps.sort(key=lambda a: -a['installs'])
    total_inst = sum(a['installs'] for a in apps)
    variant = 'probe' if probe_n < 15 and len(apps) <= 3 else 'pitch'
    if variant == 'probe': probe_n += 1
    top = apps[0]
    lines = [f"TO: {email}", f"VENDOR: {vendor}  APPS: {len(apps)}  INSTALLS: {total_inst}  ENRICH: {'YES' if group[0].get('needs_founder_enrichment') else 'no'}", f"VARIANT: {variant}", ""]
    if variant == 'probe':
        lines += [f"SUBJECT: {top['name']} and the Forge deadline — one question", "",
f"Hi {vendor} team,", "",
f"Quick question from a fellow Marketplace developer: {top['name']} is still on Connect, and since March you can't ship updates to it. What's the #1 thing blocking the Forge migration for you — time, a missing Forge capability, or is it just not worth it for the app's revenue?", "",
"I'm asking because I migrate Connect apps full-time and I'm collecting the real blockers. If it's useful, I'll send back a free module-by-module migration map for your app either way.", "", "{sender}", CFG['url']]
    else:
        app_lines = []
        for a in apps[:4]:
            bits = f"{a['n_direct']} direct" + (f", {a['n_partial']} rework" if a['n_partial'] else "") + (f", {a['n_none']} no equivalent" if a['n_none'] else "")
            app_lines.append(f"• {a['name']} ({a['installs']} installs): {a['n_modules']} modules — {bits}. Map: {a['map_url']}")
        lines += [f"SUBJECT: Migration maps for your {len(apps)} Connect app{'s' if len(apps)>1 else ''} ({vendor})", "",
f"Hi {vendor} team,", "",
f"Your Connect apps haven't been able to ship updates since 31 March, and from 1 October Connect listings pay 25% revenue share — native Forge pays 0%. I generated module-by-module Forge migration maps from your public descriptors:", "",
*app_lines, "",
"Fixed prices, same app key (installs and reviews carry over):",
f"• Forge Wrap (Connect-on-Forge, backend stays): {top['wrap_price']}, 3 business days — credited in full against Native.",
f"• Forge Native (Runs on Atlassian eligible, 0% rev share): {top['native_price']} for {top['name']}; portfolio of 3+ apps −25%.", "",
"If you're already mid-migration, tell me where you're stuck instead — flat $490 per blocker.", "", "{sender}", CFG['url'], "", "—", "You're getting this one-time note because your app is publicly listed on the Atlassian Marketplace. Reply 'no' and I won't write again. {postal_address}"]
    open(os.path.join(out, f"w1_{i+1:02d}_{fname(vendor)}.txt"), 'w').write('\n'.join(lines))
print(f"emails generated: {len(byemail)} (probes {probe_n}) -> {out}")
