"""Minimal KiCad S-expression reader/writer preserving structure."""
import re

def parse(text):
    """Return nested lists. Atoms are str (quoted strings keep a marker)."""
    i = 0; n = len(text)
    def rd():
        nonlocal i
        while i < n and text[i] in ' \t\r\n': i += 1
        if text[i] == '(':
            i += 1
            out = []
            while True:
                while i < n and text[i] in ' \t\r\n': i += 1
                if text[i] == ')':
                    i += 1; return out
                out.append(rd())
        if text[i] == '"':
            i += 1; buf = []
            while text[i] != '"':
                if text[i] == '\\':
                    buf.append(text[i]); i += 1
                buf.append(text[i]); i += 1
            i += 1
            return ('str', ''.join(buf))
        j = i
        while i < n and text[i] not in ' \t\r\n()': i += 1
        return text[j:i]
    while i < n and text[i] in ' \t\r\n': i += 1
    return rd()

def sym(x):
    """head symbol of a node, or None"""
    if isinstance(x, list) and x and isinstance(x[0], str):
        return x[0]
    return None

def val(x):
    """unwrap a ('str', s) or plain atom"""
    if isinstance(x, tuple): return x[1]
    return x

def get(node, name):
    for c in node:
        if sym(c) == name: return c
    return None

def getall(node, name):
    return [c for c in node if sym(c) == name]

def at(node):
    a = get(node, 'at')
    if not a: return None
    return (float(val(a[1])), float(val(a[2])), float(val(a[3])) if len(a) > 3 else 0.0)
