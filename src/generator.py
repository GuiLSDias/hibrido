"""Grafos simples G(N,p): cada aresta é sorteada independentemente."""
import numpy as np
SIZES = [10, 15, 20, 30, 40, 60]
SEED_BASE = 2026
DENSITY = 0.5


def seed_for(n, rep):
    return SEED_BASE + 1000 * rep + n


def from_edges(n, edges, seed=0, density=None):
    if n < 1:
        raise ValueError('N deve ser positivo')
    edges = sorted(set(tuple(sorted(map(int, e))) for e in edges))
    adj = [[] for _ in range(n)]
    for u, v in edges:
        if not 0 <= u < v < n:
            raise ValueError('Aresta inválida')
        adj[u].append(v); adj[v].append(u)
    return {'n': n, 'seed': seed, 'p': density, 'edges': edges,
            'adj': [np.array(a, dtype=int) for a in adj]}


def generate(n, seed, density=DENSITY):
    if not 0 <= density <= 1:
        raise ValueError('p deve estar entre 0 e 1')
    rng = np.random.default_rng(seed)
    edges = [(u, v) for u in range(n) for v in range(u + 1, n)
             if rng.random() < density]
    return from_edges(n, edges, seed, density)
