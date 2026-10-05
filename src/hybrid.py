"""Tabu -> Fix-and-Optimize -> MIP global, tudo dentro do orçamento T."""
import time
import numpy as np
from .heuristic import tabu_search
from .exact import solve_mip
from .common import objective, record


def neighborhood(inst, colors, K, strategy, rng):
    # Todos os vértices da menor classe ficam livres, para permitir eliminá-la.
    classes = [np.flatnonzero(colors == c) for c in range(objective(colors))]
    smallest = min(classes, key=len)
    mandatory = set(map(int, smallest))
    saturation = [len(set(colors[inst['adj'][v]])) for v in range(inst['n'])]
    adjacent = set(int(u) for v in smallest for u in inst['adj'][v])
    others = [v for v in range(inst['n']) if v not in mandatory]
    ranking = sorted(others, key=lambda v: (v in adjacent, saturation[v], len(inst['adj'][v]), -v), reverse=True)
    slots = max(0, min(inst['n'], K) - len(mandatory))
    if strategy == 'critical':
        chosen = ranking[:slots]
    elif strategy == 'random':
        chosen = rng.permutation(others)[:slots].tolist()
    elif strategy == 'mix':
        first = ranking[:slots//2]
        tail = [v for v in others if v not in first]
        chosen = first + rng.permutation(tail)[:slots-len(first)].tolist()
    else:
        raise ValueError('Estratégia desconhecida')
    return sorted(mandatory | set(chosen))


def hybrid(inst, T, strategy='critical', seed=1, warm_only=False):
    start = time.perf_counter(); deadline = start + T
    trace, fo_log = [], []
    r = tabu_search(inst, max(0, min(0.1*T, deadline-time.perf_counter())), seed, trace, start)
    best = r['colors']; warm_time = time.perf_counter()-start
    rng = np.random.default_rng(seed)
    fo_deadline = min(deadline, time.perf_counter()+0.4*T)
    K = min(inst['n'], max(5, int(0.4*inst['n'])))
    misses = 0
    if not warm_only:
        while time.perf_counter() < fo_deadline and misses < 4:
            # Renomeia a menor classe para a última cor: y ordenado pode
            # então desligá-la. Sem isso, cores fixas posteriores impediriam
            # a eliminação de uma classe com rótulo intermediário.
            smallest = min(range(objective(best)), key=lambda c: int(np.sum(best == c)))
            order = [c for c in range(objective(best)) if c != smallest] + [smallest]
            mapping = {c: i for i, c in enumerate(order)}
            best = np.array([mapping[int(c)] for c in best], dtype=int)
            free = neighborhood(inst, best, K, strategy, rng)
            before = objective(best)
            sub = solve_mip(inst, min(2.0, fo_deadline-time.perf_counter()), best, free, trace, start, seed)
            if sub['obj'] < before:
                best = sub['colors']; misses = 0
            else:
                misses += 1
            fo_log.append({'free': free, 'K': len(free), 'before': before, 'after': objective(best),
                           'time': sub['time'], 'status': sub['status'],
                           'subproblem_optimal': sub['subproblem_optimal']})
            if sub['subproblem_optimal'] and sub['time'] < 1.0:
                K = min(inst['n'], max(K+1, int(1.25*K)))
            elif not sub['subproblem_optimal']:
                K = max(5, int(0.7*K))
    before_global = time.perf_counter()
    full = solve_mip(inst, max(0, deadline-before_global), best, trace=trace, origin=start, seed=seed)
    record(trace, start, full['colors'], 'final')
    full.update(time=time.perf_counter()-start, warm_time=warm_time,
                fo_time=before_global-start-warm_time, fo_log=fo_log, trace=trace)
    return full
