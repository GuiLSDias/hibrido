"""Executa sequencialmente os métodos para evitar competição por CPU.
Cada chamada recebe T incluindo construção do modelo e todas as fases.
"""
import argparse
import csv
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
import highspy
import numpy as np
from src.generator import generate, seed_for, SIZES, DENSITY
from src.common import clique_bound, valid, objective
from src.heuristic import tabu_search
from src.exact import solve_mip
from src.hybrid import hybrid

FIELDS = ['N','rep','seed','p','arestas','metodo','obj','bound','optimal','tempo_s',
          'solver_s','warm_s','fo_s','fo_sub','fo_imp','warm_accepted','fallback','status','T']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--T',type=float,default=20)
    ap.add_argument('--reps',type=int,default=3)
    ap.add_argument('--sizes',type=int,nargs='+',default=SIZES)
    ap.add_argument('--density',type=float,default=DENSITY)
    ap.add_argument('--ablation-sizes',type=int,nargs='*',default=[30,40,60])
    ap.add_argument('--out',default='.')
    a = ap.parse_args()
    if a.T <= 0 or a.reps < 1 or any(n < 1 for n in a.sizes):
        ap.error('T, reps e tamanhos devem ser positivos')
    out = Path(a.out); (out/'data').mkdir(parents=True,exist_ok=True)
    rows, details, instances = [], {}, []
    metadata = {'T':a.T,'reps':a.reps,'sizes':a.sizes,'density':a.density,
                'seed_rule':'2026 + 1000*rep + N','highs':highspy.Highs().version(),
                'python':platform.python_version(),'numpy':np.__version__,
                'platform':platform.platform(),'threads':1,'solver_seed':1,
                'date_utc':datetime.now(timezone.utc).isoformat()}
    def save():
        with (out/'results.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=FIELDS)
            writer.writeheader(); writer.writerows(rows)
        (out/'results.json').write_text(json.dumps({'metadata':metadata,'runs':details},indent=2),encoding='utf-8')
        (out/'data/instances.json').write_text(json.dumps({'metadata':metadata,'instances':instances},indent=2),encoding='utf-8')
    for n in a.sizes:
        for rep in range(a.reps):
            seed=seed_for(n,rep); inst=generate(n,seed,a.density)
            lb,clique=clique_bound(inst)
            instances.append({'N':n,'rep':rep,'seed':seed,'p':a.density,
                              'edges':inst['edges'],'clique_lb':lb,'clique':clique})
            dimacs = [f'c G(N,p), N={n}, p={a.density}, seed={seed}',f'p edge {n} {len(inst["edges"])}']
            dimacs += [f'e {u+1} {v+1}' for u,v in inst['edges']]
            (out/f'data/g{n}_r{rep}.col').write_text('\n'.join(dimacs)+'\n',encoding='utf-8')
            methods=['heuristica','exato','exato+warm','hibrido']
            if n in a.ablation_sizes:
                methods += ['hibrido_random','hibrido_mix']
            for method in methods:
                if method=='heuristica':
                    r=tabu_search(inst,a.T,seed=1)
                    r.update(bound=lb,optimal=False,status='Heuristic (no solver certificate)')
                elif method=='exato':
                    r=solve_mip(inst,a.T,seed=1)
                else:
                    strategy = method.removeprefix('hibrido_') if method.startswith('hibrido_') else 'critical'
                    r=hybrid(inst,a.T,strategy=strategy,seed=1,warm_only=method=='exato+warm')
                assert valid(inst,r['colors']), (n,rep,method,'coloração inválida')
                assert objective(r['colors'])==r['obj']
                assert r['bound'] <= r['obj']+1e-5, (n,rep,method,'limite inválido')
                row=dict(N=n,rep=rep,seed=seed,p=a.density,arestas=len(inst['edges']),metodo=method,
                         obj=r['obj'],bound=r['bound'],optimal=r['optimal'],tempo_s=r['time'],
                         solver_s=r.get('solver_time',0),warm_s=r.get('warm_time',0),fo_s=r.get('fo_time',0),
                         fo_sub=len(r.get('fo_log',[])),
                         fo_imp=sum(s['after']<s['before'] for s in r.get('fo_log',[])),
                         warm_accepted=r.get('warm_accepted',False),fallback=r.get('fallback',False),
                         status=r['status'],T=a.T)
                rows.append(row)
                details[f'{n}_{rep}_{method}']={'colors':r['colors'].tolist(),'trace':r['trace'],
                                              'fo_log':r.get('fo_log',[]),'row':row}
                save()
                print(f'N={n:2} r={rep} {method:16} cores={r["obj"]:2} LB={r["bound"]:.2f} '
                      f'prova={r["optimal"]} t={r["time"]:.3f}s',flush=True)
    print('Experimentos concluídos.',flush=True)

if __name__=='__main__':
    main()
