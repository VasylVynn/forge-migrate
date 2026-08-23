# forge-migrate

Connect Radar + Migration Map generator for Atlassian Marketplace apps still built on Atlassian Connect (end of support: 31 Jan 2027).

- `scripts/scan_fast.py` — pulls the full cloud catalog from the public Marketplace REST API (`withVersion=true`).
- `scripts/fetch_descriptors.py` — downloads each Connect app's `atlassian-connect.json` as hosted by the Marketplace.
- `scripts/migration_map.py` — maps Connect modules to Forge modules using Atlassian's published equivalence tables (`data/connect_forge_mapping.json`) and estimates effort.
- `scripts/build_site.py` — renders the static site in `site/`.

Data comes from public Atlassian endpoints; not affiliated with Atlassian.
