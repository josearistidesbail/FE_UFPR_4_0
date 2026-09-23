#!/usr/bin/env python3
"""S12: re-verify every LCSC line of the BOM against live JLCSearch (stock / price / Basic-Preferred).

Usage:
  kicad-cli sch export bom --fields 'Reference,Value,Footprint,LCSC,${QUANTITY}' \
      --labels 'Reference,Value,Footprint,LCSC,Qty' --group-by 'Value,Footprint,LCSC' -o SCRATCH/bom.csv FE_UFPR_4_0.kicad_sch
  python3 tools/fab/jlc_verify.py SCRATCH/bom.csv [--boards 5] [--out SCRATCH/jlc_verify.json] [--md SCRATCH/jlc_verify.md]

Flags per line: NOT_FOUND, OUT_OF_STOCK, LOW_STOCK (< boards x qty x 3), EXTENDED (feeder fee),
PACKAGE_MISMATCH (JLC package string vs the KiCad footprint size), VALUE_MISMATCH (R/C value vs JLC's description).  Placeholders (NOFIT, CONSIGNED) are
listed, not queried.  JLCSearch is a snapshot mirror - treat stock as indicative (TOOLING_NOTES.md).
"""
import csv, json, re, subprocess, sys, time

SRC = sys.argv[1]
BOARDS = int(sys.argv[sys.argv.index('--boards') + 1]) if '--boards' in sys.argv else 5
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
MD = sys.argv[sys.argv.index('--md') + 1] if '--md' in sys.argv else None
API = 'https://jlcsearch.tscircuit.com/api/search?q={}&limit=5'

def fetch(code):
    """curl, not urllib: JLCSearch answers urllib's default User-Agent with HTTP 403 (2026-09-23)"""
    err = None
    for attempt in range(3):
        try:
            out = subprocess.run(['curl', '-s', '-m', '20', API.format(code)], capture_output=True, text=True, timeout=25).stdout
            d = json.loads(out)
            for c in d.get('components', []):
                if str(c.get('lcsc')) == code[1:]: return c
            # /api/search does not index every part (C25804, the 10k 0603, is missing): the resistors
            # endpoint honours ?lcsc= (the capacitors one ignores it and returns unrelated rows)
            out = subprocess.run(['curl', '-s', '-m', '20', f'https://jlcsearch.tscircuit.com/resistors/list.json?lcsc={code[1:]}&limit=1'], capture_output=True, text=True, timeout=25).stdout
            for c in json.loads(out).get('resistors', []):
                if str(c.get('lcsc')) == code[1:]:
                    return {'lcsc': c['lcsc'], 'mfr': c.get('mfr'), 'package': c.get('package'), 'stock': c.get('stock'), 'price': c.get('price1'), 'is_basic': c.get('is_basic'), 'is_preferred': c.get('is_preferred'), 'description': f"resistors endpoint: {c.get('resistance')} ohm {c.get('tolerance_fraction')}"}
            return None
        except Exception as e:
            err = e; time.sleep(2)
    return {'error': str(err)}

