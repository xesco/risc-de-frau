#!/usr/bin/env bash
# fetch.sh — Fetches contract data from contractes.cat and saves to data.json
# Requires: @gerardgimenezadsuar/contractes-cli (npm install -g @gerardgimenezadsuar/contractes-cli)

set -euo pipefail

YEAR=${1:-2025}
PAGES=${2:-20}
OUT="data.json"

echo "Fetching ${PAGES} pages of contracts for year ${YEAR}..."

python3 -c "
import subprocess, json, sys

year = '$YEAR'
pages = int('$PAGES')
contracts = []

for page in range(1, pages + 1):
    print(f'  Page {page}/{pages}...', flush=True)
    result = subprocess.run(
        ['contractes', 'search-contracts', '--year', year, '--sort', 'amount-desc', '--page', str(page), '--raw'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f'  Warning: page {page} failed — {result.stderr.strip()}', file=sys.stderr)
        continue
    try:
        data = json.loads(result.stdout)
        contracts.extend(data.get('data', []))
    except json.JSONDecodeError as e:
        print(f'  Warning: could not parse page {page} — {e}', file=sys.stderr)

print(f'Fetched {len(contracts)} contracts.')
with open('$OUT', 'w') as f:
    json.dump(contracts, f, ensure_ascii=False)
print(f'Saved to $OUT')
"

echo "Done."
