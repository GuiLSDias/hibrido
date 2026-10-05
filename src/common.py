"""Operações comuns; não compartilha incumbentes entre abordagens."""
import numpy as np


def normalize(colors):
    mapping = {}
    return np.array([mapping.setdefault(int(c), len(mapping)) for c in colors], dtype=int)


def valid(inst, colors):
    if colors is None or len(colors) != inst['n']:
        return False
    a = np.asarray(colors)
    return bool(np.all(a >= 0) and np.all(a == a.astype(int)) and
                all(a[u] != a[v] for u, v in inst['edges']))


def objective(colors):
    return len(set(map(int, colors)))


def dsatur(inst, rng=None):
    """DSATUR: saturação, grau e desempate determinístico/aleatório."""
    n, adj = inst['n'], inst['adj']
    colors = np.full(n, -1, dtype=int)
    sat = [set() for _ in range(n)]
    remaining = set(range(n))
    tie = np.arange(n)[::-1] if rng is None else rng.random(n)
    while remaining:
        v = max(remaining, key=lambda v: (len(sat[v]), len(adj[v]), tie[v]))
        c = 0
        while c in sat[v]:
            c += 1
        colors[v] = c
        remaining.remove(v)
        for u in adj[v]:
            sat[u].add(c)
    return normalize(colors)


def clique_bound(inst):
    """Clique gulosa multi-início: limite inferior válido, não clique máxima."""
    adj = [set(a) for a in inst['adj']]
    best = []
    for start in sorted(range(inst['n']), key=lambda v: (-len(adj[v]), v)):
        clique, candidates = [start], set(adj[start])
        while candidates:
            v = max(candidates, key=lambda u: (len(candidates & adj[u]), len(adj[u]), -u))
            clique.append(v)
            candidates &= adj[v]
        if len(clique) > len(best):
            best = clique
    return max(1, len(best)), list(map(int, best))


def record(trace, origin, colors, phase):
    import time
    value = objective(colors)
    if not trace or value < trace[-1]['cores']:
        trace.append({'t': time.perf_counter() - origin, 'cores': value, 'fase': phase})