_MULT = {'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'm': 1e-3, 'k': 1e3, 'M': 1e6, 'R': 1, '': 1}
def bom_value(v):
    """'1M' / '4.7k' / '47.0R 0.1%' / '0R' -> ohms; '2.2nF C0G' / '10uF 25V' -> farads; else None"""
    m = re.match(r'\s*([\d.]+)\s*([pnum]?)F\b', v)
    if m: return ('F', float(m[1]) * _MULT[m[2]])
    m = re.match(r'\s*([\d.]+)\s*([kMR]?)(?:\s|$|\s*[Ω%])', v)
    if m and not re.search(r'[VA]\b', v.split()[0]): return ('R', float(m[1]) * _MULT[m[2]])
    return None
def jlc_value(descr):
    """first '4.7kΩ' / '1MΩ' / '2.2nF' token of JLC's description"""
    m = re.search(r'(?<![\w.])([\d.]+)([kM]?)Ω', descr)
    if m: return ('R', float(m[1]) * _MULT[m[2]])
    m = re.search(r'(?<![\w.])([\d.]+)([pnum])F\b', descr)
    if m: return ('F', float(m[1]) * _MULT[m[2]])
    return None

def fp_size(footprint):
    m = re.search(r'_(0402|0603|0805|1206|1210|2010|2512|2410)_', footprint)
    if m: return m.group(1)
    for k in ('SOIC-8', 'SOT-23-6', 'SOT-23', 'SOT-223', 'SOT-583', 'TO-252', 'HSOP-8', 'SMA', 'SMB', 'SMC', 'SOD-123'):
        if k in footprint: return k
    return None

rows = list(csv.DictReader(open(SRC)))
res = []
cache = {}
for r in rows:
    code = r['LCSC'].strip(); qty = int(r.get('Qty', '1') or 1)
    rec = {'lcsc': code, 'refs': r['Reference'], 'value': r['Value'], 'footprint': r['Footprint'].split(':')[-1], 'qty': qty, 'need': qty * BOARDS, 'flags': []}
    if not re.fullmatch(r'C\d+', code):
        rec['flags'].append('PLACEHOLDER'); res.append(rec); continue
    if code not in cache: cache[code] = fetch(code); time.sleep(0.3)
    c = cache[code]
    if c is None: rec['flags'].append('NOT_FOUND'); res.append(rec); continue
    if 'error' in c: rec['flags'].append('QUERY_ERROR ' + c['error'][:60]); res.append(rec); continue
    rec.update(mfr=c.get('mfr'), package=c.get('package'), stock=c.get('stock'), price=c.get('price'), basic=c.get('is_basic'), preferred=c.get('is_preferred'), descr=(c.get('description') or '')[:90])
    if not rec['stock']: rec['flags'].append('OUT_OF_STOCK')
    elif rec['stock'] < rec['need'] * 3: rec['flags'].append('LOW_STOCK')
    if not (rec['basic'] or rec['preferred']): rec['flags'].append('EXTENDED')
    sz = fp_size(rec['footprint']); pk = (rec['package'] or '')
    if sz and sz not in pk and not (sz == 'SOIC-8' and 'SOP-8' in pk) and not (sz == 'TO-252' and 'TO-252' in pk): rec['flags'].append(f'PACKAGE_MISMATCH {pk}')
    # value check: the BOM value against JLC's own description (this is what catches C22936 = 1 R sold as '1M')
    if rec['footprint'].startswith(('R_', 'C_')):
        bv, jv = bom_value(rec['value']), jlc_value(c.get('description') or '')
        if bv and jv and (bv[0] != jv[0] or abs(bv[1] - jv[1]) > 0.011 * max(bv[1], 1e-15)):
            rec['flags'].append(f'VALUE_MISMATCH jlc={jv[1]:g}{jv[0]}')
    res.append(rec)

n_real = sum(1 for x in res if 'PLACEHOLDER' not in x['flags'])
flagged = [x for x in res if x['flags'] and x['flags'] != ['EXTENDED'] and 'PLACEHOLDER' not in x['flags']]
ext = [x for x in res if 'EXTENDED' in x['flags']]
cost = sum((x.get('price') or 0) * x['need'] for x in res if x.get('price'))
print(f'{len(rows)} BOM lines, {n_real} real LCSC lines, {len(set(x["lcsc"] for x in res if "PLACEHOLDER" not in x["flags"]))} unique codes')
print(f'flagged (not just EXTENDED): {len(flagged)}; plain-Extended lines: {len(ext)} (feeder fee ${3.07 * len(set(x["lcsc"] for x in ext)):.2f}); parts cost for {BOARDS} boards ${cost:.2f}')
for x in flagged: print('  ', x['lcsc'], x['refs'][:40], x['value'], x['flags'], 'stock', x.get('stock'))
if OUT: json.dump({'boards': BOARDS, 'date': time.strftime('%Y-%m-%d'), 'lines': res}, open(OUT, 'w'), indent=1)
if MD:
    with open(MD, 'w') as f:
        f.write(f'# JLC re-verification {time.strftime("%Y-%m-%d")} — {BOARDS} boards\n\n| LCSC | Refs | Value | Pkg (KiCad) | Pkg (JLC) | Stock | Need | Price | Basic/Pref | Flags |\n|---|---|---|---|---|---|---|---|---|---|\n')
        for x in sorted(res, key=lambda x: (x['flags'] == [], x['lcsc'])):
            f.write(f"| `{x['lcsc']}` | {x['refs'][:30]} | {x['value']} | {x['footprint'][:22]} | {x.get('package','')} | {x.get('stock','')} | {x['need']} | {x.get('price','')} | {'B' if x.get('basic') else ''}{'P' if x.get('preferred') else ''} | {' '.join(x['flags'])} |\n")
