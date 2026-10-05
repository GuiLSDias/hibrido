# Resultados reais — Coloração de Grafos

18 grafos, 90 execuções, T=20 s, HiGHS 1.15.0, uma thread.

## 1. Quando o exato deixa de fechar o gap?
A transição observada está entre N=40 e N=60. A dificuldade depende também das arestas e da seed.

## 2. O híbrido amplia esse limite?
Ganhos de prova em comparação pareada: 0; perdas: 0. Instâncias com ganho: []. Instâncias com perda: [].
Não houve ampliação do limite nas instâncias testadas.
Compare também a tabela por tamanho. Três réplicas por tamanho não permitem uma conclusão de superioridade estatística.

## 3. Quando a heurística iguala o híbrido?
- N=10: valores iguais em 3/3; heurística melhor em 0; híbrido melhor em 0.
- N=15: valores iguais em 3/3; heurística melhor em 0; híbrido melhor em 0.
- N=20: valores iguais em 3/3; heurística melhor em 0; híbrido melhor em 0.
- N=30: valores iguais em 3/3; heurística melhor em 0; híbrido melhor em 0.
- N=40: valores iguais em 3/3; heurística melhor em 0; híbrido melhor em 0.
- N=60: valores iguais em 3/3; heurística melhor em 0; híbrido melhor em 0.

## 4. A estratégia acelera o solver?
O F&O crítico produziu 0 reduções de cores nas execuções principais.
Não houve ganho primal atribuível à fase F&O neste conjunto.
Tamanhos com menor tempo total médio do híbrido versus exato, quando ambos provaram todas as réplicas: [40].
Tamanhos com menor tempo total médio do híbrido versus warm start sozinho, quando ambos provaram todas as réplicas: []. Diferenças pequenas podem refletir variação do solver e da máquina; não isolam uma aceleração causal.
Compare tempo total, contagem de provas e qualidade com exato puro e com exato + warm start. Tempo até prova usa apenas casos provados e possui viés de seleção; não é média de todas as execuções.

## Tabela resumida

| N | Método | Provas | Cores (média) | Tempo total (s) | Gap certificado (%) | Excesso primal (%) |
|---:|---|---:|---:|---:|---:|---:|
| 10 | Exato | 3/3 | 4.00 | 0.010 | 0.00 | 0.00 |
| 10 | Exato + warm start | 3/3 | 4.00 | 0.003 | 0.00 | 0.00 |
| 10 | Busca Tabu | 0/3 | 4.00 | 0.000 | 0.00 | 0.00 |
| 10 | Híbrido (críticos) | 3/3 | 4.00 | 0.034 | 0.00 | 0.00 |
| 15 | Exato | 3/3 | 5.00 | 0.026 | 0.00 | 0.00 |
| 15 | Exato + warm start | 3/3 | 5.00 | 0.010 | 0.00 | 0.00 |
| 15 | Busca Tabu | 0/3 | 5.00 | 0.001 | 0.00 | 0.00 |
| 15 | Híbrido (críticos) | 3/3 | 5.00 | 0.033 | 0.00 | 0.00 |
| 20 | Exato | 3/3 | 5.67 | 0.063 | 0.00 | 0.00 |
| 20 | Exato + warm start | 3/3 | 5.67 | 1.378 | 0.00 | 0.00 |
| 20 | Busca Tabu | 0/3 | 5.67 | 13.334 | 0.00 | 0.00 |
| 20 | Híbrido (críticos) | 3/3 | 5.67 | 1.399 | 0.00 | 0.00 |
| 30 | Exato | 3/3 | 7.00 | 0.521 | 0.00 | 0.00 |
| 30 | Exato + warm start | 3/3 | 7.00 | 2.324 | 0.00 | 0.00 |
| 30 | Busca Tabu | 0/3 | 7.00 | 20.000 | 0.00 | 0.00 |
| 30 | Híbrido (críticos) | 3/3 | 7.00 | 2.366 | 0.00 | 0.00 |
| 30 | Híbrido (misto) | 3/3 | 7.00 | 2.364 | 0.00 | 0.00 |
| 30 | Híbrido (aleatório) | 3/3 | 7.00 | 2.359 | 0.00 | 0.00 |
| 40 | Exato | 3/3 | 8.33 | 8.455 | 0.00 | 0.00 |
| 40 | Exato + warm start | 3/3 | 8.33 | 7.325 | 0.00 | 0.00 |
| 40 | Busca Tabu | 0/3 | 8.33 | 20.000 | 0.00 | 0.00 |
| 40 | Híbrido (críticos) | 3/3 | 8.33 | 7.443 | 0.00 | 0.00 |
| 40 | Híbrido (misto) | 3/3 | 8.33 | 7.414 | 0.00 | 0.00 |
| 40 | Híbrido (aleatório) | 3/3 | 8.33 | 7.386 | 0.00 | 0.00 |
| 60 | Exato | 0/3 | 12.33 | 20.004 | 32.48 | 15.76 |
| 60 | Exato + warm start | 0/3 | 10.67 | 20.007 | 21.82 | 0.00 |
| 60 | Busca Tabu | 0/3 | 10.67 | 20.000 | 21.82 | 0.00 |
| 60 | Híbrido (críticos) | 0/3 | 10.67 | 20.005 | 21.82 | 0.00 |
| 60 | Híbrido (misto) | 0/3 | 10.67 | 20.009 | 21.82 | 0.00 |
| 60 | Híbrido (aleatório) | 0/3 | 10.67 | 20.005 | 21.82 | 0.00 |

## Definições e limites

Minimização: LB ≤ χ(G) ≤ UB. UB é o número de cores da coloração válida. LB é clique ou dual global do MIP.
Gap certificado = 100(UB − LB_ref)/UB; LB_ref é o maior teto numérico seguro dos limites globais observados. É uma referência compartilhada somente após os experimentos.
Excesso primal = 100(UB − melhor observado)/melhor observado. Zero significa igualar a melhor solução observada; não garante ótimo.
A coluna de provas registra certificado do HiGHS no modelo completo. A heurística não recebe certificado de outra abordagem; uma clique do mesmo tamanho pode, separadamente, certificar a coloração.
Limites dos subproblemas F&O não são usados como limites globais. Ótimo local não implica ótimo global.
Máximo excesso observado sobre T: 0.019 s. Construção, extração e tolerância do solver entram no tempo registrado; não há 20 s adicionais por fase.
Três grafos por tamanho e um ambiente computacional. O teste não estabelece um limiar universal nem superioridade estatística.
