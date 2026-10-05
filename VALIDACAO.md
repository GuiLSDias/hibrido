# Validação da versão entregue

## Algoritmos

`python -m unittest discover -s tests -v` — **5 grupos de testes aprovados**.

- MIP comparado com enumeração independente em 14 grafos pequenos: isolados, grafo completo, ciclo ímpar, bipartido e grafos aleatórios.
- Colorações da heurística verificadas pelas arestas; seus valores não ficam abaixo do ótimo enumerado.
- Warm start aceito pelo HiGHS; MIP completo com warm start confere com a enumeração.
- Fix-and-Optimize preserva a partição dos vértices fixados e nunca converte seu ótimo local em prova global.
- Um teste específico de ciclo com quatro vértices confirma que o subproblema consegue eliminar uma cor quando a classe apropriada está livre.
- Gerador reproduzível, rejeição de warm start com conflitos, limite de tempo e trace de melhorias verificados.

## Dados completos

`python validate_results.py` — **18 grafos e 90 execuções aprovados**.

- Todos os grafos foram reproduzidos a partir das seeds e comparados com as arestas salvas.
- Cada clique salva foi conferida aresta a aresta.
- Cada coloração foi conferida em todas as arestas; a quantidade de cores confere com o objetivo informado.
- Os limites globais não excedem nenhuma solução válida correspondente.
- Cada prova marcada corresponde ao status Optimal do MIP completo, sem fallback, e ao limite inferior inteiro compatível.
- Todos os métodos com warm start registram aceitação do MIP start.
- Os traces só registram melhorias de incumbentes e terminam no objetivo final; os logs de F&O conferem com as contagens.
- Todas as instâncias têm as quatro abordagens principais. A ablação acrescenta 18 execuções.

## Análise e apresentação

`python analyze.py` — métricas, sete figuras, relatório, resumo CSV e dados HTML recalculados a partir das 90 execuções.

Apresentação aberta localmente em Chromium headless, sem servidor:

- **9 slides**, navegação e abas funcionais.
- **30 linhas** na tabela de resumo, incluindo ablação.
- Nenhum erro JavaScript e nenhuma figura ausente.
- Conferência visual dos slides de abertura, modelagem e respostas; imagens e tabelas mantêm os dados da análise.
- Fontes, estilos, scripts e figuras da apresentação funcionam offline. Somente links de referência externos precisam de internet.

## Interpretação dos resultados

O exato puro prova 3/3 réplicas em N=10,15,20,30,40 e 0/3 em N=60. O híbrido possui as mesmas contagens de prova. A heurística e o híbrido alcançam a mesma quantidade de cores nas 18 instâncias. Em N=60, o exato puro retorna 13,12,12 cores; a Tabu, warm start e híbrido retornam 11,10,11.

O F&O crítico não produz redução de cores nos experimentos principais. Isso é um resultado real do teste e não uma falha de execução. Seu teste independente confirma que a estratégia consegue reduzir cores quando existe melhoria dentro da vizinhança.

## Tempo e reprodutibilidade

HiGHS 1.15.0, uma thread, seed interna 1; o ambiente completo está em `results.json`. O limite nominal é 20 s incluindo construção e fases. O maior excesso observado é aproximadamente **0,019 s**, registrado e explicado no relatório. Tempos e trajetórias podem variar em outra máquina, mesmo com grafos idênticos.

Os resultados entregues pertencem somente à versão de Coloração de Grafos. Não foram aproveitados resultados numéricos do projeto anterior.
