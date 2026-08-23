#!/usr/bin/env python3
"""Build a per-app Migration Map from Connect descriptors → data/migration_maps.json (+ markdown in data/maps_md/)."""
import json, os, re, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
M = json.load(open(os.path.join(DATA, 'connect_forge_mapping.json')))
apps = {a['key']: a for a in json.load(open(os.path.join(DATA, 'fast_apps.json')))}

JIRA_ITEM_LOC = {'system.top.navigation.bar': 'jira:globalPage', 'admin_plugins_menu': 'jira:adminPage', 'atl.jira.proj.config': 'jira:projectSettingsPage',
  'jira.issue.tools': 'jira:issueAction', 'operations-operations': 'jira:issueAction', 'operations-top-level': 'jira:issueAction', 'operations-work': 'jira:issueAction',
  'operations-attachments': 'jira:issueAction', 'opsbar-operations': 'jira:issueAction', 'operations-subtasks': 'jira:issueAction', 'jira.project.sidebar.plugins.navigation': 'jira:projectPage',
  'jira.project.sidebar.navigation': 'jira:projectPage', 'jira.agile.board.tools': 'jira:boardAction (preview)', 'jira.software.board.tools': 'jira:boardAction (preview)',
  'jira.software.backlog.tools': 'jira:backlogAction (preview)', 'sprint-move-actions': 'jira:sprintAction', 'sprint-delete-action': 'jira:sprintAction', 'jira.navigator.pluggable.items': 'jira:issueNavigatorAction (preview)',
  'system.user.options/personal': 'jira:personalSettingsPage (preview)', 'servicedesk.agent.queues': 'jiraServiceManagement:queuePage', 'top_system_section': 'jira:adminPage', 'top_plugins_section': 'jira:adminPage', 'admin_system_menu': 'jira:adminPage'}
JIRA_ITEM_NONE = {'opsbar-transitions', 'transitions-all', 'gadgets.dashboard.menu', 'system.preset.filters', 'view.issue.opsbar', 'board-links', 'topnavbar-menu', 'greenhopper_menu', 'find_link', 'browse_link', 'jira.global.board.sidebar.navigation'}
CONF_ITEM_LOC = {'system.header/left': 'confluence:globalPage', 'system.top.navigation.bar': 'confluence:globalPage', 'system.admin': 'confluence:globalSettings', 'system.admin/configuration': 'confluence:globalSettings', 'system.admin/administration': 'confluence:globalSettings',
  'system.content.action': 'confluence:contentAction', 'system.content.action/secondary': 'confluence:contentAction', 'system.content.action/primary': 'confluence:contentAction', 'system.content.action/modify': 'confluence:contentAction', 'system.content.action/marker': 'confluence:contentAction',
  'system.space.sidebar/main-links': 'confluence:spacePage', 'system.space.tools/contenttools': 'confluence:spaceSettings', 'system.space.tools/overview': 'confluence:spaceSettings', 'system.space.tools/integrations': 'confluence:spaceSettings', 'page.view.selection/action-panel': 'confluence:contextMenu'}
CONF_ITEM_NONE = {'system.content.button', 'page.metadata.banner', 'system.editor.precursor.buttons', 'system.content.metadata', 'atl.page.metadata.banner', 'atl.dashboard.secondary', 'atl.editor.savebar', 'admin_plugins_menu', 'system.user.options/personal', 'top_system_section/user_interface'}
JIRA_PANEL_LOC = {'atl.jira.view.issue.left.context': 'jira:issuePanel', 'atl.jira.view.issue.right.context': 'jira:issueGlance', 'atl.gh.issue.details.tab': 'jira:issuePanel'}
CONF_PANEL_LOC = {'atl.footer': 'confluence:backgroundScript', 'atl.general': 'confluence:pageBanner'}
CONF_EVENTS_NONE = {'user_created', 'user_removed', 'group_created', 'group_removed', 'relation_created', 'relation_deleted', 'search_performed', 'user_updated', 'blueprint_page_created', 'user_reactivated', 'space_logo_updated', 'user_followed', 'theme_enabled', 'user_deactivated', 'theme_updated'}
JIRA_EVENTS_NONE = {'issue_property_set', 'issue_property_deleted'}

