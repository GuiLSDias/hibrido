# Roteiro — apresentação do TP-III

Este roteiro segue os nove slides do `index.html`. Os números vêm de `RELATORIO.md` e da tabela da apresentação; consulte-os antes de apresentar. Não reutilize números ou conclusões da versão anterior do projeto.

## Slide 1 — Heurística e método exato na Coloração de Grafos

“Neste trabalho, mantivemos o problema do TP-II: Coloração de Grafos. Queremos atribuir cores aos vértices, garantindo que dois vértices conectados tenham cores diferentes, usando o menor número possível de cores. No exemplo de provas, cada vértice é uma disciplina, a aresta representa alunos em comum e a cor é um horário.

Adaptamos a Busca Tabu do TP-I e combinamos essa heurística com o solver HiGHS. A ideia é fornecer uma boa coloração inicial e melhorar partes dela antes de resolver o modelo completo. Testamos seis tamanhos, com três réplicas cada e o mesmo limite total de 20 segundos por abordagem.”

## Slide 2 — Problema e instâncias

“A modelagem continua com as variáveis x e y do TP-II. A variável x indica qual cor cada vértice recebe. A variável y indica quais cores estão sendo utilizadas. O objetivo é minimizar a soma dos y.

As restrições garantem uma cor por vértice, cores diferentes nas arestas e a ligação entre atribuir e utilizar uma cor. Também ordenamos as cores para reduzir soluções equivalentes que só trocam os nomes das cores.

Geramos grafos com 10, 15, 20, 30, 40 e 60 vértices. Cada par recebe uma aresta com probabilidade de 50%. A seed depende de N e da réplica, permitindo repetir os mesmos grafos. Não estamos apenas aumentando uma instância; temos três grafos diferentes em cada tamanho.”

## Slide 3 — Quatro abordagens

“A primeira abordagem usa somente a Busca Tabu. A segunda usa o HiGHS sem receber uma coloração como warm start. A DSATUR ajuda a limitar a quantidade de cores oferecidas ao modelo, como no TP-II.

A terceira abordagem usa até 10% do tempo para a Busca Tabu e entrega a sua coloração ao solver. Ela serve para avaliar o warm start isoladamente.

A quarta é o híbrido completo: warm start, depois Fix-and-Optimize, e finalmente o modelo exato completo. O F&O recebe até 40% do orçamento. Todas as fases competem pelos mesmos 20 segundos. Se uma fase terminar cedo, o solver pode usar o tempo que sobrou.”

Se perguntarem como a Tabu foi adaptada:

“A solução deixou de ser uma seleção de itens e passou a ser uma cor por vértice. Para tentar reduzir uma cor, aceitamos temporariamente estados com conflitos e fazemos recolorações. A lista tabu evita desfazer movimentos recentes. Só uma coloração com zero conflitos pode virar a melhor solução válida.”

## Slide 4 — Fix-and-Optimize

“A nossa decisão foi tentar eliminar uma classe de cor pequena. Liberamos todos os vértices dessa classe e completamos a janela com vizinhos críticos, priorizando saturação e grau. Os demais vértices mantêm suas cores.

Saturação é a quantidade de cores diferentes que um vértice observa na sua vizinhança. Grau é a quantidade de vizinhos. Esses critérios tentam identificar onde pequenas mudanças podem abrir espaço para eliminar uma cor.

A menor classe é renomeada para a última cor, pois as cores do modelo estão ordenadas. Assim podemos desligar essa cor sem contrariar a ordenação.

O tamanho da janela é adaptativo. Aumentamos quando o solver resolve rapidamente e reduzimos quando ele não consegue concluir. Cada tentativa recebe até dois segundos. Também comparamos essa seleção com vértices adicionais aleatórios e uma mistura das duas regras.

Um detalhe importante: provar o ótimo com vários vértices fixados só prova o melhor resultado daquela vizinhança. Isso não prova o número cromático do grafo completo.”

## Slide 5 — Quem fecha o gap?

