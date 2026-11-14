# Decisões antes do registro: efeitos mínimos (Q20) e regra de veredito (Q22)

2026-11-14 · Apoio à decisão sobre a v2 do pré-registro (`preregistro_osf_v2.md`). Estas escolhas ficam
congeladas no registro.

## Premissas usadas

Os erros-padrão (EP) são os do rascunho, com a contagem real da H6:

| Hipótese | Estimando | EP | De onde vem |
| --- | --- | --- | --- |
| H2 | π̄, diferença por diabetes (kg/m²) | 0,11 | Q21: SD 6,3, efeito de desenho 1,8, ~50 mil adultos com diabetes por ano, DP residual 0,08 |
| H3 | C, contraste P90 − P50 (kg/m²) | 0,20 | Q21: DP residual anual 0,15 |
| H6 | β, iniciantes vs. nunca usuários (kg/m², 2 anos) | 0,33 | SD(ΔIMC) 2,5, efeito de desenho 1,5, **89 iniciantes e 5.211 nunca usuários** (Q13) |

## 1. Poder para "apoiada"

Probabilidade de a hipótese ser apoiada, por efeito verdadeiro. Com Holm, a primeira hipótese testada
usa α/3, que é a situação mais comum quando só uma delas tem efeito.

| Efeito verdadeiro | H2: bilateral α = 0,05 (Q21) | H2: bilateral Holm | H2: unilateral Holm | H3: bilateral α = 0,05 | H3: bilateral Holm | H3: unilateral Holm | H6: bilateral α = 0,05 | H6: bilateral Holm | H6: unilateral Holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| −0,2 | 44% | 28% | 38% | 17% | 8% | 13% | 9% | 4% | 6% |
| −0,3 | 78% | 63% | 73% | 32% | 19% | 26% | 15% | 7% | 11% |
| −0,5 | ~100% | 98% | 99% | 71% | 54% | 65% | 33% | 19% | 27% |
| −0,75 | 100% | 100% | 100% | 96% | 91% | 95% | 63% | 46% | 56% |
| −1,0 | 100% | 100% | 100% | 100% | 100% | 100% | 86% | 75% | 82% |

A Q21 informa o poder sem Holm (primeira coluna de cada hipótese). Com Holm, o poder real é menor.

## 2. O problema: H3 e H6 não podem ser "contraditas"

Pela Q22, uma hipótese é contradita se o teste de equivalência (TOST, α = 0,05) mostrar que o efeito é
menor que o mínimo de interesse. Para isso, o intervalo de 90% inteiro precisa caber dentro de ± o mínimo.
Metade da largura desse intervalo é 1,645 × EP:

| Hipótese | Mínimo de interesse (Q20) | Metade do IC 90% | P(contradita) se o efeito verdadeiro é zero |
| --- | --- | --- | --- |
| H2 | −0,2 | 0,18 | 14% |
| H3 | −0,3 | 0,33 | **0%, impossível** |
| H6 | −0,5 | 0,54 | **0%, impossível** |

Consequência para o veredito geral: "ausente" exige duas hipóteses contraditas (ou NC1 falhar). Só a H2
pode ser contradita por equivalência, e com 14% de chance. Se a assinatura dos remédios realmente não
existir, o resultado quase certo é "misto" ou "inconclusivo", nunca "ausente". O desenho, do jeito que
está, não consegue chegar à conclusão negativa, e um revisor vai notar isso.

## 3. Opções

**A. Tornar a contradição unilateral (recomendada).** As previsões já têm sinal (efeito negativo). A
contradição passa a ser: "o IC 90% inteiro fica acima de −mínimo" (teste unilateral de que o efeito é
menos negativo que o mínimo de interesse, α = 0,05). Os mínimos da Q20 continuam os mesmos. P(contradita
| efeito zero): H2 57%, H3 44%, H6 45%. Um efeito positivo e significativo continua contando como
contradição.

**B. Testar "apoiada" também de forma unilateral.** É coerente com previsões direcionais e com A. O
ganho é modesto (H6 em −1,0: de 75% para 82% com Holm). Desvantagem: revisores às vezes desconfiam de
testes unilaterais; o pré-registro, feito antes dos dados, é a defesa.

**C. Aumentar os mínimos de interesse até ficarem detectáveis** (H3 −0,5; H6 −1,0). Isso resolve o
poder, mas um mínimo de interesse tem que ser um limite substantivo, não uma consequência do tamanho da
amostra. Não recomendo para H3. Para H6, −1,0 kg/m² é defensável por si só: fica dentro da faixa
esperada (−0,5 a −3) e abaixo da perda média por usuário calculada na H5 (−1,3 a −4,3 kg/m² com IMC 35).

**D. Manter tudo como está.** Nesse caso, a v2 precisa dizer claramente que H3 e H6 só podem ser apoiadas
ou ficar inconclusivas, e que o veredito "ausente" depende da H2, de um efeito significativo no sentido
contrário ou da NC1.

## 4. Recomendação

1. **A**, contradição unilateral, para H2, H3 e H6.
2. **B**, apoio unilateral, para fechar a coerência do teste direcional.
3. Para a H6, manter −0,5 como mínimo de interesse e declarar na Q21 o poder com Holm (cerca de 27%
   unilateral). A H6 está no limite: o resultado mais provável é "inconclusiva", a não ser que o efeito
   real passe de −0,75. A alternativa honesta é C só para a H6 (−1,0).
4. Corrigir a Q21 para informar o poder com Holm.

## O que muda na v2, se aceito

- **Q22:** reescrever a definição de "apoiada" e "contradita" (unilateral) e conferir se o veredito geral
  continua igual.
- **Q21:** acrescentar o poder com Holm para H2, H3 e H6 (tabela 1).
- **Q20:** só se a opção C for escolhida para a H6.

## Decisão (14/nov/2026)

Marsel Eleutério escolheu:

1. **Contradição unilateral** (opção A) para H2, H3 e H6.
2. **Apoio unilateral** (opção B), com Holm sobre as três.
3. **Mínimo de interesse da H6 mantido em −0,5 kg/m²**; o poder baixo fica declarado na Q21.

Aplicado na v2: Q21 (poder unilateral, sem ajuste e no primeiro passo de Holm, e P(contradita) com
efeito zero) e Q22 (definições de apoiada, contradita e inconclusiva, com a justificativa). Q20 e o
veredito geral não mudaram.
