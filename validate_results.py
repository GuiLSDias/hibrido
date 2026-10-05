"""Audita os arquivos entregues sem resolver nenhum MIP novamente."""
import argparse
import json
import math
from pathlib import Path
from src.generator import from_edges, generate
from src.common import valid, objective


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='.')
    root=Path(ap.parse_args().out)
    collection=json.loads((root/'data/instances.json').read_text(encoding='utf-8'))
    results=json.loads((root/'results.json').read_text(encoding='utf-8'))
    instances={(g['N'],g['rep']):g for g in collection['instances']}
    meta=results['metadata']
    assert len(instances)==len(meta['sizes'])*meta['reps'], 'Faltam instâncias'
    for key,g in instances.items():
        inst=from_edges(g['N'],g['edges'])
        assert generate(g['N'],g['seed'],g['p'])['edges']==inst['edges'], key
        clique=g['clique']
        assert len(set(clique))==g['clique_lb']
        edges=set(map(tuple,inst['edges']))
        assert all(tuple(sorted((u,v))) in edges for i,u in enumerate(clique) for v in clique[i+1:])
    for key,run in results['runs'].items():
        row=run['row'];g=instances[(row['N'],row['rep'])]
        inst=from_edges(g['N'],g['edges'])
        assert valid(inst,run['colors']), key
        assert objective(run['colors'])==row['obj'], key
        assert g['clique_lb']<=row['bound']<=row['obj']+1e-5, key
        if row['optimal']:
            assert row['status']=='Optimal' and row['metodo']!='heuristica' and not row['fallback'], key
            assert math.ceil(row['bound']-1e-6)==row['obj'], key
        if row['metodo'].startswith('hibrido') or row['metodo']=='exato+warm':
            assert row['warm_accepted'], key
        tr=run['trace']
        assert tr and tr[-1]['cores']==row['obj'], key
        assert all(t['cores']>=row['obj'] and 0<=t['t']<=row['tempo_s']+.02 for t in tr), key
        assert all(a['cores']>b['cores'] and a['t']<=b['t'] for a,b in zip(tr,tr[1:])), key
        assert all(s['after']<=s['before'] for s in run['fo_log']), key
        assert row['fo_imp']==sum(s['after']<s['before'] for s in run['fo_log']), key
    for n,rep in instances:
        for method in ['heuristica','exato','exato+warm','hibrido']:
            assert f'{n}_{rep}_{method}' in results['runs'], (n,rep,method)
    print(f'OK: {len(instances)} grafos reproduzidos, cliques verificadas e {len(results["runs"])} execuções auditadas.')

if __name__=='__main__':
    main()
