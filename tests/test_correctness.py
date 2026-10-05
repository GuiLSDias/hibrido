"""Testes independentes: cromático por enumeração em grafos pequenos e casos clássicos."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.generator import from_edges, generate
from src.common import valid, objective, clique_bound
from src.heuristic import tabu_search
from src.exact import solve_mip
from src.hybrid import hybrid, neighborhood


def chromatic_bruteforce(g):
    colors = [-1]*g['n']
    def search(v, k):
        if v == g['n']:
            return True
        for c in range(k):
            if all(colors[u] != c for u in g['adj'][v] if u < v):
                colors[v] = c
                if search(v+1,k):
                    return True
        colors[v] = -1
        return False
    for k in range(1,g['n']+1):
        colors[:] = [-1]*g['n']
        if search(0,k):
            return k


class Correctness(unittest.TestCase):
    def test_exact_vs_independent_enumeration(self):
        graphs = [from_edges(1,[]),from_edges(5,[]),
                  from_edges(5,[(u,v) for u in range(5) for v in range(u+1,5)]),
                  from_edges(5,[(i,(i+1)%5) for i in range(5)]),
                  from_edges(6,[(u,v) for u in range(3) for v in range(3,6)])]
        graphs += [generate(7, s, p) for s in [7,17,27] for p in [.2,.5,.8]]
        for g in graphs:
            expected = chromatic_bruteforce(g)
            r = solve_mip(g,3)
            self.assertTrue(r['optimal'], r['status'])
            self.assertTrue(valid(g,r['colors']))
            self.assertEqual(r['obj'],expected)
            self.assertLessEqual(r['bound'],expected+1e-6)
            self.assertLessEqual(clique_bound(g)[0],expected)
            t = tabu_search(g,.03)
            self.assertTrue(valid(g,t['colors']))
            self.assertGreaterEqual(t['obj'],expected)
    def test_warm_and_fixed_vertices(self):
        g = generate(14,700,.5)
        t = tabu_search(g,.05)
        x = t['colors']
        for strategy in ['critical','random','mix']:
            free = neighborhood(g,x,6,strategy,np.random.default_rng(1))
            r = solve_mip(g,2,x,free)
            self.assertTrue(r['warm_accepted'])
            self.assertFalse(r['optimal']) # prova local nunca vira prova global
            # Normalização muda rótulos: checar partição dos vértices fixados.
            fixed = sorted(set(range(g['n']))-set(free))
            for u in fixed:
                for v in fixed:
                    self.assertEqual(x[u]==x[v],r['colors'][u]==r['colors'][v])
            self.assertTrue(valid(g,r['colors']))
            self.assertLessEqual(r['obj'],t['obj'])
        full = solve_mip(g,3,x)
        self.assertTrue(full['warm_accepted'])
        self.assertTrue(full['optimal'])
        self.assertEqual(full['obj'],chromatic_bruteforce(g))
    def test_generator_and_budget(self):
        self.assertEqual(generate(10,123)['edges'],generate(10,123)['edges'])
        self.assertNotEqual(generate(10,123)['edges'],generate(10,124)['edges'])
        r = hybrid(generate(30,3000),.3)
        self.assertTrue(valid(generate(30,3000),r['colors']))
        self.assertLess(r['time'],.6)
        self.assertTrue(all(a['cores'] >= b['cores'] and a['t'] <= b['t']
                            for a,b in zip(r['trace'],r['trace'][1:])))
    def test_fix_and_optimize_can_eliminate_a_color(self):
        g = from_edges(4,[(0,1),(1,2),(2,3),(3,0)])
        # Última classe livre pode se unir à outra classe sem conflitos.
        x = np.array([0,2,0,1])
        r = solve_mip(g,2,x,[1])
        self.assertEqual(r['obj'],2)
        self.assertTrue(valid(g,r['colors']))
        self.assertTrue(r['subproblem_optimal'])
        self.assertFalse(r['optimal'])

    def test_invalid_start(self):
        with self.assertRaises(ValueError):
            solve_mip(from_edges(2,[(0,1)]),1,np.array([0,0]))

if __name__ == '__main__':
    unittest.main()
