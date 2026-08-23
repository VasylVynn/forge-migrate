import json,urllib.request,time,sys,concurrent.futures as cf
UA={"User-Agent":"Mozilla/5.0 (connect-eos-radar; github VasylVynn)","Accept":"application/json"}
def page(off):
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(f"https://marketplace.atlassian.com/rest/2/addons?hosting=cloud&limit=50&offset={off}&withVersion=true",headers=UA),timeout=60) as r: return json.load(r)['_embedded'].get('addons',[])
        except Exception as e: time.sleep(2*(i+1))
    return []
out=[]
with cf.ThreadPoolExecutor(max_workers=6) as ex:
    for batch in ex.map(page, range(0,6100,50)):
        for a in batch:
            e=a.get('_embedded',{}); v=e.get('version') or {}
            out.append({'key':a.get('key'),'id':a.get('id'),'name':a.get('name'),'status':a.get('status'),'vendor':e.get('vendor',{}).get('name'),
              'vendor_href':e.get('vendor',{}).get('_links',{}).get('alternate',{}).get('href'),'categories':[c.get('name') for c in e.get('categories',[])],
              'installs':e.get('distribution',{}).get('totalInstalls'),'stars':e.get('reviews',{}).get('averageStars'),'reviews':e.get('reviews',{}).get('count'),
              'lastModified':e.get('lastModified'),'listing_href':a.get('_links',{}).get('alternate',{}).get('href'),
              'connect':(v.get('deployment') or {}).get('connect'),'paymentModel':v.get('paymentModel'),'license':((v.get('_embedded') or {}).get('license') or {}).get('key'),
              'release_date':(v.get('release') or {}).get('date'),'version':v.get('name'),'apps':[c.get('application') for c in v.get('compatibilities',[])],'summary':(a.get('summary') or '')[:200]})
seen=set(); uniq=[]
for r in out:
    if r['key'] in seen: continue
    seen.add(r['key']); uniq.append(r)
json.dump(uniq,open('fast_apps.json','w'))
c=[r for r in uniq if r['connect']]; print("total",len(uniq),"connect",len(c),"paid-connect",sum(1 for r in c if r['paymentModel']=='atlassian'))
