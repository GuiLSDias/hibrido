# TP-III — Heurística + Método Exato (Mochila 0/1)

Hibridização da **Busca Tabu** (TP-I, portada de JavaScript para Python) com **branch-and-cut (HiGHS)** na **Mochila 0/1**, usando **warm start** e **Fix-and-Optimize**, comparada com a heurística pura e o exato puro sob o mesmo orçamento de tempo.

> **Premissa:** assumi que o problema do TP-II é a Mochila 0/1, o mesmo do `heuristica.zip` (TP-I). Se o grupo usou outro problema, o gerador, a heurística e o modelo MIP precisam ser adaptados.
> Do TP-I foi portada apenas a Busca Tabu; o Algoritmo Genético não foi usado.

## Estrutura

```
hibrido/
├── src/
│   ├── generator.py        # gerador parametrizado por N, com semente documentada
│   ├── common.py           # avaliação, guloso p/w, limite de Dantzig, relógio
│   ├── heuristic.py        # Busca Tabu (flip + swap vetorizado, aspiração, diversificação)
│   ├── exact.py            # MIP no HiGHS: warm start (setSolution) e subproblemas com variáveis livres
│   └── hybrid.py           # warm start + fix-and-optimize + exato com incumbente
├── run_experiments.py      # roda tudo; gera results.csv, results.json, data/instances.json
├── analyze.py              # gera figures/*.png, results_summary.csv, results_primal_gap.csv
├── data/instances.json     # parâmetros do gerador e semente de cada instância
├── figures/                # gráficos comparativos (fig1..fig6)
├── index.html, style.css, app.js   # apresentação (slides) + tabela de resultados
├── requirements.txt
└── README.md
```

## Como executar

```bash
pip install -r requirements.txt
python run_experiments.py --T 20 --reps 3     # ~17 min em 1 núcleo
python analyze.py                              # figuras e tabelas
# abra index.html no navegador (setas ← → navegam pelos slides)
```

## Instâncias

Fortemente correlacionadas (Pisinger): `w_i ~ U{1..R}`, `p_i = w_i + R/10`, `C = ⌊0,5·Σw⌋`, `R = 100000`.
Semente: `seed = 2026 + 1000·réplica + N` (3 réplicas por tamanho).

| N | seed (réplicas 0/1/2) |
|---|---|
| 25 | 2051 / 3051 / 4051 |
| 50 | 2076 / 3076 / 4076 |
| 100 | 2126 / 3126 / 4126 |
| 200 | 2226 / 3226 / 4226 |
| 400 | 2426 / 3426 / 4426 |
| 800 | 2826 / 3826 / 4826 |

(Todos os parâmetros, incluindo `C` e o limite de Dantzig, estão em `data/instances.json`.)
Com T = 20 s, N = 25 resolve em ~0,02 s e N = 800 não fecha o gap em nenhuma réplica.

## Abordagens (todas com T = 20 s de relógio)

1. **Heurística pura** — Busca Tabu usando T inteiro.
2. **Exato puro** — MIP no HiGHS 1.15, 1 thread, prova de ótimo (gap absoluto < 1, pois os lucros são inteiros).
3. **Exato + warm start** — Tabu por 0,1·T, solução injetada como incumbente, exato no restante. Serve para isolar o efeito do warm start.
4. **Híbrido** — warm start (0,1·T) → **Fix-and-Optimize** (até 0,4·T) → exato completo com o melhor incumbente.

O tempo do warm start e do F&O está dentro de T.

### Fix-and-Optimize (decisão de projeto)

- Calcula o preço-sombra λ da capacidade na relaxação linear (razão p/w do item crítico).
- Ordena os itens por `|p_i − λ·w_i|` (custo reduzido): os menores são os "incertos" da relaxação.
- Deixa livre uma janela de K itens desse ranking, fixa o resto no valor do incumbente e resolve o subproblema reduzido (capacidade residual) exatamente.
- K adaptativo (×1,25 se fecha rápido; ×0,7 se estoura 2 s). A janela desliza K/2 por iteração; encerra após várias passadas sem melhora.
- Ablação: `rc` (custo reduzido), `random` (aleatório) e `mix` (metade rc, metade aleatória).

