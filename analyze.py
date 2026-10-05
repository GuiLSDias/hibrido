"""Recalcula tabelas, gráficos e apresentação a partir dos resultados reais."""
import argparse
import json
import math
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

MAIN=['heuristica','exato','exato+warm','hibrido']
NAMES={'heuristica':'Busca Tabu','exato':'Exato','exato+warm':'Exato + warm start',
       'hibrido':'Híbrido (críticos)','hibrido_random':'Híbrido (aleatório)','hibrido_mix':'Híbrido (misto)'}
COLORS={'heuristica':'#a68cf5','exato':'#ff8279','exato+warm':'#ffd17a','hibrido':'#71e0cf',
        'hibrido_random':'#77aaff','hibrido_mix':'#f09bc6'}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default='.')
    a=ap.parse_args(); root=Path(a.out)
    df=pd.read_csv(root/'results.csv')
    detail=json.loads((root/'results.json').read_text(encoding='utf-8'))
    meta=detail['metadata']
    df['optimal']=df['optimal'].astype(str).str.lower().eq('true')
    groups=df.groupby(['N','rep'])
    df['best_known']=groups['obj'].transform('min')
    # MINIMIZAÇÃO: limite dual é INFERIOR. O teto de um LB válido também é válido.
    df['reference_lb']=groups['bound'].transform('max').map(lambda x:math.ceil(x-1e-6))
    if (df['reference_lb']>df['best_known']).any():
        raise ValueError('LB de referência contradiz uma solução viável')
    df['gap_certificate_pct']=100*(df['obj']-df['reference_lb'])/df['obj']
    df['gap_primal_pct']=100*(df['obj']-df['best_known'])/df['best_known']
    df['own_gap_pct']=100*(df['obj']-df['bound'])/df['obj']
    df.to_csv(root/'results_metrics.csv',index=False)
    summary=df.groupby(['N','metodo']).agg(replicas=('obj','size'),provadas=('optimal','sum'),
        cores_media=('obj','mean'),tempo_medio_s=('tempo_s','mean'),tempo_min_s=('tempo_s','min'),
        tempo_max_s=('tempo_s','max'),gap_certificado_pct=('gap_certificate_pct','mean'),
        gap_primal_pct=('gap_primal_pct','mean'),fo_melhorias=('fo_imp','sum')).reset_index()
    summary.to_csv(root/'results_summary.csv',index=False)
    sizes=sorted(df.N.unique()); T=meta['T']; figs=root/'figures'; figs.mkdir(exist_ok=True)
    plt.rcParams.update({'figure.facecolor':'#111827','axes.facecolor':'#111827',
        'text.color':'#e5e7eb','axes.labelcolor':'#e5e7eb','xtick.color':'#cbd5e1',
        'ytick.color':'#cbd5e1','axes.edgecolor':'#6b7280','grid.color':'#374151',
        'font.size':11,'savefig.facecolor':'#111827'})
    def line_plot(column,title,ylabel,filename,methods=MAIN,log=False):
        fig,ax=plt.subplots(figsize=(9,4.2))
        for m in methods:
            s=summary[summary.metodo==m].sort_values('N')
            if s.empty: continue
            y=100*s.provadas/s.replicas if column=='proof' else s[column]
            ax.plot(s.N,y,'o-',label=NAMES[m],color=COLORS[m],lw=2,ms=5)
        ax.set(xlabel='Número de vértices (N)',ylabel=ylabel,title=title,xticks=sizes)
        if log: ax.set_yscale('log')
        ax.grid(alpha=.5); ax.legend(fontsize=9,ncol=2); fig.tight_layout()
        fig.savefig(figs/filename,dpi=160);plt.close(fig)
    line_plot('proof',f'Prova de ótimo em até {T:g} s','Réplicas com certificado do solver (%)','fig2_otimo_provado.png',MAIN[1:])
    line_plot('gap_certificado_pct','Distância ao limite inferior comum','Gap de certificado (%)','fig1_gap_vs_N.png')
    line_plot('gap_primal_pct','Qualidade frente à melhor solução observada','Excesso de cores (%)','fig6_gap_primal.png')
    line_plot('tempo_medio_s','Tempo total médio (inclui preparação e fases)','Tempo (s)','fig3_tempo_total.png',log=True)
    proof=df[df.optimal].groupby(['N','metodo']).tempo_s.mean().unstack('metodo')
    fig,ax=plt.subplots(figsize=(9,4.2))
    for m in MAIN[1:]:
        if m in proof:
            ax.plot(proof.index,proof[m],'o-',color=COLORS[m],label=NAMES[m])
    ax.set(xlabel='Número de vértices (N)',ylabel='Tempo até prova (s)',title='Tempo de prova: somente execuções que provaram',xticks=sizes)
    ax.set_yscale('log');ax.legend(fontsize=9);ax.grid(alpha=.5);fig.tight_layout()
    fig.savefig(figs/'fig7_tempo_prova.png',dpi=160);plt.close(fig)
    selected=sizes[-3:]
    fig,axs=plt.subplots(1,len(selected),figsize=(13,4),sharey=False)
    axs=np.atleast_1d(axs)
    for ax,n in zip(axs,selected):
        for m in MAIN:
            run=detail['runs'].get(f'{n}_0_{m}')
            if not run: continue
            tr=run['trace']
            if tr:
                xs=[r['t'] for r in tr]+[run['row']['tempo_s']]
                ys=[r['cores'] for r in tr]+[run['row']['obj']]
                ax.step(xs,ys,where='post',label=NAMES[m],color=COLORS[m],lw=1.7)
        ax.set(title=f'N = {n}, réplica 0',xlabel='Tempo (s)',ylabel='Cores do incumbente')
        ax.set_xlim(0,T*1.04);ax.grid(alpha=.5)
    handles,labels=axs[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',ncol=4,fontsize=9)
    fig.suptitle('Convergência: somente colorações válidas, menor é melhor')
    fig.tight_layout(rect=[0,.10,1,.92]);fig.savefig(figs/'fig4_anytime.png',dpi=160);plt.close(fig)
    methods=['exato+warm','hibrido','hibrido_random','hibrido_mix']
    ns=sorted(df.loc[df.metodo=='hibrido_random','N'].unique())
    fig,ax=plt.subplots(figsize=(9,4.2))
    for j,m in enumerate(methods):
        s=summary[(summary.metodo==m)&summary.N.isin(ns)].set_index('N')
        ax.bar([i+(j-1.5)*.19 for i in range(len(ns))],s.reindex(ns).cores_media,
               width=.19,color=COLORS[m],label=NAMES[m])
    ax.set(xticks=range(len(ns)),xticklabels=ns,xlabel='Número de vértices (N)',ylabel='Cores (média)',title='Ablação: warm start e seleção da vizinhança')
    ax.grid(axis='y',alpha=.4);ax.legend(fontsize=9,ncol=2);fig.tight_layout()
    fig.savefig(figs/'fig5_ablacao_fo.png',dpi=160);plt.close(fig)
    comparisons=[]
    for n in sizes:
        part=df[df.N==n].pivot(index='rep',columns='metodo',values='obj')
        comparisons.append({'N':int(n),'iguais':int((part.heuristica==part.hibrido).sum()),'replicas':len(part),
                            'heuristica_melhor':int((part.heuristica<part.hibrido).sum()),
                            'hibrido_melhor':int((part.hibrido<part.heuristica).sum())})
    paired=df[df.metodo.isin(['exato','hibrido'])].pivot(index=['N','rep'],columns='metodo',values='optimal')
    gains=[{'N':int(n),'rep':int(r)} for (n,r),v in paired.iterrows() if v.hibrido and not v.exato]
    losses=[{'N':int(n),'rep':int(r)} for (n,r),v in paired.iterrows() if v.exato and not v.hibrido]
    ex=summary[summary.metodo=='exato'].sort_values('N')
    fail=ex[ex.provadas<ex.replicas]
    if fail.empty:
        transition='O exato provou todas as instâncias; o limite não foi observado na faixa testada.'
    else:
        first=int(fail.iloc[0].N)
        previous=ex[(ex.N<first)&(ex.provadas==ex.replicas)]
        transition=(f'A primeira falha do exato ocorreu em N={first}.' if previous.empty else
                    f'A transição observada está entre N={int(previous.iloc[-1].N)} e N={first}.')
        transition+=' A dificuldade depende também das arestas e da seed.'
    time_comparison=[]
    fo_comparison=[]
    for n in sizes:
        by=summary[summary.N==n].set_index('metodo')
        if all(m in by.index and by.loc[m,'provadas']==by.loc[m,'replicas'] for m in ['exato','hibrido']):
            time_comparison.append({'N':int(n),'exato_s':float(by.loc['exato','tempo_medio_s']),
                                    'hibrido_s':float(by.loc['hibrido','tempo_medio_s']),
                                    'hibrido_mais_rapido':bool(by.loc['hibrido','tempo_medio_s']<by.loc['exato','tempo_medio_s'])})
        if all(m in by.index and by.loc[m,'provadas']==by.loc[m,'replicas'] for m in ['exato+warm','hibrido']):
            fo_comparison.append({'N':int(n),'warm_s':float(by.loc['exato+warm','tempo_medio_s']),
                                  'hibrido_s':float(by.loc['hibrido','tempo_medio_s']),
                                  'hibrido_mais_rapido':bool(by.loc['hibrido','tempo_medio_s']<by.loc['exato+warm','tempo_medio_s'])})
    conclusion={'transition':transition,'proof_gains':gains,'proof_losses':losses,'quality_comparison':comparisons,
                'fo_improvements':int(df[df.metodo=='hibrido'].fo_imp.sum()),
                'time_comparison':time_comparison,'fo_comparison':fo_comparison,
                'runs':len(df),'instances':len(groups),'max_overrun_s':float(max(0,(df.tempo_s-T).max())),
                'main_proof_counts':summary[summary.metodo.isin(MAIN)].to_dict(orient='records')}
    data={'metadata':meta,'summary':summary.to_dict(orient='records'),'runs':detail['runs'],'conclusions':conclusion,'names':NAMES}
    (root/'presentation-data.js').write_text('window.EXPERIMENT = '+json.dumps(data,ensure_ascii=False)+';\n',encoding='utf-8')
    (root/'analysis.json').write_text(json.dumps(conclusion,ensure_ascii=False,indent=2),encoding='utf-8')
    report=['# Resultados reais — Coloração de Grafos','',f'{len(groups)} grafos, {len(df)} execuções, T={T:g} s, HiGHS {meta["highs"]}, uma thread.','',
            '## 1. Quando o exato deixa de fechar o gap?',transition,'',
            '## 2. O híbrido amplia esse limite?',
            f'Ganhos de prova em comparação pareada: {len(gains)}; perdas: {len(losses)}. Instâncias com ganho: {gains}. Instâncias com perda: {losses}.',
            ('Não houve ampliação do limite nas instâncias testadas.' if not gains else 'Houve ganho de prova nas instâncias listadas; consulte a contagem por tamanho para distinguir ganho parcial de ampliação com todas as réplicas.'),
            'Compare também a tabela por tamanho. Três réplicas por tamanho não permitem uma conclusão de superioridade estatística.','',
            '## 3. Quando a heurística iguala o híbrido?',
            *[f'- N={c["N"]}: valores iguais em {c["iguais"]}/{c["replicas"]}; heurística melhor em {c["heuristica_melhor"]}; híbrido melhor em {c["hibrido_melhor"]}.' for c in comparisons],
            '', '## 4. A estratégia acelera o solver?',
            f'O F&O crítico produziu {conclusion["fo_improvements"]} reduções de cores nas execuções principais.',
            ('Não houve ganho primal atribuível à fase F&O neste conjunto.' if conclusion['fo_improvements']==0 else 'Houve melhoria primal na fase F&O; isso não garante aceleração da prova global.'),
            'Tamanhos com menor tempo total médio do híbrido versus exato, quando ambos provaram todas as réplicas: '+str([v['N'] for v in time_comparison if v['hibrido_mais_rapido']])+'.',
            'Tamanhos com menor tempo total médio do híbrido versus warm start sozinho, quando ambos provaram todas as réplicas: '+str([v['N'] for v in fo_comparison if v['hibrido_mais_rapido']])+'. Diferenças pequenas podem refletir variação do solver e da máquina; não isolam uma aceleração causal.',
            'Compare tempo total, contagem de provas e qualidade com exato puro e com exato + warm start. Tempo até prova usa apenas casos provados e possui viés de seleção; não é média de todas as execuções.',
            '', '## Tabela resumida','',
            '| N | Método | Provas | Cores (média) | Tempo total (s) | Gap certificado (%) | Excesso primal (%) |',
            '|---:|---|---:|---:|---:|---:|---:|']
    for r in data['summary']:
        report.append(f'| {r["N"]} | {NAMES[r["metodo"]]} | {r["provadas"]}/{r["replicas"]} | {r["cores_media"]:.2f} | {r["tempo_medio_s"]:.3f} | {r["gap_certificado_pct"]:.2f} | {r["gap_primal_pct"]:.2f} |')
    report += ['', '## Definições e limites','',
        'Minimização: LB ≤ χ(G) ≤ UB. UB é o número de cores da coloração válida. LB é clique ou dual global do MIP.',
        'Gap certificado = 100(UB − LB_ref)/UB; LB_ref é o maior teto numérico seguro dos limites globais observados. É uma referência compartilhada somente após os experimentos.',
        'Excesso primal = 100(UB − melhor observado)/melhor observado. Zero significa igualar a melhor solução observada; não garante ótimo.',
        'A coluna de provas registra certificado do HiGHS no modelo completo. A heurística não recebe certificado de outra abordagem; uma clique do mesmo tamanho pode, separadamente, certificar a coloração.',
        'Limites dos subproblemas F&O não são usados como limites globais. Ótimo local não implica ótimo global.',
        f'Máximo excesso observado sobre T: {conclusion["max_overrun_s"]:.3f} s. Construção, extração e tolerância do solver entram no tempo registrado; não há 20 s adicionais por fase.',
        'Três grafos por tamanho e um ambiente computacional. O teste não estabelece um limiar universal nem superioridade estatística.']
    (root/'RELATORIO.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(json.dumps(conclusion,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
