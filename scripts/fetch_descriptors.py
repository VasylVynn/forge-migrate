#!/usr/bin/env python3
"""Fetch the Marketplace-hosted Connect descriptor for every Connect app → data/descriptors.jsonl (resumable)."""
import json, os, sys, time, random, urllib.request, urllib.error, concurrent.futures as cf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (forge-migrate radar; github VasylVynn)", "Accept": "application/json"}
OUT = os.path.join(ROOT, 'data', 'descriptors.jsonl')
def get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(3 * (i + 1) + random.random())
        except Exception:
            time.sleep(2 * (i + 1))
    return None
def one(a):
    row = {'key': a['key'], 'id': a['id']}
    v = get(f"https://marketplace.atlassian.com/rest/2/addons/{a['key']}/versions/latest?hosting=cloud")
    try: v = json.loads(v) if v else None
    except Exception: v = None
    if not v: row['err'] = 'version'; return row
    art = (v.get('_embedded') or {}).get('artifact') or {}
    links = art.get('_links') or {}
    row['remote_descriptor'] = (links.get('remote') or {}).get('href')
    row['scopes'] = [p.get('key') for p in (v.get('deployment') or {}).get('permissions', [])]
    row['apps'] = [c.get('application') for c in v.get('compatibilities', [])]
    row['build'] = v.get('buildNumber')
    binary = (links.get('binary') or {}).get('href')
    d = get(f"https://marketplace.atlassian.com/download/apps/{a['id']}/version/{v.get('buildNumber')}/descriptor") if v.get('buildNumber') else (get(binary) if binary else None)
    try: d = json.loads(d) if d else None
    except Exception: d = None
    if not d: row['err'] = 'descriptor'; return row
    row['descriptor'] = d
    return row
def main():
    apps = [a for a in json.load(open(os.path.join(ROOT, 'data', 'fast_apps.json'))) if a.get('connect') and a.get('status') == 'public']
    done = set()
    if os.path.exists(OUT):
        for l in open(OUT):
            try: done.add(json.loads(l)['key'])
            except Exception: pass
    todo = [a for a in apps if a['key'] not in done]
    todo.sort(key=lambda a: -(a.get('installs') or 0))
    print(f"todo {len(todo)} done {len(done)}", file=sys.stderr, flush=True)
    with open(OUT, 'a') as f, cf.ThreadPoolExecutor(max_workers=4) as ex:
        for i, row in enumerate(ex.map(one, todo)):
            f.write(json.dumps(row) + '\n'); f.flush()
            if i % 50 == 0: print(i, file=sys.stderr, flush=True)
    print('DONE', file=sys.stderr)
if __name__ == '__main__': main()
