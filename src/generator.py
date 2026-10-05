"""Gerador parametrizado de instâncias da Mochila 0/1 (fortemente correlacionadas).

Parâmetros: N (nº de itens), seed, R (faixa dos pesos), tipo.
  w_i ~ U{1..R};  p_i = w_i + R/10  (strongly correlated, Pisinger 2005);  C = floor(0.5 * sum(w)).
Esse tipo é o mais difícil para B&B/ MIP: a razão p/w é quase constante e os limites LP são fracos.
"""
import numpy as np

SEED_BASE = 2026          # semente-mestra documentada
SIZES = [25, 50, 100, 200, 400, 800]
R_DEFAULT = 100_000


def seed_for(n: int, rep: int = 0) -> int:
    """Semente determinística por (N, réplica): SEED_BASE + 1000*rep + N."""
    return SEED_BASE + 1000 * rep + n


def generate(n: int, seed: int, R: int = R_DEFAULT, kind: str = "sc", cap_frac: float = 0.5):
    rng = np.random.default_rng(seed)
    w = rng.integers(1, R + 1, n).astype(np.int64)
    if kind == "sc":      # strongly correlated
        p = w + R // 10
    elif kind == "ss":    # subset-sum
        p = w.copy()
    elif kind == "un":    # uncorrelated
        p = rng.integers(1, R + 1, n).astype(np.int64)
    else:
        raise ValueError(kind)
    C = int(cap_frac * w.sum())
    return {"n": n, "seed": seed, "R": R, "kind": kind, "cap_frac": cap_frac,
            "w": w, "p": p, "C": C}
