# Resultados reais — Coloração de Grafos

3 grafos, 14 execuções, T=5 s, HiGHS 1.15.0, uma thread.

## 1. Quando o exato deixa de fechar o gap?
O exato provou todas as instâncias; o limite não foi observado na faixa testada.

## 2. O híbrido amplia esse limite?
Ganhos de prova em comparação pareada: 0; perdas: 0. Instâncias com ganho: []. Instâncias com perda: [].
Não houve ampliação do limite nas instâncias testadas.
Compare também a tabela por tamanho. Três réplicas por tamanho não permitem uma conclusão de superioridade estatística.

## 3. Quando a heurística iguala o híbrido?
- N=10: valores iguais em 1/1; heurística melhor em 0; híbrido melhor em 0.
- N=20: valores iguais em 1/1; heurística melhor em 0; híbrido melhor em 0.
- N=30: valores iguais em 1/1; heurística melhor em 0; híbrido melhor em 0.

## 4. A estratégia acelera o solver?
O F&O crítico produziu 0 reduções de cores nas execuções principais.
Não houve ganho primal atribuível à fase F&O neste conjunto.
Tamanhos com menor tempo total médio do híbrido versus exato, quando ambos provaram todas as réplicas: [].
Tamanhos com menor tempo total médio do híbrido versus warm start sozinho, quando ambos provaram todas as réplicas: []. Diferenças pequenas podem refletir variação do solver e da máquina; não isolam uma aceleração causal.
Compare tempo total, contagem de provas e qualidade com exato puro e com exato + warm start. Tempo até prova usa apenas casos provados e possui viés de seleção; não é média de todas as execuções.

## Tabela resumida

| N | Método | Provas | Cores (média) | Tempo total (s) | Gap certificado (%) | Excesso primal (%) |
|---:|---|---:|---:|---:|---:|---:|
| 10 | Exato | 1/1 | 4.00 | 0.031 | 0.00 | 0.00 |
| 10 | Exato + warm start | 1/1 | 4.00 | 0.008 | 0.00 | 0.00 |
| 10 | Busca Tabu | 0/1 | 4.00 | 0.001 | 0.00 | 0.00 |
| 10 | Híbrido (críticos) | 1/1 | 4.00 | 0.064 | 0.00 | 0.00 |
| 20 | Exato | 1/1 | 5.00 | 0.010 | 0.00 | 0.00 |
| 20 | Exato + warm start | 1/1 | 5.00 | 0.011 | 0.00 | 0.00 |
| 20 | Busca Tabu | 0/1 | 5.00 | 0.001 | 0.00 | 0.00 |
| 20 | Híbrido (críticos) | 1/1 | 5.00 | 0.053 | 0.00 | 0.00 |
| 30 | Exato | 1/1 | 7.00 | 0.051 | 0.00 | 0.00 |
| 30 | Exato + warm start | 1/1 | 7.00 | 0.726 | 0.00 | 0.00 |
| 30 | Busca Tabu | 0/1 | 7.00 | 5.000 | 0.00 | 0.00 |
| 30 | Híbrido (críticos) | 1/1 | 7.00 | 0.753 | 0.00 | 0.00 |
| 30 | Híbrido (misto) | 1/1 | 7.00 | 0.760 | 0.00 | 0.00 |
| 30 | Híbrido (aleatório) | 1/1 | 7.00 | 0.753 | 0.00 | 0.00 |

## Definições e limites

Minimização: LB ≤ χ(G) ≤ UB. UB é o número de cores da coloração válida. LB é clique ou dual global do MIP.
Gap certificado = 100(UB − LB_ref)/UB; LB_ref é o maior teto numérico seguro dos limites globais observados. É uma referência compartilhada somente após os experimentos.
Excesso primal = 100(UB − melhor observado)/melhor observado. Zero significa igualar a melhor solução observada; não garante ótimo.
A coluna de provas registra certificado do HiGHS no modelo completo. A heurística não recebe certificado de outra abordagem; uma clique do mesmo tamanho pode, separadamente, certificar a coloração.
Limites dos subproblemas F&O não são usados como limites globais. Ótimo local não implica ótimo global.
Máximo excesso observado sobre T: 0.000 s. Construção, extração e tolerância do solver entram no tempo registrado; não há 20 s adicionais por fase.
Três grafos por tamanho e um ambiente computacional. O teste não estabelece um limiar universal nem superioridade estatística.