def product_of(row, d):
    a = [x for x in (row.get('apps') or []) if x]
    if a: return 'confluence' if 'confluence' in a else 'jira'
    mods = set((d.get('modules') or {}).keys())
    return 'confluence' if mods & {'dynamicContentMacros', 'staticContentMacros', 'customContent', 'spaceToolsTabs', 'blueprints', 'contentBylineItems', 'confluenceContentProperties'} else 'jira'

def classify(row):
    d = row['descriptor']; prod = product_of(row, d); tbl = M[prod]
    mods = d.get('modules') or {}; out = []; days = 1.0  # manifest/scaffold/test baseline
    warnings = []; none_count = 0; partial_count = 0; n_instances = 0
    def add(connect, forge, status, note, dcount, count=1, billable=True):
        nonlocal days, none_count, partial_count, n_instances
        out.append({'connect': connect, 'forge': forge, 'status': status, 'note': note, 'count': count})
        if billable: n_instances += count
        if status == 'none': none_count += count
        elif status in ('partial', 'preview'): partial_count += count
        days += dcount * (1 + 0.5 * (count - 1))
    for k, v in mods.items():
        items = v if isinstance(v, list) else [v]
        cnt = len(items)
        if k in ('webItems', 'webSections'):
            locs = collections.Counter((it.get('location') or '?') for it in items)
            for loc, c in locs.items():
                base = loc.split('/')[0]
                table = JIRA_ITEM_LOC if prod == 'jira' else CONF_ITEM_LOC
                nonet = JIRA_ITEM_NONE if prod == 'jira' else CONF_ITEM_NONE
                target = table.get(loc) or table.get(base)
                if target: add(f"{k} @ {loc}", target, 'preview' if 'preview' in target else 'direct', '', 0.5 if k == 'webItems' else 0.25, c)
                elif loc in nonet or base in nonet: add(f"{k} @ {loc}", 'no equivalent', 'none', 'location not planned in Forge — relocate to a supported page/action', 0.75, c)
                else: add(f"{k} @ {loc}", 'by location (review)', 'partial', 'location needs manual mapping', 0.5, c)
            continue
        if k == 'webPanels':
            locs = collections.Counter((it.get('location') or '?') for it in items)
            for loc, c in locs.items():
                table = JIRA_PANEL_LOC if prod == 'jira' else CONF_PANEL_LOC
                target = table.get(loc)
                if target: add(f"webPanels @ {loc}", target, 'direct', '', 1.0, c)
                else: add(f"webPanels @ {loc}", 'by location (review)', 'partial', 'panel location needs manual mapping', 1.0, c)
            continue
        if k == 'webhooks':
            evs = [it.get('event') for it in items]
            bad = [e for e in evs if e in (JIRA_EVENTS_NONE if prod == 'jira' else CONF_EVENTS_NONE)]
            add(f"webhooks ({cnt} event{'s' if cnt!=1 else ''})", 'trigger → avi:* product events', 'partial' if bad else 'direct', (f"no Forge event for: {', '.join(bad)}" if bad else ''), min(0.3 + 0.1 * cnt, 1.5), 1)
            continue
        spec = tbl.get(k)
        if spec: add(k, spec['forge'], spec['status'], spec.get('note', ''), spec['days'], cnt)
        else: add(k, 'unknown module (review)', 'partial', 'not in Atlassian equivalence table', 1.0, cnt)
    lc = d.get('lifecycle') or {}
    if lc.get('installed'): add('lifecycle.installed', 'avi:forge:installed:app trigger + Forge storage', 'direct', 'enabled/disabled no longer sent', 0.5, billable=False)
    if lc.get('uninstalled'): add('lifecycle.uninstalled', 'no equivalent (FRGE-1246)', 'none', 'cleanup must run on next install or via scheduled job', 0.25, billable=False)
    scopes = row.get('scopes') or d.get('scopes') or []
    if 'ACT_AS_USER' in scopes: warnings.append('ACT_AS_USER (user impersonation) → Forge asUser()/asApp() with OAuth scopes; offline user actions need Forge Remote or asApp')
    if prod == 'confluence' and any(m in mods for m in ('dynamicContentMacros', 'staticContentMacros')): warnings.append('Macros cannot render in the legacy editor after migration; nested bodied macros and macro parameters via URL are not supported')
    if 'jiraIssueFields' in mods: warnings.append('Issue field values are NOT retained on migration — a value migration script is required')
    gaps = [r['connect'] for r in out if r['status'] == 'none']
    if gaps: warnings.append('No direct Forge equivalent for: ' + ', '.join(gaps) + ' (see notes)')
    base_host = re.sub(r'^https?://', '', d.get('baseUrl') or '').split('/')[0]
    n = n_instances
    native_days = days + (2 if lc.get('installed') else 1)  # backend/state port baseline
    wrap_days = 1 if n <= 6 else 2
    native_price = 4900 if n <= 3 else (9900 if n <= 8 else None)
    return {'product': prod, 'modules': out, 'module_count': n, 'scope_count': len(scopes), 'scopes': scopes, 'base_host': base_host,
            'wrap_days': f"{wrap_days} build day{'s' if wrap_days>1 else ''}, delivered within 3 business days", 'wrap_price': '$1,200' if n <= 8 else '$1,800',
            'native_days': f"{int(round(native_days))}–{int(round(native_days*1.6))} engineering days", 'native_price': f"${native_price:,}" if native_price else f"~${int(round(native_days*1.3*700/100))*100:,} (quote)",
            'warnings': ' · '.join(warnings), 'none_count': none_count, 'partial_count': partial_count}

