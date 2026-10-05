"""Hibridização heurística + exato.

Pipeline do HÍBRIDO (orçamento total T):
  Fase 1  Warm start      : Busca Tabu por warm_frac*T  -> incumbente x0
  Fase 2  Fix-and-optimize: vizinhanças MIP exatas pequenas sobre x0 (até fo_frac*T; encerra antes se estagnar)
  Fase 3  Exato completo  : branch-and-cut do HiGHS sobre o problema inteiro, com o melhor incumbente
                            injetado (setSolution) -> prova de otimalidade / limite dual.

A "inteligência" do fix-and-optimize (qual variável fica livre) está em `choose_free`:
  strategy="rc"     janelas deslizantes no ranking de |custo reduzido| = |p_i - lambda*w_i|
                    (itens "incertos" na relaxação linear: lambda = preço-sombra da capacidade);
  strategy="random" subconjunto aleatório (baseline sem inteligência);
  strategy="mix"    metade janela-rc + metade aleatória (diversificação).
"""
import time
import numpy as np
from .common import Clock, dantzig_bound, evaluate
from .heuristic import tabu_search
from .exact import solve_mip


def lp_dual_price(inst):
    """Preço-sombra lambda da capacidade na relaxação linear (razão p/w do item crítico)."""
    w, p, C = inst["w"], inst["p"], inst["C"]
    order = np.argsort(-(p / w), kind="stable"); cap = C
    for i in order:
        if w[i] > cap: return p[i] / w[i]
        cap -= w[i]
    return 0.0


def choose_free(inst, order, pos, K, strategy, rng):
    n = inst["n"]
    K = min(K, n)
    if strategy == "random":
        return rng.choice(n, K, replace=False)
    kw = K if strategy == "rc" else K // 2
    win = order[(pos + np.arange(kw)) % n]
    if strategy == "rc":
        return win
    rest = np.setdiff1d(np.arange(n), win)
    return np.concatenate([win, rng.choice(rest, min(K - kw, len(rest)), replace=False)])


def fix_and_optimize(inst, x, budget, strategy="rc", K0=40, sub_tl=2.0, seed=0, trace=None, t0=None, log=None):
    rng = np.random.default_rng(seed); clk = Clock(budget)
    n, p = inst["n"], inst["p"]
    lam = lp_dual_price(inst)
    score = np.abs(p - lam * inst["w"])
    order = np.argsort(score, kind="stable")           # mais "incertos" primeiro
    x = x.copy(); val = int(p @ x); K = min(K0, n)
    pos = 0; stale = 0; n_sub = 0; n_imp = 0
    while clk.left() > 0.05 and K < n:
        free = choose_free(inst, order, pos, K, strategy, rng)
        r = solve_mip(inst, min(sub_tl, clk.left()), x0=x, free=free)
        n_sub += 1
        if r["x"] is not None and r["obj"] > val:
            x, val = r["x"], r["obj"]; stale = 0; n_imp += 1
            if trace is not None: trace.append((time.perf_counter() - t0, float(val)))
        else:
            stale += 1
        # tamanho adaptativo da vizinhança
        if r["optimal"] and r["time"] < 0.25 * sub_tl: K = min(n, int(K * 1.25) + 1)
        elif not r["optimal"]: K = max(10, int(K * 0.7))
        pos = (pos + max(1, K // 2)) % n
        if stale > 2 * int(np.ceil(n / max(1, K // 2))) + 4:   # várias passadas sem melhora -> encerra
            break
    if log is not None: log.update(fo_subproblems=n_sub, fo_improvements=n_imp, fo_final_K=K, fo_time=clk.elapsed())
    return x, val


def hybrid(inst, T, strategy="rc", warm_frac=0.10, fo_frac=0.40, use_fo=True, seed=0):
    t0 = time.perf_counter(); trace = []; log = {}
    # Fase 1: warm start
    x, v, _ = tabu_search(inst, warm_frac * T, seed=seed)
    trace.append((time.perf_counter() - t0, float(v))); log["warm_val"] = v
    # Fase 2: fix-and-optimize
    if use_fo:
        x, v = fix_and_optimize(inst, x, min(fo_frac * T, T - (time.perf_counter() - t0)), strategy=strategy,
                                seed=seed, trace=trace, t0=t0, log=log)
    log["after_fo_val"] = v
    # Fase 3: exato completo com incumbente
    left = T - (time.perf_counter() - t0)
    tr = []
    r = solve_mip(inst, left, x0=x, trace=tr, t_origin=t0) if left > 0.05 else {"x": x, "obj": v, "bound": None, "optimal": False, "status": "NoTime"}
    trace += [(t, val) for t, val in tr if val > v]
    best_x = r["x"] if (r["x"] is not None and r["obj"] >= v) else x
    best = int(inst["p"] @ best_x)
    return {"x": best_x, "obj": best, "bound": r["bound"], "optimal": r["optimal"],
            "time": time.perf_counter() - t0, "trace": sorted(trace), "log": log}
