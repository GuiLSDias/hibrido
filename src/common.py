import time
import numpy as np


def evaluate(inst, x):
    return int(inst["p"] @ x), int(inst["w"] @ x)


def dantzig_bound(inst):
    """Limite superior LP (relaxação linear da mochila, solução gulosa fracionária)."""
    w, p, C = inst["w"], inst["p"], inst["C"]
    order = np.argsort(-(p / w), kind="stable")
    cap, val = C, 0.0
    for i in order:
        if w[i] <= cap:
            cap -= w[i]; val += p[i]
        else:
            val += p[i] * cap / w[i]; break
    return val


def greedy(inst):
    """Guloso por razão p/w (mesma semente inicial do TP-I)."""
    w, p, C = inst["w"], inst["p"], inst["C"]
    order = np.argsort(-(p / w), kind="stable")
    x = np.zeros(inst["n"], dtype=np.int8); cap = C
    for i in order:                       # continua após o primeiro que não cabe (preenche folgas)
        if w[i] <= cap:
            x[i] = 1; cap -= w[i]
    return x


class Clock:
    def __init__(self, limit):
        self.t0 = time.perf_counter(); self.limit = limit
    def elapsed(self): return time.perf_counter() - self.t0
    def left(self): return self.limit - self.elapsed()
