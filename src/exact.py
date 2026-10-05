"""Método exato: MIP da mochila 0/1 resolvido com HiGHS (branch-and-cut), com suporte a
(i) incumbente inicial (warm start), (ii) subconjunto livre de variáveis (para fix-and-optimize)."""
import time
import numpy as np
import highspy

INF = highspy.kHighsInf


def solve_mip(inst, time_limit, x0=None, free=None, trace=None, t_origin=None, threads=1):
    """Resolve max p.x s.t. w.x <= C, x binário.

    free: índices livres; os demais ficam fixos no valor de x0 (modelo reduzido, mais rápido que
          fixar por bounds). Exige x0.
    trace: lista onde se anexa (tempo, objetivo_total) a cada incumbente melhor (callback do HiGHS).
    Retorna dict(x, obj, bound, optimal, time, status).
    """
    n, w, p, C = inst["n"], inst["w"], inst["p"], inst["C"]
    idx = np.arange(n) if free is None else np.asarray(free, dtype=np.int64)
    m = len(idx)
    offset_val = 0; offset_w = 0
    if free is not None:
        fixed_mask = np.ones(n, dtype=bool); fixed_mask[idx] = False
        offset_val = int(p[fixed_mask] @ x0[fixed_mask]); offset_w = int(w[fixed_mask] @ x0[fixed_mask])
    cap = C - offset_w
    h = highspy.Highs(); h.setOptionValue("output_flag", False)
    h.setOptionValue("time_limit", float(max(0.05, time_limit)))
    h.setOptionValue("mip_rel_gap", 0.0); h.setOptionValue("mip_abs_gap", 0.999)  # profits inteiros -> ótimo provado
    h.setOptionValue("threads", threads); h.setOptionValue("random_seed", 1)
    cols = np.arange(m, dtype=np.int32)
    lp = highspy.HighsLp()
    lp.num_col_ = m; lp.num_row_ = 1
    lp.col_cost_ = (-p[idx]).astype(float); lp.col_lower_ = np.zeros(m); lp.col_upper_ = np.ones(m)
    lp.row_lower_ = np.array([-INF]); lp.row_upper_ = np.array([float(cap)])
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    lp.a_matrix_.start_ = np.array([0, m], dtype=np.int32)
    lp.a_matrix_.index_ = cols; lp.a_matrix_.value_ = w[idx].astype(float)
    lp.integrality_ = [highspy.HighsVarType.kInteger] * m
    h.passModel(lp)
    if x0 is not None:
        sol = highspy.HighsSolution(); sol.col_value = [float(v) for v in x0[idx]]
        h.setSolution(sol)
    if trace is not None:
        t0 = t_origin if t_origin is not None else time.perf_counter()
        def cb(ev):
            try:
                v = -ev.data_out.objective_function_value + offset_val
                trace.append((time.perf_counter() - t0, float(v)))
            except Exception:
                pass
        try:
            h.cbMipImprovingSolution.subscribe(cb); h.startCallback(highspy.cb.HighsCallbackType.kCallbackMipImprovingSolution)
        except Exception:
            pass
    t = time.perf_counter(); h.run(); t = time.perf_counter() - t
    info = h.getInfo(); st = h.getModelStatus()
    status = h.modelStatusToString(st)
    sol = h.getSolution().col_value
    out_x = None if x0 is None else x0.copy()
    if len(sol) == m and info.primal_solution_status == 2:
        xs = np.rint(np.array(sol)).astype(np.int8)
        if free is None:
            out_x = xs
        else:
            cand = x0.copy(); cand[idx] = xs
            if cand @ w <= C and (cand @ p) >= (x0 @ p if x0 is not None else -1): out_x = cand
    elif free is None:
        out_x = None
    obj = int(p @ out_x) if out_x is not None else None
    bound = -info.mip_dual_bound + offset_val if np.isfinite(info.mip_dual_bound) else None
    return {"x": out_x, "obj": obj, "bound": bound, "optimal": status == "Optimal",
            "time": t, "status": status}