## Resultados (média de 3 réplicas)

Ótimo provado em T = 20 s (réplicas provadas / 3):

| N | Exato | Exato + warm | Híbrido | Heurística (gap primal, ppm) |
|---|:--:|:--:|:--:|:--:|
| 25 | 3/3 | 3/3 | 3/3 | 0,00 |
| 50 | 3/3 | 3/3 | 3/3 | 0,00 |
| 100 | 3/3 | 3/3 | 3/3 | 0,51 |
| 200 | 3/3 | 3/3 | 3/3 | 0,05 |
| 400 | 1/3 | 0/3 | 0/3 | 0,18 |
| 800 | 0/3 | 0/3 | 0/3 | 0,00 |

O gap primal é medido contra a melhor solução conhecida na instância. Tabela completa: `results_summary.csv`; figuras em `figures/`.
Em N = 400 e 800 o gap relativo ao limite dual é ~0,03 %, e vem do limite, não da solução.

Tempo médio até terminar: N ≤ 100: exato puro 0,02–0,34 s contra ~2,0–2,5 s do híbrido (o warm start fixo de 2 s domina). N = 200: exato 1,2–4,4 s contra 2,1–4,0 s do híbrido.

## Respostas às perguntas

1. **A partir de que tamanho o exato deixa de fechar o gap?** Entre N = 200 (3/3 provados, 1,2–4,4 s) e N = 400 (1/3, em 10,8 s). Em N = 800, 0/3.
2. **O híbrido empurra esse limite?** Não neste experimento. Em N = 400 o híbrido provou 0/3 e o exato puro 1/3, então o ganho foi de zero tamanhos. Com 3 réplicas e um solver de 1 thread, não dá para dizer que o híbrido seja pior; a diferença de 1 réplica pode ser variabilidade do caminho de busca do HiGHS.
3. **A heurística já iguala o híbrido?** Em qualidade de solução, sim, desde o menor tamanho: gap primal ≤ 0,51 ppm (a Tabu errou por pouco em N = 100, 200 e 400, e acertou o melhor valor conhecido nas demais). O que o híbrido acrescenta é a prova de otimalidade, e só até N = 200, onde o exato puro também prova. Em N ≥ 400 o ganho de combinar desaparece.
4. **A estratégia acelerou o solver?**
   - *Warm start:* sim, no sentido de que, com o incumbente ótimo, o HiGHS prova o ótimo em ~0,02 s em 2 das 3 réplicas de N = 200 (1,2 s na terceira). Mas os 2 s gastos para obter o incumbente superam o que o exato puro leva, então o tempo total não melhorou.
   - *Fix-and-Optimize:* não fez diferença. Houve 0 a 2 melhorias por execução e mínimas (ex.: +1 unidade de lucro em N = 400); em N = 800 nenhuma. As três vizinhanças (rc, aleatório, mix) deram resultados idênticos, pois não havia melhora a encontrar.

   **Nossa leitura do porquê:** (i) a mochila tem uma só restrição e a Busca Tabu já entrega solução a ≤ 0,5 ppm do ótimo, então o F&O não tem o que melhorar; (ii) o gargalo do exato nessas instâncias é o **limite dual** (árvore de B&B com poda fraca por causa da correlação forte), e F&O só melhora o limite primal; (iii) fixar variáveis não tira nada da árvore do problema completo. Esperamos ganho do F&O em problemas com muitas restrições/estrutura (multidimensional, GAP, lot-sizing), onde a heurística costuma deixar um gap primal maior.

## Limitações

- 1 thread, HiGHS (não Gurobi/CPLEX), T = 20 s, 3 réplicas por tamanho: resultados são indicativos, não estatisticamente conclusivos.
- A transição 200 → 400 é abrupta e muito dependente da instância (em um teste exploratório com R = 10000 e semente 1, N = 800 fechou em ~0,3 s enquanto N = 400 estourou 20 s, ou seja, a dificuldade não é monótona em N). Outro gerador ou solver mudaria o ponto.
- O ótimo "provado" usa gap absoluto < 1 (válido porque p é inteiro).
