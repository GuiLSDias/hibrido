"""Busca Tabu para coloração: tenta k-1 cores minimizando conflitos (TabuCol).
Soluções intermediárias podem ter conflitos; só retorna colorações válidas.
"""
import time
import numpy as np
from .common import dsatur, normalize, valid, objective, record, clique_bound


def tabu_search(inst, time_limit, seed=1, trace=None, origin=None):
    start = time.perf_counter()
    deadline = start + max(0, time_limit)
    origin = start if origin is None else origin
    trace = [] if trace is None else trace
    rng = np.random.default_rng(seed)
    best = dsatur(inst, rng)
    record(trace, origin, best, 'tabu')
    lb, _ = clique_bound(inst)
    iterations = restarts = 0
    while time.perf_counter() < deadline and objective(best) > lb:
        k = objective(best) - 1
        # Remove a menor classe; os seus vértices geram o estado conflituoso inicial.
        classes = [np.flatnonzero(best == c) for c in range(k + 1)]
        removed = min(range(k + 1), key=lambda c: len(classes[c]))
        order = [c for c in range(k + 1) if c != removed]
        mapping = {c: i for i, c in enumerate(order)}
        colors = np.array([mapping.get(int(c), -1) for c in best])
        for v in classes[removed]:
            counts = np.bincount(colors[inst['adj'][v]][colors[inst['adj'][v]] >= 0], minlength=k)
            choices = np.flatnonzero(counts == counts.min())
            colors[v] = int(rng.choice(choices))
        counts = np.zeros((inst['n'], k), dtype=int)
        for v in range(inst['n']):
            counts[v] = np.bincount(colors[inst['adj'][v]], minlength=k)
        conflicts = sum(colors[u] == colors[v] for u, v in inst['edges'])
        tabu = np.zeros_like(counts)
        local_best, stagnant, it = conflicts, 0, 0
        while conflicts and time.perf_counter() < deadline:
            conflicted = np.flatnonzero(counts[np.arange(inst['n']), colors] > 0)
            delta = counts[conflicted] - counts[conflicted, colors[conflicted]][:, None]
            allowed = (tabu[conflicted] <= it) | (conflicts + delta < local_best)
            allowed[np.arange(len(conflicted)), colors[conflicted]] = False
            score = np.where(allowed, delta, 10**9)
            choices = np.argwhere(score == score.min())
            if score.min() == 10**9:
                # Não há movimento permitido: avança até expirar uma proibição.
                it = int(tabu[conflicted].min()) + it + 1
                continue
            row, new = choices[int(rng.integers(len(choices)))]
            v = int(conflicted[row]); new = int(new); old = int(colors[v])
            conflicts += int(delta[row, new])
            colors[v] = new
            counts[inst['adj'][v], old] -= 1
            counts[inst['adj'][v], new] += 1
            tabu[v, old] = it + int(0.6 * len(conflicted)) + int(rng.integers(4, 11))
            it += 1; iterations += 1; stagnant += 1
            if conflicts < local_best:
                local_best = conflicts; stagnant = 0
            if stagnant >= max(200, 20 * inst['n']):
                restarts += 1
                break  # Diversificação: novo desempate/reinicialização da menor classe.
        if conflicts == 0:
            candidate = normalize(colors)
            assert valid(inst, candidate)
            best = candidate
            record(trace, origin, best, 'tabu')
        elif time.perf_counter() < deadline:
            candidate = dsatur(inst, rng)
            if objective(candidate) < objective(best):
                best = candidate; record(trace, origin, best, 'tabu')
    return {'colors': best, 'obj': objective(best), 'trace': trace,
            'time': time.perf_counter() - start, 'iterations': iterations, 'restarts': restarts}
