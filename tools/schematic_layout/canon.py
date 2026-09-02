r"""Re-emit MCP-added symbol blocks in KiCad's canonical tab-indented form.

The MCP server writes `(symbol (lib_id "...") (at X Y R) (unit 1)` on one line with
space indentation. sheetedit.Sheet finds top-level nodes with `^\t\(` and rewrites
placement with `^\t\t\(at ...\)$`, so a space-indented block is invisible to it --
the symbols are simply skipped, silently. This normalises them.
"""
import sys, os, re, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse

def atom(a):
    return f'"{a[1]}"' if isinstance(a, tuple) else a

def fmt(node, d=1):
    ind = '\t' * d
    if not isinstance(node, list):
        return ind + atom(node)
    head, i = [], 0
    while i < len(node) and not isinstance(node[i], list):
        head.append(atom(node[i])); i += 1
    rest = node[i:]
    open_ = ind + '(' + ' '.join(head)
    if not rest:
        return open_ + ')'
    return '\n'.join([open_] + [fmt(c, d + 1) for c in rest] + [ind + ')'])

def block_at(text, start):
    """balanced span of the node beginning at `start`"""
    d, k = 0, start
    while True:
        if text[k] == '"':
            k += 1
            while text[k] != '"':
                k += 2 if text[k] == '\\' else 1
        elif text[k] == '(': d += 1
        elif text[k] == ')':
            d -= 1
            if d == 0: return k + 1
        k += 1

def canonicalise(path):
    t = io.open(path, encoding='utf-8').read()
    n = 0
    while True:
        m = re.search(r'(?m)^[ \t]*\(symbol \(lib_id ', t)
        if not m: break
        a = t.index('(symbol', m.start())
        b = block_at(t, a)
        new = fmt(parse(t[a:b]), 1)
        line_start = t.rfind('\n', 0, a) + 1
        t = t[:line_start] + new + t[b:]
        n += 1
    io.open(path, 'w', encoding='utf-8').write(t)
    return n

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(p, "->", canonicalise(p), "symbol blocks normalised")
