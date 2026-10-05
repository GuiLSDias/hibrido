"""Executa as 4 abordagens (+ ablação de estratégias de fix-and-optimize) sob o MESMO orçamento T.
Uso: python run_experiments.py [--T 20] [--reps 3] [--sizes 25 50 100 200 400 800]
Saídas: results.csv, results.json (traces/anytime), data/instances.json (parâmetros + sementes)."""
import argparse, json, time, csv, os
import numpy as np
from src.generator import generate, seed_for, SIZES, R_DEFAULT, SEED_BASE
from src.common import dantzig_bound, evaluate
from src.heuristic import tabu_search
from src.exact import solve_mip
from src.hybrid import hybrid

ap = argparse.ArgumentParser()
ap.add_argument("--T", type=float, default=20.0)
ap.add_argument("--reps", type=int, default=3)
ap.add_argument("--sizes", type=int, nargs="+", default=SIZES)
ap.add_argument("--ablation_sizes", type=int, nargs="+", default=[200, 400, 800])
ap.add_argument("--out", default=".")
a = ap.parse_args()
T = a.T
rows, traces, inst_meta = [], {}, []
FIELDS = ["fo_sub", "fo_imp", "N", "rep", "seed", "metodo", "obj", "bound", "optimal", "tempo_s", "dantzig", "T"]


def add(inst, rep, metodo, obj, bound, optimal, t, tr=None):
    rows.append(dict(N=inst["n"], rep=rep, seed=inst["seed"], metodo=metodo, obj=obj, bound=bound,
                     optimal=bool(optimal), tempo_s=round(t, 3), dantzig=round(dantzig_bound(inst), 2), T=T))
    if tr is not None: traces[f"{inst['n']}_{rep}_{metodo}"] = [(round(t_, 4), v) for t_, v in tr]
    print(f"N={inst['n']:4d} rep={rep} {metodo:18s} obj={obj} bound={bound} opt={optimal} t={t:.1f}s", flush=True)


def save():
    with open(os.path.join(a.out, "results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS, restval=""); w.writeheader(); w.writerows(rows)
    json.dump({"T": T, "traces": traces}, open(os.path.join(a.out, "results.json"), "w"))


for n in a.sizes:
    for rep in range(a.reps):
        inst = generate(n, seed_for(n, rep))
        inst_meta.append(dict(N=n, rep=rep, seed=inst["seed"], R=inst["R"], kind=inst["kind"],
                              cap_frac=inst["cap_frac"], C=inst["C"], dantzig=dantzig_bound(inst)))
        # 1) heurística pura: Busca Tabu usa T inteiro
        t0 = time.perf_counter(); tr = []
        x, v, _ = tabu_search(inst, T, seed=rep)
        add(inst, rep, "heuristica", v, None, False, time.perf_counter() - t0)
        # 2) exato puro
        tr = []; t0 = time.perf_counter(); r = solve_mip(inst, T, trace=tr, t_origin=t0)
        add(inst, rep, "exato", r["obj"], r["bound"], r["optimal"], r["time"], tr)
        # 3) exato + warm start (tabu 10% de T, exato no restante) -- isola o efeito do warm start
        t0 = time.perf_counter(); x, v, _ = tabu_search(inst, 0.1 * T, seed=rep)
        tr = [(time.perf_counter() - t0, float(v))]
        left = T - (time.perf_counter() - t0)
        r = solve_mip(inst, left, x0=x, trace=tr, t_origin=t0)
        add(inst, rep, "exato+warm", max(v, r["obj"] or 0), r["bound"], r["optimal"], time.perf_counter() - t0, tr)
        # 4) híbrido completo: warm start + fix-and-optimize (rc) + exato com incumbente
        r = hybrid(inst, T, strategy="rc", seed=rep)
        add(inst, rep, "hibrido", r["obj"], r["bound"], r["optimal"], r["time"], r["trace"])
        rows[-1]["fo_sub"] = r["log"].get("fo_subproblems"); rows[-1]["fo_imp"] = r["log"].get("fo_improvements")
        # ablação das estratégias de fix-and-optimize
        if n in a.ablation_sizes:
            for s in ["random", "mix"]:
                r = hybrid(inst, T, strategy=s, seed=rep)
                add(inst, rep, f"hibrido_{s}", r["obj"], r["bound"], r["optimal"], r["time"], r["trace"])
        save()
os.makedirs(os.path.join(a.out, "data"), exist_ok=True)
json.dump({"seed_base": SEED_BASE, "R": R_DEFAULT, "regra_seed": "seed = 2026 + 1000*rep + N",
           "gerador": "w~U{1..R}, p=w+R/10 (strongly correlated), C=floor(0.5*sum w)", "instancias": inst_meta},
          open(os.path.join(a.out, "data", "instances.json"), "w"), indent=1)
print("FIM")
