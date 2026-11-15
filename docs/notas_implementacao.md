# Notas de implementação das análises

2026-11-14 · Código em `src/glp1_review/`, escrito antes do registro e testado só com dados simulados
(`tests/`). Este documento registra onde a Q19 não detalha um passo e qual escolha o código faz. Os itens
que mudavam o resultado de forma relevante foram decididos em 14/nov (ver `decisoes_q20_q22.md`).

## Trava do pré-registro

`guard.py`: qualquer leitura de IMC, obesidade ou altura de dados reais (`data.load_brfss`) dá erro até existir
`docs/osf_registration.txt` com o DOI ou link do registro.

## Comum

| Ponto | Escolha | Onde |
| --- | --- | --- |
| Preditiva da etapa 2 | Regressão linear bayesiana com priori de referência: Student-t com n − p graus de liberdade, locação = previsão de MQO, escala = s·√(1 + x₀′(X′X)⁻¹x₀) | `trend.py` |
| Contrafactual "nível de 2022" (Q24) | Nível observado de 2022 + inclinação estimada em 2011-2019; incerteza só da inclinação | `trend.py` |
| Estratos com uma só PSU | Centrados na média geral dos totais de PSU (Q23) | `survey.py` |
| Bootstrap Rao–Wu | n_h − 1 PSUs sorteadas com reposição em cada estrato, fator n_h/(n_h − 1) | `survey.py` |

## H1 (MRP)

| Ponto | Escolha |
| --- | --- |
| z_s no primeiro ano (2011) | Não há ano anterior: usa a estimativa direta do ano seguinte disponível |
| Raça em 2015-2016 | Sem `_IMPRACE`: o efeito de raça sai do modelo nesses anos e a pós-estratificação soma as células de raça |
| Efeitos de grupo | N(0, σ) com soma zero (ZeroSumNormal), forma não-centrada; sexo como efeito fixo; desvios dos estados com soma zero (decisão de 14/nov) |
| Efeito de divisão | Efeito de grupo como os demais |
| Amostrador | NUTS via `nutpie` (sem compilador C nesta máquina); 4 cadeias × 1.000 + 1.000 de aquecimento, target_accept 0,95 |
| Pareamento entre anos | Os ajustes anuais são independentes; a etapa 2 pareia os sorteios pelo índice |
| Categorias | Idade de `_AGEG5YR` (1; 2-3; 4-5; 6-7; 8-9; 10-13), raça de `_IMPRACE` (4 e 6 → "outros ou multirracial"), escolaridade de `_EDUCAG` |

## H2

Inferência em duas etapas (decisão de 14/nov; ver `decisoes_q20_q22.md`). Efeitos fixos estado × ano absorvidos
por transformação within ponderada (exata por Frisch–Waugh–Lovell). Estratos aninhados no ano.

## H3 e NC1

| Ponto | Escolha |
| --- | --- |
| Modelo logístico da reponderação DFL | Saturado nas 240 células (idade × sexo × raça × escolaridade): o fator é a razão entre a participação da célula em 2017-2019 e no ano |
| Quantis | ECDF ponderada com interpolação linear (Q23) |
| Incerteza | Bootstrap Rao–Wu (500 réplicas) repetindo reponderação, quantis e projeção, **com o sorteio da preditiva Student-t em cada réplica**, para incluir os choques de ano, como na H2 |
| NC1, "por sexo" | Média de altura por sexo, cada série com a sua tendência; o estimando é a média dos dois desvios, e cada sexo é reportado |

## H4

| Ponto | Escolha |
| --- | --- |
| Priori do ruído do fator | σ_j ~ Half-Normal(1) (a Q19 não especifica) |
| Estudo de eventos | MQO sem pesos com efeitos fixos de estado e ano (projeções alternadas no painel desbalanceado); EP agrupado por estado |
| Teste de permutação | Bicaudal em \|β*\| (decisão de 14/nov) |
| Limites de Rambachan–Roth | Versão conservadora (decisão de 14/nov, declarada na Q19): β* ± (1,96·EP + B(M)), em que B(M) é o pior viés da extrapolação linear quando as segundas diferenças da trajetória pré são limitadas por M (programação linear). O intervalo exato de comprimento fixo do pacote HonestDiD (só em R) pode ser mais estreito. É válido, mas pode dificultar a classificação "supportive" |
| Dose-resposta | Desvio de cada estado = média dos anos disponíveis em 2023-2025 menos a projeção da tendência própria de 2011-2019 (pelo menos 3 anos pré) |

## H5

Dentro de cada um dos 10.000 sorteios de parâmetros, a expectativa sobre quem usa e quem persiste é calculada
exatamente (probabilidade de uso × persistência), em vez de sortear pessoa a pessoa; assim os sorteios carregam
só a incerteza dos parâmetros. A perda é a mesma para todos os usuários dentro de um sorteio.

## H6

LSAQWT, com LONGWT onde LSAQWT falta; estratos aninhados no painel. Grupo "desconhecido" (status de GLP-1
faltando em algum ano do painel) fica fora.
