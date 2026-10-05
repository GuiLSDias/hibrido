"""Lê results.csv/results.json e gera figuras + results_summary.csv."""
import json, os
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("figures", exist_ok=True)
df = pd.read_csv("results.csv"); R = json.load(open("results.json")); T = R["T"]
ub = {}
for (n, rep), g in df.groupby(["N", "rep"]):
    cands = [g["dantzig"].iloc[0]] + [b for b in g["bound"].dropna()]
    best_obj = g["obj"].max()
    ub[(n, rep)] = max(best_obj, min(cands))        # melhor limite superior provado (nunca < melhor primal)
df["ub"] = [ub[(n, r)] for n, r in zip(df.N, df.rep)]
df["gap_pct"] = 100 * (df.ub - df.obj) / df.ub
df["gap_prov_pct"] = 100 * (df.ub - df.obj) / df.ub
summ = df.groupby(["N", "metodo"]).agg(obj=("obj", "mean"), gap_pct=("gap_pct", "mean"), gap_max=("gap_pct", "max"),
                                       provado=("optimal", "sum"), reps=("optimal", "count"), tempo=("tempo_s", "mean")).reset_index()
summ.to_csv("results_summary.csv", index=False)
print(summ.to_string())

C = {"heuristica": "#8b5cf6", "exato": "#ef4444", "exato+warm": "#f59e0b", "hibrido": "#06b6d4",
     "hibrido_random": "#10b981", "hibrido_mix": "#64748b"}
L = {"heuristica": "Heurística (Tabu)", "exato": "Exato (HiGHS)", "exato+warm": "Exato + warm start",
     "hibrido": "Híbrido (warm + F&O + exato)"}
sizes = sorted(df.N.unique()); main = list(L)
FLOOR = 1e-5

# Fig 1: gap vs N
fig, ax = plt.subplots(figsize=(8, 4.8))
for m in main:
    s = summ[summ.metodo == m].sort_values("N")
    ax.plot(s.N, np.maximum(s.gap_pct, FLOOR), "o-", color=C[m], label=L[m], lw=2)
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xticks(sizes); ax.set_xticklabels(sizes)
ax.set_xlabel("N (itens)"); ax.set_ylabel(f"Gap médio vs. melhor limite superior (%)  [0 plotado em {FLOOR}]")
ax.set_title(f"Qualidade da solução final com orçamento T = {T:g} s"); ax.grid(alpha=.3, which="both"); ax.legend()
fig.tight_layout(); fig.savefig("figures/fig1_gap_vs_N.png", dpi=150); plt.close(fig)

# Fig 2: instâncias com otimalidade provada
fig, ax = plt.subplots(figsize=(8, 4.2)); w = 0.2
for k, m in enumerate(["exato", "exato+warm", "hibrido"]):
    s = summ[summ.metodo == m].sort_values("N")
    ax.bar(np.arange(len(sizes)) + (k - 1) * w, 100 * s.provado / s.reps, w, color=C[m], label=L[m])
ax.set_xticks(range(len(sizes))); ax.set_xticklabels(sizes); ax.set_ylabel("% das instâncias com ótimo provado")
ax.set_xlabel("N (itens)"); ax.set_title(f"Quem fecha o gap em T = {T:g} s?"); ax.legend(); ax.grid(axis="y", alpha=.3)
fig.tight_layout(); fig.savefig("figures/fig2_otimo_provado.png", dpi=150); plt.close(fig)

# Fig 3: tempo até provar ótimo (só instâncias provadas) 
fig, ax = plt.subplots(figsize=(8, 4.2))
for m in ["exato", "exato+warm", "hibrido"]:
    s = df[(df.metodo == m)].groupby("N").apply(lambda g: np.where(g.optimal, g.tempo_s, T).mean(), include_groups=False)
    ax.plot(s.index, s.values, "o-", color=C[m], label=L[m], lw=2)
ax.axhline(T, color="k", ls=":", lw=1); ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xticks(sizes); ax.set_xticklabels(sizes)
ax.set_xlabel("N (itens)"); ax.set_ylabel("Tempo médio até provar ótimo (s; T se não provou)")
ax.set_title("Custo de provar otimalidade"); ax.legend(); ax.grid(alpha=.3, which="both")
fig.tight_layout(); fig.savefig("figures/fig3_tempo_prova.png", dpi=150); plt.close(fig)