def md(row, m):
    a = apps.get(row['key'], {}); name = a.get('name', row['key'])
    lines = [f"# Migration map — {name}", f"Vendor: {a.get('vendor')} · {a.get('installs') or 0:,} installs · last release {a.get('release_date')} · {m['product']}", '',
             f"Source: public Connect descriptor ({m['module_count']} module instances, scopes: {', '.join(m['scopes']) or '—'}{', backend: ' + m['base_host'] if m['base_host'] else ''})", '',
             '| Connect | Forge | Status | Note |', '|---|---|---|---|']
    for r in m['modules']: lines.append(f"| {r['connect']}{' ×'+str(r['count']) if r['count']>1 else ''} | {r['forge']} | {r['status']} | {r.get('note','')} |")
    lines += ['', f"**Forge Wrap** (Connect-on-Forge, backend stays): {m['wrap_days']} — fixed {m['wrap_price']}", f"**Forge Native** (Runs on Atlassian eligible, 0% rev share): {m['native_days']} — {m['native_price']}"]
    if m['warnings']: lines += ['', f"⚠ {m['warnings']}"]
    return '\n'.join(lines)

def main():
    maps = {}; os.makedirs(os.path.join(DATA, 'maps_md'), exist_ok=True)
    path = os.path.join(DATA, 'descriptors.jsonl')
    n = 0
    for l in open(path):
        row = json.loads(l)
        if 'descriptor' not in row: continue
        try: m = classify(row)
        except Exception as e: print('ERR', row['key'], e); continue
        maps[row['key']] = m; n += 1
        open(os.path.join(DATA, 'maps_md', re.sub(r'[^a-zA-Z0-9._-]', '_', row['key']) + '.md'), 'w').write(md(row, m))
    json.dump(maps, open(os.path.join(DATA, 'migration_maps.json'), 'w'))
    print(f"maps: {n}")
if __name__ == '__main__': main()