“O eixo horizontal mostra o número de vértices e o vertical mostra a proporção das três réplicas em que cada abordagem obteve um certificado de otimalidade do solver. Esse gráfico mostra a diferença entre simplesmente encontrar uma coloração e provar que não existe outra com menos cores.”

Leia a transição que aparece abaixo do gráfico. Use “neste experimento” e informe as contagens por tamanho. Se não houver falha na faixa testada, diga que o limite não foi observado, sem inventar um tamanho.

## Slide 6 — Solução e certificado

“Agora separamos duas perguntas. Na esquerda, medimos a distância entre a coloração encontrada e o limite inferior conhecido. Na direita, medimos quantas cores a abordagem usa a mais em relação à melhor coloração observada na instância.

Como estamos minimizando, a coloração válida fornece um limite superior: sabemos que o grafo pode ser colorido com aquela quantidade de cores. A clique ou o solver fornece um limite inferior: sabemos que não podemos usar menos do que aquele limite.

Quando esses lados se encontram, podemos certificar o ótimo. Mas igualar a melhor coloração observada só demonstra qualidade relativa; se o limite inferior ainda estiver abaixo, o ótimo pode continuar desconhecido.”

## Slide 7 — Convergência

“Cada curva acompanha melhorias na quantidade de cores de uma coloração válida. Uma queda significa que encontramos uma solução melhor. Nos métodos com warm start, a fase inicial da Busca Tabu aparece dentro do tempo total.

É importante observar que esse gráfico acompanha o incumbente, e não a evolução inteira do limite dual. Uma curva estável pode significar que a solução já é boa ou que o método não conseguiu melhorá-la. A interpretação depende também do gap final e do certificado.”

Leia a quantidade real de melhorias do F&O que aparece no slide. Uma tentativa sem melhoria também faz parte do resultado experimental.

## Slide 8 — Perguntas obrigatórias

Use as quatro respostas atualizadas do slide:

1. Informe a primeira falha do exato e o tamanho anterior com todas as réplicas provadas.
2. Compare o híbrido e o exato nas mesmas instâncias. Diga se houve ganho de prova e se o maior tamanho com todas as réplicas provadas mudou.
3. Informe em quais tamanhos a Tabu e o híbrido chegaram à mesma quantidade de cores. Isso é igualdade de qualidade, não igualdade de capacidade de prova.
4. Compare o tempo total quando ambos provaram, o número de melhorias do F&O e o controle de warm start. Evite afirmar que uma etapa acelerou o solver apenas porque o tempo depois do warm start foi pequeno.

## Slide 9 — Interpretação e limites

“O warm start ajuda o solver a começar com uma solução viável de boa qualidade. O Fix-and-Optimize tenta melhorar essa solução em regiões escolhidas. Porém, uma prova global também depende do limite inferior, da simetria e da estrutura do grafo.

O efeito da combinação deve ser avaliado pelos resultados, incluindo o custo das fases. Um resultado sem ganho continua sendo válido, porque mostra que a estratégia não trouxe a vantagem esperada naquele conjunto.

As conclusões se limitam a esses grafos, ao orçamento de 20 segundos e ao ambiente utilizado. Testamos três réplicas por tamanho. Não estamos afirmando um limite universal nem uma superioridade estatística de uma abordagem.”

## Respostas curtas para perguntas

- **HiGHS:** solver de otimização que resolve o modelo inteiro usando branch-and-cut, com limites e cortes para reduzir a árvore de busca.
- **Warm start:** fornecer ao solver uma coloração completa e válida como solução inicial.
- **Fix-and-Optimize:** fixar parte das decisões e permitir mudanças apenas em uma vizinhança, resolvendo o subproblema com o método exato.
- **Incumbente:** melhor coloração válida encontrada até aquele momento.
- **Clique:** conjunto de vértices em que todos são adjacentes entre si; exige uma cor diferente para cada vértice e fornece um limite inferior.
- **Ablação:** mudar uma parte da estratégia para avaliar se essa escolha contribui para o resultado.
- **Por que não continuar com o problema do TP-I?** O TP-III mantém o problema do TP-II. O que pode ser reaproveitado do TP-I é a heurística, adaptada para coloração.
