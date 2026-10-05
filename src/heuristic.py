"""Busca Tabu (adaptada do TP-I em JS) para a Mochila 0/1, com avaliação incremental O(1) por movimento.

Vizinhança: flip (insere/remove) + swap 1-1 (item dentro <-> item fora), com viabilidade mantida
(movimentos que estouram C são descartados -> sem reparo). Tenure dinâmico ~ sqrt(n),
aspiração por valor, diversificação por perturbação da melhor solução após estagnação.
O swap é avaliado de forma vetorizada (numpy) sobre a matriz in x out.
"""
import numpy as np
from .common import greedy, evaluate, Clock


def tabu_search(inst, time_limit, x0=None, seed=0, stag_limit=None, verbose=False):
    rng = np.random.default_rng(seed)
    n, w, p, C = inst["n"], inst["w"], inst["p"], inst["C"]
    clk = Clock(time_limit)
    x = (greedy(inst) if x0 is None else x0.copy()).astype(np.int8)
    val, wt = evaluate(inst, x)
    best_x, best_val = x.copy(), val
    tabu_until = np.zeros(n, dtype=np.int64)
    it = 0; last_imp = 0
    stag_limit = stag_limit or max(100, 3 * n)
    tenure = max(5, int(np.sqrt(n)))
    ratio = p / w
    while clk.left() > 0:
        it += 1
        ins = np.where(x == 1)[0]; out = np.where(x == 0)[0]
        cand_val = -np.inf; mv = None
        # --- flip: inserir item fora que ainda cabe
        if len(out):
            fit = out[wt + w[out] <= C]
            if len(fit):
                nv = val + p[fit]
                ok = (tabu_until[fit] <= it) | (nv > best_val)
                if ok.any():
                    k = np.argmax(np.where(ok, nv, -np.inf)); cand_val = nv[k]; mv = ("add", fit[k], -1)
        # --- swap 1-1 (vetorizado)
        if len(ins) and len(out):
            dw = w[out][None, :] - w[ins][:, None]                  # (|ins|, |out|)
            feas = wt + dw <= C
            dv = p[out][None, :] - p[ins][:, None]
            nv = val + dv
            allowed = ((tabu_until[ins][:, None] <= it) & (tabu_until[out][None, :] <= it)) | (nv > best_val)
            sc = np.where(feas & allowed, nv, -np.inf)
            idx = np.argmax(sc); a, b = divmod(idx, len(out))
            if sc[a, b] > cand_val:
                cand_val = sc[a, b]; mv = ("swap", ins[a], out[b])
        # --- remoção (escape) se nada viável
        if mv is None:
            if len(ins):
                j = ins[np.argmin(ratio[ins])]; mv = ("drop", j, -1); cand_val = val - p[j]
            else:
                break
        kind, i, j = mv
        if kind == "add":
            x[i] = 1; wt += w[i]; tabu_until[i] = it + tenure + rng.integers(0, tenure)
        elif kind == "drop":
            x[i] = 0; wt -= w[i]; tabu_until[i] = it + tenure + rng.integers(0, tenure)
        else:
            x[i] = 0; x[j] = 1; wt += w[j] - w[i]
            tabu_until[i] = it + tenure + rng.integers(0, tenure)
            tabu_until[j] = it + tenure // 2
        val = int(cand_val)
        if val > best_val:
            best_val, best_x, last_imp = val, x.copy(), it
        # --- diversificação
        if it - last_imp > stag_limit:
            x = best_x.copy()
            ins = np.where(x == 1)[0]
            k = max(2, len(ins) // 10)
            for r in rng.choice(ins, size=min(k, len(ins)), replace=False): x[r] = 0
            wt = int(w @ x)
            for r in rng.permutation(np.where(x == 0)[0]):       # reenche aleatoriamente
                if wt + w[r] <= C: x[r] = 1; wt += w[r]
            val = int(p @ x); last_imp = it; tabu_until[:] = 0
    return best_x, int(best_val), {"iters": it, "time": clk.elapsed()}
