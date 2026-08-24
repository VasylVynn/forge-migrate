#!/usr/bin/env python3
"""Fetch Marketplace reviews for apps in candidate + leader slots -> data/reviews.jsonl"""
import json, os, sys, time, random, urllib.request, urllib.error, concurrent.futures as cf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (market research; github VasylVynn)", "Accept": "application/json"}
apps = [a for a in json.load(open(os.path.join(ROOT,'data','fast_apps.json'))) if a.get('status')=='public']
SLOTS = {
 'read-confirm': ['read and understood','read confirmation','acknowledg','read receipt'],
 'cql-search': ['cql','advanced search'],
 'recurring': ['recurring'],
 'epic-rollup': ['epic sum','roll up','rollup','epic progress'],
 'glossary': ['glossary','terms','definition'],
 'orgchart': ['org chart','orgchart','organization chart','people directory'],
 'restore': ['restore deleted','who deleted'],
 'lms': ['course','lms','quiz','training'],
 'footnotes': ['footnote','citation'],
 'decision': ['decision log','decision register','decisions'],
 'toc-headings': ['table of contents','numbered heading','easy heading'],
 'countdown-status': ['countdown','status macro','banner'],
 'ai-apps': ['ai assistant','ai for jira','ai for confluence','acceptance criteria','user story generator','release notes'],
}
def get(url, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(2*(i+1)+random.random())
        except Exception: time.sleep(1.5*(i+1))
    return None
targets = []
for a in apps:
    nm = a['name'].lower()
    for slot, kws in SLOTS.items():
        if any(k in nm for k in kws) and (a.get('installs') or 0) >= 50 and (a.get('reviews') or 0) >= 2:
            targets.append({'slot': slot, **{k: a[k] for k in ('key','name','vendor','installs','connect','paymentModel','release_date')}, 'nrev': a.get('reviews')})
            break
print(f"targets {len(targets)}", file=sys.stderr)
OUT = os.path.join(ROOT,'data','reviews.jsonl')
done=set()
if os.path.exists(OUT):
    for l in open(OUT): done.add(json.loads(l)['key'])
def one(t):
    if t['key'] in done: return None
    revs=[]; off=0
    while off < min(t['nrev'], 60):
        d = get(f"https://marketplace.atlassian.com/rest/2/addons/{t['key']}/reviews?limit=25&offset={off}&sort=recent")
        if not d: break
        batch = d.get('_embedded',{}).get('reviews',[])
        if not batch: break
        for r in batch:
            revs.append({'stars': r.get('stars'), 'date': r.get('date'), 'text': (r.get('review') or '')[:600]})
        off += len(batch)
    return {**t, 'reviews': revs}
with open(OUT,'a') as f, cf.ThreadPoolExecutor(max_workers=6) as ex:
    n=0
    for row in ex.map(one, targets):
        if row is None: continue
        f.write(json.dumps(row)+'\n'); f.flush(); n+=1
        if n % 10 == 0: print(n, file=sys.stderr, flush=True)
print("DONE", file=sys.stderr)
