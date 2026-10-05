# TP-III — Busca Tabu + HiGHS na Coloração de Grafos

Versão corrigida do projeto híbrido. Mantém o **problema do TP-II do grupo: coloração mínima de grafos**, aplicado ao agendamento de provas. A Busca Tabu do TP-I é reaproveitada como ideia e adaptada para recoloração de vértices. O modelo inteiro preserva as variáveis `x[v,c]` e `y[c]` do TP-II.

O pacote contém código executável, instâncias completas, resultados reais, colorações válidas, gráficos, relatório e apresentação HTML offline. Os resultados são específicos do ambiente registrado em `results.json`.

## Comece aqui

1. Extraia o ZIP e abra `index.html` no navegador: apresentação, resultados e metodologia. Use as setas ← → e o botão de tela cheia.
2. Leia `RELATORIO.md` para as respostas baseadas nos resultados.
3. Leia `ROTEIRO.md` para estudar a apresentação.
4. Para executar, instale Python 3.10 ou superior e as dependências:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python run_experiments.py --T 20 --reps 3
python validate_results.py
python analyze.py
```

A execução completa leva vários minutos; cada abordagem tem limite de até 20 s por grafo e pode encerrar antes. Execute os comandos na pasta do projeto. Para preservar os resultados entregues durante novos testes, use uma pasta de saída:

```bash
python run_experiments.py --T 5 --reps 1 --sizes 10 20 30 --ablation-sizes 30 --out teste
python analyze.py --out teste
```

A análise grava dados e figuras na pasta de saída. Para usar a apresentação nessa pasta, copie `index.html`, `style.css` e `app.js` para ela.

## Atendimento aos requisitos recuperados do TP-III

| Requisito | Implementação |
|---|---|
| Mesmo problema do TP-II | Coloração mínima de grafos; `src/exact.py` |
| Reutilização de heurística do TP-I adaptada | Busca Tabu para recoloração; `src/heuristic.py` |
| Gerador parametrizado por N e seed documentada | G(N,p); `src/generator.py`, `data/instances.json` |
| Cinco ou seis tamanhos crescentes | 10, 15, 20, 30, 40, 60 vértices |
| Mesmo limite total T | 20 s por abordagem; preparação e fases contabilizadas |
| Warm start | Coloração viável convertida em vetor completo x/y e enviada por `setSolution` |
| Estratégia avançada | Fix-and-Optimize com janela de vértices críticos |
| Explicar fixações e decisões livres | Menor classe e vizinhos críticos livres; demais vértices fixos |
| Heurística, exato e híbrido | Quatro configurações principais, incluindo controle de warm start |
| Código e gráficos comparativos | Scripts, sete gráficos, CSV/JSON e HTML |
| Quatro perguntas experimentais | `RELATORIO.md`, slide 8 e tabelas por réplica |

## Estrutura

- `src/generator.py`: geração de grafos simples e seeds.
- `src/common.py`: DSATUR, clique gulosa, validação e avaliação.
- `src/heuristic.py`: Busca Tabu com aspiração e diversificação.
- `src/exact.py`: modelo inteiro de coloração com HiGHS.
- `src/hybrid.py`: warm start, Fix-and-Optimize e MIP completo.
- `run_experiments.py`: comparação independente e sequencial; salva após cada execução.
- `analyze.py`: recalcula métricas, figuras, relatório e dados da apresentação.
- `tests/test_correctness.py`: comparação com enumeração independente e verificação de fixações.
- `data/`: 18 grafos DIMACS `.col` e descrição completa JSON.
- `results.csv`: uma linha por execução, com status e fases.
- `results.json`: ambiente, coloração de cada vértice, traces e logs de vizinhanças.
- `results_metrics.csv`, `results_summary.csv`: métricas detalhadas e médias.
- `analysis.json`, `RELATORIO.md`: respostas e comparações derivadas dos dados.
- `index.html`, `style.css`, `app.js`, `presentation-data.js`: apresentação offline.
- `execution.log`: saída da execução entregue.
- `VALIDACAO.md`: verificações realizadas.

## Instâncias

Grafo aleatório simples G(N,p), com p=0,5 fixo. Cada par não ordenado de vértices recebe uma aresta de forma independente. Não há laços ou arestas repetidas.

- N ∈ {10, 15, 20, 30, 40, 60}.
- Réplicas r ∈ {0, 1, 2}.
- Seed = 2026 + 1000r + N.
- NumPy `default_rng`, com versão registrada. O JSON preserva todas as arestas, permitindo reprodução independente do gerador.
- N significa **número de vértices**. Uma cor pode representar um horário de prova.

Os menores casos verificam solução e prova rápidas; os maiores investigam onde o solver deixa de provar dentro de T. Os tamanhos foram escolhidos após testes exploratórios curtos, separados dos resultados principais. A dificuldade não depende exclusivamente de N.

## Modelo matemático

Paleta de K cores obtida por uma coloração DSATUR viável. Como existe solução com K cores, restringir a paleta a K não exclui o ótimo.

Minimizar Σc y[c], com:

1. Σc x[v,c] = 1 para cada vértice v.
2. x[u,c] + x[v,c] ≤ y[c] para cada aresta {u,v} e cor c.
3. x[v,c] ≤ y[c] para todos os vértices, incluindo isolados.
4. y[c] ≥ y[c+1], reduzindo a simetria entre cores.
5. x e y binários.

Adicionalmente, Σc y[c] ≥ tamanho de uma clique gulosa encontrada. Essa clique não precisa ser máxima: seus vértices são mutuamente adjacentes e exigem cores diferentes. No modelo completo, x[v,c]=0 para c>v é uma quebra de simetria segura, pois qualquer coloração pode ser renomeada pela primeira ocorrência das cores. Ela é desativada no F&O para não conflitar com as fixações.

O HiGHS executa branch-and-cut, uma thread, seed interna 1, gaps relativo e absoluto iguais a zero. A prova refere-se à minimização do número de cores no modelo completo.

## Busca Tabu adaptada

A solução é um vetor `colors[v]`. DSATUR cria uma coloração inicial válida. Para tentar k−1 cores, a menor classe é removida e seus vértices são recoloridos, podendo criar conflitos.

Um movimento muda a cor de um vértice que participa de conflitos. O custo é a mudança no total de arestas monocromáticas. O par (vértice, cor antiga) fica temporariamente tabu, com tenure adaptado ao número de vértices conflitantes e uma parcela aleatória. A aspiração aceita uma proibição quando o movimento melhora o menor número de conflitos dessa tentativa. Após estagnação, a busca reinicia a tentativa, com novos desempates e atribuições.

Uma solução só vira incumbente quando tem **zero conflitos**. A heurística nunca devolve uma coloração inválida. Pode terminar cedo se a quantidade de cores alcança o limite da clique. Isso permite uma certificação combinatória externa, mas a coluna `optimal` do experimento é reservada ao status ótimo do **solver global**.

## Quatro configurações e orçamento

| Método | Etapas dentro de T |
|---|---|
| Heurística pura | Busca Tabu por até T |
| Exato puro | Pré-processamento + MIP global por até T |
| Exato + warm start | Tabu até 0,1T + MIP global no restante |
| Híbrido | Tabu até 0,1T + F&O até 0,4T + MIP global no restante |

DSATUR limita a paleta de todos os MIPs. No exato puro, essa coloração **não é enviada ao solver como incumbente**. Se o solver não devolver uma solução viável, ela é usada como saída de segurança, com `fallback=True`, sem marcar prova. O warm start usa o vetor completo x/y da solução da Tabu.

O tempo de construção do modelo é descontado antes de definir o `time_limit` do HiGHS. Tempo de extração e pequenos excessos internos de relógio são registrados; o máximo observado aparece no relatório. Não se força uma fase a consumir seu orçamento quando ela já terminou. Não se compartilham incumbentes ou provas entre as abordagens. As execuções são sequenciais para evitar concorrência deliberada por CPU.

## Fix-and-Optimize: inteligência da seleção

1. Selecionar a menor classe de cor e renomeá-la para a última cor. Isso permite desligar seu y sem contrariar a ordenação das cores.
2. Liberar todos os seus vértices.
3. Preencher a janela com vizinhos dessa classe, priorizando maior saturação e grau.
4. Fixar x dos demais vértices na coloração corrente e otimizar Σy com HiGHS.
5. Aceitar uma coloração válida somente se reduz cores.

K começa em aproximadamente 40% de N, mínimo 5 e máximo N. A classe obrigatória pode ultrapassar K. Cada subproblema tem no máximo 2 s e o restante da fase. Se prova seu ótimo em menos de 1 s, K aumenta 25%; se não prova, K reduz 30%, respeitando limites. Após quatro tentativas sem melhora, o tempo restante vai ao modelo completo.

A ablação preserva a classe obrigatória e altera os vértices adicionais: `critical` (vizinhança, saturação, grau), `random` e `mix` (metade críticos, metade aleatórios). Aplica-se a N=30,40,60. A configuração exato + warm start permite separar o efeito da solução inicial do custo adicional do F&O.

**Um limite dual do MIP com vértices fixados não é um limite inferior global.** Por isso os limites locais são descartados para prova e cálculo de gap do problema completo. O status ótimo do F&O é salvo apenas em `subproblem_optimal` nos logs.

## Métricas corretas para minimização

- UB: quantidade de cores de uma coloração válida.
- LB: limite inferior válido, por clique ou dual do MIP **completo**.
- LB ≤ χ(G) ≤ UB.
- Gap próprio: 100(UB−LB)/UB.
- Gap de certificado de referência: 100(UB−LB_ref)/UB, com LB_ref igual ao maior teto seguro dos limites globais observados naquela instância. É comparável entre métodos.
- Excesso primal: 100(UB−melhor observado)/melhor observado. Zero não implica prova de ótimo.
- Prova: status Optimal do modelo completo, solução validada e sem fallback.
- Tempo total: todas as fases e preparação. Tempo de prova: apenas execuções certificadas, exibidas separadamente.

LB_ref e melhor observado são calculados **depois** dos experimentos, nunca usados para ajudar uma abordagem. A melhor solução observada pode continuar acima do número cromático desconhecido.

## Referências e origem

- Modelo e problema do TP-II do grupo: https://github.com/GabrielMarcelini/Trabalho-Pratico-II---Metodos-Exatos
- HiGHS, projeto oficial e solver MIP: https://highs.dev/
- API oficial Python / exemplos de callbacks: https://github.com/ERGO-Code/HiGHS/blob/master/examples/call_highs_from_python.py
- Hertz, A.; de Werra, D. Using tabu search techniques for graph coloring. *Computing*, 39, 345–351, 1987. DOI: 10.1007/BF02239976. A implementação é uma adaptação própria da ideia TabuCol, não uma reprodução literal do artigo.

As instâncias Mycielski do TP-II não são os experimentos principais deste pacote: o TP-III pede um gerador parametrizado e tamanhos crescentes. O problema e a base da formulação são os mesmos; as instâncias são novas.
