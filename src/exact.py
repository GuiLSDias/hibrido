"""MIP de coloração mínima com x[v,c] e y[c], HiGHS / branch-and-cut.
O ótimo de subproblema F&O NUNCA é tratado como prova do problema completo.
"""
import time
import math
import numpy as np
import highspy
from .common import dsatur, normalize, valid, objective, clique_bound, record
INF = highspy.kHighsInf


def solve_mip(inst, time_limit, colors0=None, free=None, trace=None, origin=None, seed=1):
    start = time.perf_counter()
    deadline = start + max(0, time_limit)
    origin = start if origin is None else origin
    trace = [] if trace is None else trace
    if free is not None and colors0 is None:
        raise ValueError('F&O exige uma coloração inicial')
    if colors0 is not None and not valid(inst, colors0):
        raise ValueError('Warm start inválido')
    # Pré-processamento igual nas fases completas: DSATUR limita a paleta, sem
    # fornecer incumbente ao exato puro. Este tempo entra no orçamento.
    baseline = dsatur(inst)
    lb, clique = clique_bound(inst)
    n = inst['n']
    if colors0 is not None:
        colors0 = np.array(colors0, dtype=int)
        if free is None:
            colors0 = normalize(colors0)
    palette = objective(baseline) if colors0 is None else objective(colors0)
    k = palette
    total = n * k + k
    costs = np.r_[np.zeros(n * k), np.ones(k)]
    lower, upper = np.zeros(total), np.ones(total)
    # Primeira ocorrência quebra simetria apenas no modelo completo. Aplicá-la
    # no F&O poderia excluir soluções porque cores externas estão fixadas.
    if free is None:
        for v in range(n):
            upper[v*k + min(v+1, k):(v+1)*k] = 0
    else:
        free = set(map(int, free))
        if not free.issubset(range(n)):
            raise ValueError('Vértice livre inválido')
        for v in range(n):
            if v not in free:
                upper[v*k:(v+1)*k] = 0
                lower[v*k + colors0[v]] = upper[v*k + colors0[v]] = 1
    starts, indices, values, row_lo, row_hi = [0], [], [], [], []
    def row(idx, val, lo, hi):
        indices.extend(idx); values.extend(val); starts.append(len(indices))
        row_lo.append(lo); row_hi.append(hi)
    # Uma cor por vértice.
    for v in range(n):
        row(list(range(v*k, (v+1)*k)), [1]*k, 1, 1)
    # Adjacentes não compartilham cor; ligação x <= y.
    for u, v in inst['edges']:
        for c in range(k):
            row([u*k+c, v*k+c, n*k+c], [1, 1, -1], -INF, 0)
    for v in range(n):
        for c in range(k):
            row([v*k+c, n*k+c], [1, -1], -INF, 0)
    # Cores utilizadas formam prefixo; limite inferior de clique válido.
    for c in range(k-1):
        row([n*k+c, n*k+c+1], [1, -1], 0, INF)
    row(list(range(n*k, total)), [1]*k, lb, INF)
    lp = highspy.HighsLp()
    lp.num_col_ = total; lp.num_row_ = len(row_lo)
    lp.col_cost_ = costs; lp.col_lower_ = lower; lp.col_upper_ = upper
    lp.row_lower_ = row_lo; lp.row_upper_ = row_hi
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    lp.a_matrix_.start_ = np.array(starts, dtype=np.int32)
    lp.a_matrix_.index_ = np.array(indices, dtype=np.int32)
    lp.a_matrix_.value_ = np.array(values, dtype=float)
    lp.integrality_ = [highspy.HighsVarType.kInteger] * total
    h = highspy.Highs()
    for name, value in [('output_flag', False), ('threads', 1), ('random_seed', int(seed)),
                        ('mip_rel_gap', 0.0), ('mip_abs_gap', 0.0)]:
        if h.setOptionValue(name, value) != highspy.HighsStatus.kOk:
            raise RuntimeError('Opção HiGHS inválida: ' + name)
    if h.passModel(lp) != highspy.HighsStatus.kOk:
        raise RuntimeError('Falha na construção do MIP')
    warm_accepted = False
    if colors0 is not None:
        sol = highspy.HighsSolution()
        col = np.zeros(total)
        col[np.arange(n)*k + colors0] = 1
        col[n*k:] = 1
        sol.col_value = col.tolist()
        warm_accepted = h.setSolution(sol) == highspy.HighsStatus.kOk
        if not warm_accepted:
            raise RuntimeError('HiGHS rejeitou o MIP start')
    def cb(event):
        raw = np.asarray(event.data_out.mip_solution)
        if raw.size == total:
            colors = np.argmax(raw[:n*k].reshape(n, k), axis=1)
            if valid(inst, colors):
                record(trace, origin, colors, 'fo' if free is not None else 'exato')
    h.cbMipImprovingSolution.subscribe(cb)
    remaining = deadline - time.perf_counter()
    fallback = colors0.copy() if colors0 is not None else baseline
    if remaining <= 0:
        return {'colors': fallback, 'obj': objective(fallback), 'bound': lb,
                'optimal': False, 'subproblem_optimal': False, 'status': 'Budget exhausted before solve',
                'time': time.perf_counter()-start, 'solver_time': 0.0, 'warm_accepted': warm_accepted,
                'fallback': colors0 is None, 'trace': trace}
    h.setOptionValue('time_limit', remaining)
    solver_start = time.perf_counter(); h.run(); solver_time = time.perf_counter()-solver_start
    status = h.getModelStatus(); info = h.getInfo(); solution = h.getSolution()
    out, used_fallback = fallback, True
    if solution.value_valid and info.primal_solution_status == highspy.SolutionStatus.kSolutionStatusFeasible:
        raw = np.asarray(solution.col_value)
        colors = np.argmax(raw[:n*k].reshape(n, k), axis=1)
        if valid(inst, colors) and objective(colors) <= objective(out):
            out, used_fallback = normalize(colors), False
    bound = float(info.mip_dual_bound)
    if not math.isfinite(bound):
        bound = float(lb)
    if free is not None:
        bound = float(lb)  # Limite restrito não é limite global.
    else:
        bound = max(float(lb), bound)
    record(trace, origin, out, 'fo' if free is not None else ('fallback_dsatur' if used_fallback else 'exato'))
    optimal = free is None and status == highspy.HighsModelStatus.kOptimal and not used_fallback
    return {'colors': out, 'obj': objective(out), 'bound': bound, 'optimal': optimal,
            'subproblem_optimal': status == highspy.HighsModelStatus.kOptimal,
            'status': h.modelStatusToString(status), 'time': time.perf_counter()-start,
            'solver_time': solver_time, 'warm_accepted': warm_accepted,
            'fallback': used_fallback, 'trace': trace, 'clique': clique}