# Fig 4: anytime (rep 0) nos 3 maiores tamanhos
big = sizes[-3:]
fig, axs = plt.subplots(1, 3, figsize=(14, 4.2))
for ax, n in zip(axs, big):
    u = ub[(n, 0)]
    for m in ["exato", "exato+warm", "hibrido"]:
        tr = R["traces"].get(f"{n}_0_{m}", [])
        if not tr: continue
        t_, v_ = zip(*tr); t_ = list(t_) + [T]; v_ = list(v_) + [v_[-1]]
        ax.step(t_, 100 * (u - np.array(v_)) / u, where="post", color=C[m], label=L[m], lw=2)
    h = df[(df.N == n) & (df.rep == 0) & (df.metodo == "heuristica")].gap_pct.iloc[0]
    ax.axhline(h, color=C["heuristica"], ls="--", label="Heurística (final)")
    ax.set_yscale("log"); ax.set_title(f"N = {n} (réplica 0)"); ax.set_xlabel("tempo (s)"); ax.grid(alpha=.3, which="both")
axs[0].set_ylabel("gap do incumbente (%)"); axs[0].legend(fontsize=8)
fig.suptitle("Convergência (anytime) do incumbente"); fig.tight_layout(); fig.savefig("figures/fig4_anytime.png", dpi=150); plt.close(fig)

# Fig 5: ablação das estratégias de F&O
ab = ["exato+warm", "hibrido", "hibrido_random", "hibrido_mix"]
names = {"exato+warm": "sem F&O\n(só warm start)", "hibrido": "F&O 'rc'\n(custo reduzido)", "hibrido_random": "F&O aleatório", "hibrido_mix": "F&O mix"}
asz = [n for n in sizes if (df[(df.N == n) & (df.metodo == "hibrido_random")].shape[0] > 0)]
if asz:
    fig, ax = plt.subplots(figsize=(8, 4.2)); w = 0.2
    for k, m in enumerate(ab):
        s = summ[(summ.metodo == m) & summ.N.isin(asz)].sort_values("N")
        ax.bar(np.arange(len(asz)) + (k - 1.5) * w, np.maximum(s.gap_pct, FLOOR), w, color=C[m] if m != "hibrido" else C["hibrido"], label=names[m].replace("\n", " "))
    ax.set_yscale("log"); ax.set_xticks(range(len(asz))); ax.set_xticklabels(asz); ax.set_xlabel("N"); ax.set_ylabel("gap médio (%)")
    ax.set_title("Ablação: qual vizinhança do fix-and-optimize?"); ax.legend(fontsize=8); ax.grid(axis="y", alpha=.3, which="both")
    fig.tight_layout(); fig.savefig("figures/fig5_ablacao_fo.png", dpi=150); plt.close(fig)
print("figuras ok")

# Fig 6: gap PRIMAL (vs melhor solução conhecida) em ppm -- separa qualidade da solução de qualidade do limite dual
best = df.groupby(["N", "rep"])["obj"].transform("max")
df["gap_primal_ppm"] = 1e6 * (best - df.obj) / best
sp = df.groupby(["N", "metodo"]).gap_primal_ppm.mean().reset_index()
sp.to_csv("results_primal_gap.csv", index=False)
fig, ax = plt.subplots(figsize=(8, 4.2)); w = 0.2
for k, m in enumerate(main):
    s = sp[sp.metodo == m].sort_values("N")
    ax.bar(np.arange(len(sizes)) + (k - 1.5) * w, s.gap_primal_ppm, w, color=C[m], label=L[m])
ax.set_xticks(range(len(sizes))); ax.set_xticklabels(sizes); ax.set_xlabel("N (itens)")
ax.set_ylabel("gap primal médio vs. melhor solução conhecida (ppm)")
ax.set_title("Qualidade PRIMAL: heurística vs. exato vs. híbrido"); ax.legend(fontsize=8); ax.grid(axis="y", alpha=.3)
fig.tight_layout(); fig.savefig("figures/fig6_gap_primal_ppm.png", dpi=150); plt.close(fig)
print(sp.pivot(index="N", columns="metodo", values="gap_primal_ppm").round(2).to_string())
