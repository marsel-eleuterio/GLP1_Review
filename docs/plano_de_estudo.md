# Plano de estudo: uso de GLP-1 e queda da obesidade nos EUA

2026-11-12 · Marsel Eleutério

## Resumo

O piloto achou a relação na direção esperada, mas fraca: a cada desvio-padrão a mais de uso de GLP-1, a obesidade do estado variou 0,33 ponto percentual a menos (r = −0,28; p = 0,05). O resultado depende de quatro estados e não aparece nos recortes por idade e sexo. O estudo segue viável, com outra moldura: a curva dobrou, não caiu.

- **A queda não está no BRFSS.** A maior pesquisa de saúde dos EUA mostra platô: 33,3% em 2022 e 32,9% em 2025, já corrigindo os três estados ausentes. No Gallup, o mesmo período mostra queda de 39,9% para 37,0%.
- **A quebra de tendência é forte.** A obesidade subia 0,49 ponto por ano até 2019. Em 2025 ela está de 1,2 a 1,8 ponto abaixo do projetado, entre 3,1 e 4,7 milhões de adultos.
- **Os dados estão garantidos, com duas ressalvas.** A obesidade por estado, idade e sexo de 2011 a 2025 já foi aberta e usada. Os microdados do BRFSS e do MEPS ainda precisam ser baixados no seu computador. Não existe série pública de uso de GLP-1 por estado que cubra os planos privados.

Recomendo seguir. O artigo fica publicável nos dois desfechos: se a assinatura do remédio aparecer nos microdados, ou se ela faltar onde deveria estar.

## O que vamos demonstrar

O artigo testa uma pergunta só: a mudança na curva da obesidade adulta nos EUA depois de 2022 tem a assinatura dos medicamentos GLP-1? A resposta vem de sete previsões que podem falhar. Se o remédio explica a mudança, elas aparecem juntas; se ela for artefato de medição, elas se separam.

| # | Hipótese | Previsão que pode falhar | Dados | Sinal no piloto |
| --- | --- | --- | --- | --- |
| H0 | As fontes medem a mesma coisa | A diferença entre Gallup (queda) e BRFSS (platô) se explica por amostra, modo de coleta e ponderação | Gallup, BRFSS, NHANES | Divergência confirmada: de 2022 a 2025, −2,9 ponto no Gallup contra −0,4 no BRFSS |
| H1 | Quebra de tendência | Depois de 2022 a obesidade fica abaixo da trajetória de 2011–2019, e a distância cresce a cada ano | BRFSS 2011–2025 | Forte: −1,2 a −1,8 ponto em 2025 |
| H2 | Gradiente por perfil | O desvio é maior onde o uso é maior. Teste principal: adultos com diabetes diagnosticado contra os demais. Secundários: 50–64 anos, mulheres e quem tem plano de saúde | Microdados do BRFSS + uso por grupo (KFF, Gallup, MEPS) | Ausente por idade e sexo; diabetes ainda não testado |
| H3 | Assinatura no IMC | O percentil 90 do IMC se afasta mais da tendência do que a mediana: a cauda de cima se move primeiro | Microdados do BRFSS | Faixas vistas no piloto: sobrepeso na tendência e IMC abaixo de 25 acima dela. Quantis não testados |
| H4 | Dose-resposta entre estados | Estados com mais uso têm desvio maior, descontados o nível inicial e a tendência anterior | BRFSS + uso por estado | Fraco: r = −0,28, dependente de quatro estados |
| H5 | Plausibilidade mecânica | O desvio observado cabe no que uso × persistência × perda de peso consegue produzir | Ensaios clínicos, estudos de mundo real e MEPS | Não testado; conta de ordem de grandeza dá 1 a 3 pontos |
| H6 | Perda individual | Quem começa a usar GLP-1 perde IMC em relação a quem não usa, e essa perda não aparece antes do início | MEPS, painéis 23 e 24 | Não testado |

Dois controles negativos fecham o desenho: a altura autorreferida e o período 2015–2019 não podem mostrar o mesmo padrão. O produto final é um número: quantos milhões de adultos deixaram de ser obesos em relação à tendência, com intervalo de credibilidade, e que parte disso é compatível com o uso de GLP-1.

## Bases de dados e status de acesso

Tudo o que o estudo precisa é público e gratuito. O piloto já usou a obesidade agregada e três medidas de uso por estado; microdados e arquivos brutos tiveram só a página oficial conferida. Este ambiente lê as páginas do CDC, da CMS e da AHRQ, mas não baixa arquivos desses sites.

| Base | Papel no estudo | O que é | Status em 12 de novembro |
| --- | --- | --- | --- |
| [BRFSS, microdados](https://www.cdc.gov/brfss/annual_data/annual_2025.html) (CDC), 2011–2025 | Desfecho principal: IMC individual com estado, idade, sexo, renda e diabetes | Um ZIP por ano. O de 2025 tem 64,3 MB, 356.158 registros e 284 variáveis | Página de 2025 e [variáveis calculadas](https://www.cdc.gov/brfss/annual_data/2025/pdf/2025-calculated-variables-version4-508.pdf) conferidas (_BMI5, _BMI5CAT, _AGEG5YR, _SEX, _INCOMG1). Arquivos por baixar |
| [API aberta do CDC](https://catalog.data.gov/dataset/nutrition-physical-activity-and-obesity-behavioral-risk-factor-surveillance-system), conjunto hn4x-zwk7 | Obesidade e sobrepeso por estado, idade, sexo, renda, escolaridade e raça, 2011–2025 | Consulta sem cadastro, atualizada em 24/set/2026 | Aberta e usada no piloto: 825 linhas de local e ano conferidas por soma de controle |
| [Medicare Part D por geografia e medicamento](https://data.cms.gov/data-api/v1/dataset/c8ea3f8e-3a09-4fea-86f2-8902fb4b0920/data) (CMS) | Uso de GLP-1 por estado no Medicare, 2019–2024 | API aberta, com receitas e beneficiários por marca | API oficial aberta com uma consulta de teste. A série por estado veio da [compilação do The RX Index](https://therxindex.com/research/medicare-glp-1-prescriptions-by-state/) |
| [Medicaid, State Drug Utilization Data 2025](https://catalog.data.gov/dataset/state-drug-utilization-data-2025) (CMS) | Uso por estado no Medicaid, por medicamento | CSV de domínio público, atualizado em 13/jul/2026 | Catálogo conferido. A tabela por estado veio do [The RX Index](https://therxindex.com/research/glp-1-usage-by-state/) |
| Receitas por 100 habitantes, todos os pagadores (PurpleLab via GLP-1 Newsroom, 2024) | Única medida por estado que inclui planos privados | Tabela de terceiros, um único ano | Em mãos para 50 estados, pela auditoria do The RX Index. As contagens originais não são públicas |
| Uso por perfil: [KFF, nov/2025](https://www.kff.org/public-opinion/kff-health-tracking-poll-prescription-drug-costs-views-on-trump-administration-actions-and-glp-1-use/) e Gallup ([out/2025](https://news.gallup.com/poll/696599/obesity-rate-declining.aspx), [jul/2026](https://news.gallup.com/poll/712157/glp-usage-reaches-new-high.aspx)) | Dose por idade, sexo, diabetes e seguro. No Gallup, o uso atual para perda de peso foi de 3% em 2024 a 11% em 2026 | Páginas públicas | Abertas; números usados no piloto |
| [MEPS](https://meps.ahrq.gov/data_stats/download_data/pufs/h254a/h254adoc.shtml)[, medicamentos prescritos 2018–2024](https://meps.ahrq.gov/data_stats/download_data/pufs/h254a/h254adoc.shtml) (HC-206A a HC-254A) | Uso individual de GLP-1 com o nome do remédio, todo ano: dose por perfil (H2), calibração da simulação (H5) e início do uso (H6) | Um arquivo por ano. O de 2024, de jul/2026, tem 204.550 registros | Números e links dos sete arquivos conferidos em 13/nov. Arquivos por baixar |
| MEPS, arquivos consolidados 2018–2024 (HC-209 a HC-256) | IMC adulto, diabetes, seguro e pesos amostrais de cada pessoa | Um arquivo por ano. O IMC adulto (ADBMI42) só existe nos anos pares: 2018, 2020, 2022 e 2024. Altura e peso não são públicos | Conferido no codebook: 18.252 IMCs válidos em 2018, 13.801 em 2020, 10.601 em 2022 e 10.828 em 2024. Arquivos por baixar |
| MEPS, painéis de quatro anos: painel 23 (2018–2021, HC-236) e painel 24 (2019–2022, HC-245) | Mudança de IMC na mesma pessoa, para a análise individual (H6) | IMC em duas rodadas: 2018 e 2020 no painel 23, 2020 e 2022 no painel 24. O painel 24 tem 5.565 pessoas, 4.883 com as nove rodadas | Variáveis de IMC conferidas no codebook (ADBMI2 e ADBMI6; ADBMI4 e ADBMI8). Arquivos por baixar |

Três limitações já conhecidas entram no desenho. O BRFSS 2025 não tem Califórnia, Mississippi nem Nevada, e a amostra com IMC válido caiu de 407.742 para 318.092 entrevistas. O uso em planos privados só existe por estado num retrato de 2024, de fonte comercial. E, no MEPS, a mudança de IMC na mesma pessoa só pode ser medida nos painéis 23 e 24; quantas pessoas começam o remédio entre as duas medidas só se saberá depois do download.

O que falta para fechar a garantia:

- [ ] Baixar os 15 arquivos anuais do BRFSS e reproduzir, a partir deles, os números da API do CDC
- [ ] Confirmar no codebook de 2025 as perguntas de diabetes e de plano de saúde
- [ ] Baixar Medicare Part D (2019–2024) e Medicaid (2021–2025) direto da CMS, para não depender de compilação de terceiros
- [x] Confirmar a variável de IMC no MEPS: ADBMI42, só nos anos pares
- [ ] Baixar os 16 arquivos do MEPS e conferir as contagens com os codebooks

## Teste piloto

A relação aparece na direção esperada e com o tamanho que a hipótese prevê, mas não é robusta. O teste usou só dados agregados: obesidade por estado e ano no BRFSS, de 2011 a 2025, e três medidas de uso de GLP-1 por estado. O código e as tabelas seguem em arquivo na conversa.

### Nacional: platô, não queda

*[Gráfico (ver o documento online). Fonte: CDC, API aberta (hn4x-zwk7), com correção própria da composição de estados; Gallup, 28 de outubro de 2025 · 2011–2025]*

A obesidade autorreferida subiu 0,49 ponto por ano de 2011 a 2019 e parou em 2022. O valor publicado de 2025 (33,5%) exclui Califórnia, Mississippi e Nevada; com a composição de estados corrigida, fica em 32,9%. Contra a tendência de 2011–2019 o desvio é de −1,2 ponto, três vezes e meia o erro de previsão; contra a de 2011–2022, de −1,8.

Sobre [267 milhões de adultos](https://files.hawaii.gov/dbedt/census/popestimate/2024/state-pop/SCPRC-EST2024-18+POP.pdf), isso equivale a algo entre 3,1 e 4,7 milhões de pessoas. O sobrepeso mostra o espelho: caía desde 2011, chegou a 34,1% em 2022 e está em 34,7% desde 2023.

O Gallup parte de uma amostra pequena no pico: 3.035 entrevistas em janeiro de 2022, com margem de 2 pontos. O artigo de julho de 2026, revisado em setembro por mudança de ponderação, traz dois valores para 2026: 36,8% no texto e 36,4% na tabela. Por isso a comparação acima para em 2025.

### Estados: sinal fraco e concentrado

*[Gráfico (ver o documento online). Fonte: Obesidade: CDC, API aberta (hn4x-zwk7). Receitas de 2024: PurpleLab via GLP-1 Newsroom, na auditoria do The RX Index · 50 estados]*

Entre 2021–22 e 2024–25, cada desvio-padrão a mais de receitas por habitante acompanha 0,33 ponto a menos de obesidade (erro-padrão 0,16; p de permutação 0,05; 50 estados).

A favor da hipótese:

- **O tamanho bate.** Se todo o desvio nacional viesse do remédio, na proporção do uso de cada estado, a inclinação esperada ficaria entre −0,36 e −0,53.
- **O momento bate.** Ano a ano, o gradiente fica entre −0,08 e +0,09 de 2015 a 2021 e chega a −0,35 em 2024 e −0,39 em 2025, com erro-padrão perto de 0,18.
- **O placebo recente passa.** Entre 2015–16 e 2018–19, antes da explosão do uso, a inclinação é −0,06 (p = 0,71).

Contra:

- **Quatro estados carregam o resultado.** Sem West Virginia, Kentucky, Louisiana e Oklahoma, a inclinação vai a −0,03.
- **A medida mais limpa dá zero.** O uso no Medicaid não se correlaciona com o nível de obesidade do estado e não mostra relação (−0,05; p = 0,76). Ele cobre só a baixa renda, então o teste é fraco.
- **A desaceleração começou antes.** O uso se correlaciona em 0,77 com o nível de obesidade, e de 2012–13 a 2015–16 os estados de alto uso ainda cresciam mais rápido (+0,35; p = 0,01). Parte do gradiente é convergência entre estados.

### Idade e sexo: o gradiente do Gallup não se repete

| Faixa etária | Obesidade em 2022 | Em 2024 | Em 2025 | Uso atual de GLP-1 (KFF, nov/2025) |
| --- | --- | --- | --- | --- |
| 18–24 | 20,5% | 20,9% | 19,7% | 4% (18–29 anos) |
| 25–34 | 32,2% | 33,2% | 32,6% | entre 4% e 11% |
| 35–44 | 37,4% | 36,8% | 38,5% | 11% (30–49 anos) |
| 45–54 | 39,9% | 39,0% | 40,6% | entre 11% e 22% |
| 55–64 | 37,4% | 37,9% | 38,1% | 22% (50–64 anos) |
| 65 ou mais | 30,6% | 29,6% | 30,1% | 9% |

No Gallup, as maiores quedas de 2022 a 2025 estão em 40–49 anos (−4,3 pontos) e 50–64 anos (−5,0), justamente quem mais usa. No BRFSS essas faixas não caíram. Entre mulheres e homens a variação desde 2022 é praticamente igual (+0,2 e +0,1), embora elas usem mais (15,2% contra 9,7%, no Gallup). Os valores de 2025 excluem a Califórnia, o que os eleva em cerca de meio ponto no total.

### O que o piloto muda no plano

1. A moldura passa a ser "a curva dobrou", com o tamanho do desvio como resultado principal.
2. Dados agregados não separam o remédio da convergência entre estados. O teste decisivo fica nos microdados: adultos com diabetes diagnosticado, em que 45% usam GLP-1, contra os demais.
3. Com 50 estados, o poder para detectar o efeito cheio (desvio de 1,5 ponto proporcional ao uso) é de cerca de 75%. A dose-resposta entre estados vira evidência de apoio, não o teste central.

## Desenho e métodos

O desenho troca um teste ecológico por seis análises encadeadas nos microdados, cada uma respondendo a uma fraqueza que o piloto expôs. Hipóteses, desfechos e especificações ficam registrados no OSF antes de qualquer análise de IMC nos microdados. Até lá, os microdados só servem para reproduzir números já publicados e para contar casos.

| Etapa | Pergunta | Método | Fraqueza que resolve |
| --- | --- | --- | --- |
| 1. Série nacional comparável | Quanto a curva dobrou? | Modelo bayesiano hierárquico por estado, idade, sexo e ano, com pós-estratificação (MRP) e projeção contrafactual da tendência | Estados ausentes e amostra menor em 2025 |
| 2. Contraste por diabetes | O desvio é maior em quem usa mais? | Diferença em diferenças tripla: IMC de adultos com e sem diabetes diagnosticado, antes e depois de 2022 | Gradiente ausente por idade e sexo |
| 3. Distribuição do IMC | O movimento vem do topo? | Quantis do IMC com composição fixa (reponderação) e contraste entre o percentil 90 e a mediana; regressão RIF e regressão de distribuição como sensibilidade | Prevalência esconde o que acontece dentro das faixas |
| 4. Dose-resposta entre estados | Mais uso, mais desvio? | Diferença em diferenças com tratamento contínuo, estudo de eventos, inferência por permutação e limites de sensibilidade a pré-tendências (Rambachan–Roth); dose–resposta de Callaway, Goodman-Bacon e Sant'Anna, lida como causal só sob tendências paralelas fortes | Convergência entre estados e quatro estados influentes |
| 5. Plausibilidade mecânica | O tamanho cabe? | Microssimulação de uso × persistência × perda de peso sobre a distribuição real de IMC, com incerteza propagada | Falta de um teto para o efeito possível |
| 6. Perda individual | Quem começa o remédio perde peso, e só depois de começar? | Mudança de IMC na mesma pessoa nos painéis 23 (2018→2020) e 24 (2020→2022): quem começa GLP-1 entre as duas medidas contra quem não usa, com pesos longitudinais e ajuste pelo IMC inicial. Placebo: no painel 23, quem só começa em 2021 não pode ter perdido peso antes. Comparação extra: quem começou entre as medidas contra quem só começou em 2021, já que os dois grupos escolheram o remédio | As outras etapas são agregadas; esta liga remédio e peso na mesma pessoa e dá à etapa 5 um piso para o efeito por usuário, porque quem começou em 2019–2022 usava remédios mais antigos e doses menores |

A exposição por estado entra como variável latente. Um modelo de erro de medida combina as três medidas observadas (Medicare, Medicaid e todos os pagadores), porque nenhuma delas conta pessoas em tratamento.

Dois controles negativos acompanham todas as etapas. A altura autorreferida não pode mudar depois de 2022, e o período 2015–2019 não pode mostrar o mesmo gradiente.

Uma conta de ordem de grandeza já indica o que a etapa 5 deve encontrar. Com IMC lognormal ajustado às faixas do BRFSS, 20% dos adultos com obesidade em tratamento e perda média de 6% a 10% do peso, a obesidade cai de 1 a 3 pontos. O desvio observado, de 1,2 a 1,8, cabe nessa faixa; as premissas serão calibradas com os estudos de mundo real, os ensaios clínicos e o efeito por usuário medido na etapa 6.

## Ameaças à validade

A maior ameaça é confundir o remédio com a desaceleração que os estados mais obesos já mostravam. As demais têm tratamento conhecido.

| Ameaça | Por que importa | Tratamento |
| --- | --- | --- |
| Convergência entre estados | Estados mais obesos usam mais GLP-1 e já desaceleravam antes de 2022 | Controle pelo nível defasado, pré-tendências explícitas, limites de Rambachan–Roth e contraste dentro do estado (diabetes) |
| Choque da pandemia | A obesidade saltou cerca de 1 ponto em 2021; o ponto de partida pode estar inflado | Duas tendências de referência, 2011–2019 e 2011–2022, com os dois resultados publicados |
| BRFSS 2025 | Três estados ausentes e amostra 22% menor | Modelo hierárquico com pós-estratificação; todas as análises repetidas só até 2024 |
| Peso autorreferido | O viés do autorrelato pode mudar com o tempo e com o modo de coleta | Calibração com o IMC medido do NHANES; controle negativo de altura |
| Falácia ecológica | Relação entre estados não prova relação entre pessoas | Testes centrais dentro dos microdados (etapas 2, 3 e 6) |
| Exposição mal medida | Receitas não são pessoas, o Medicare registra o estado do prescritor, e o uso privado só existe para 2024 | Modelo de erro de medida com três medidas; análise de sensibilidade |
| Fontes divergentes | A manchete muda conforme a pesquisa: o Gallup mostra queda, o BRFSS mostra platô | Hipótese H0 explícita, com as séries lado a lado |
| Outras causas simultâneas | Mudanças de preço, renda e comportamento depois da pandemia coincidem no tempo | O artigo testa compatibilidade com o remédio, não prova causa; a discussão delimita isso |

## O que torna o preprint chamativo

O gancho é uma contradição que qualquer leitor entende: a manchete diz que a obesidade americana caiu, e a maior pesquisa de saúde do país diz que ela só parou de subir.

- **Posicionamento.** A queda já foi noticiada (Rader et al. 2024, Gallup 2025, Epic Research 2026). A novidade é o teste de causa: nenhum trabalho testou se a mudança tem a assinatura do remédio.
- **Título de trabalho.** "Is the break in the US adult obesity trend a GLP-1 effect? Preregistered signature tests in BRFSS 2011–2025 and MEPS 2018–2024". Alternativa mais curta: "The obesity decline the largest US health survey does not see". A expressão "bend the curve" já circula na imprensa e saiu do título.
- **Número-manchete.** Milhões de adultos com obesidade a menos do que a tendência previa, com intervalo de credibilidade. O piloto aponta de 3,1 a 4,7 milhões.
- **Figura principal.** A curva observada contra a contrafactual, com faixa de incerteza e a série do Gallup ao fundo.
- **Segunda figura.** Um painel com os testes de assinatura e o veredito de cada um: passou, falhou ou inconclusivo.
- **Credibilidade.** Pré-registro no OSF, código e dados em repositório aberto, e os resultados negativos publicados junto.

O texto vale nos dois desfechos. Se a assinatura aparecer, o artigo mede quanto do desvio é compatível com o remédio. Se não aparecer, ele mostra que a queda atribuída ao Ozempic ainda não está nas estatísticas oficiais.

## Cronograma e próximos passos

Estimo dez semanas em tempo parcial do download ao preprint. O primeiro passo é baixar os microdados e reproduzir com eles os números da API do CDC.

| Semana | Etapa | Entrega |
| --- | --- | --- |
| 1 | Baixar e validar BRFSS, Medicare, Medicaid e MEPS | Pipeline de dados reproduzindo a API do CDC e as contagens dos codebooks do MEPS |
| 2 | Pré-registro | Protocolo no OSF com hipóteses e especificações |
| 3–4 | Série nacional hierárquica e conciliação de fontes (H0, H1) | Figura principal e número-manchete |
| 4–5 | Contraste por diabetes e distribuição do IMC (H2, H3) | Testes centrais de assinatura |
| 6 | Dose-resposta entre estados com erro de medida (H4) | Estudo de eventos e limites de sensibilidade |
| 7–8 | Análise individual no MEPS (H6) | Efeito por usuário, com placebo |
| 9 | Microssimulação e controles negativos (H5) | Painel de vereditos |
| 10 | Texto, repositório e submissão | Preprint |

## Decisões tomadas

Decisões de Marsel em 13 de novembro de 2026.

1. **Idioma e veículo.** Inglês, com depósito no arXiv (stat.AP) e um resumo em português para divulgação.
2. **Pré-registro.** Seguir com o registro no OSF antes de analisar o IMC nos microdados, para proteger o artigo da crítica de garimpo de resultados.
3. **Escopo da primeira versão.** Tudo na primeira versão: BRFSS nas etapas 1 a 4, MEPS na simulação e a análise individual no MEPS. Com isso, o cronograma passou de oito para dez semanas.
4. **Ferramentas.** Python com PyMC, o mesmo ambiente do pipeline do piloto.

## Ajustes depois da revisão da literatura

Em 14 de novembro de 2026 a [revisão da literatura](https://claude.ai/artifact/KjoyDLWaMUG6ZkTsDUeTuX) foi fechada, e o [rascunho do pré-registro](https://claude.ai/artifact/CNLPEMmVjupDYkQfUGnb6p) passou a ser a especificação detalhada do estudo. O que mudou em relação a este plano:

- **Posicionamento.** A queda da obesidade já está publicada; o artigo se apresenta como o teste de causa.
- **H3.** Passa a ser o contraste entre o percentil 90 e a mediana do IMC, porque o piloto já viu as faixas.
- **H4.** Ganha a análise de dose–resposta de Callaway, Goodman-Bacon e Sant'Anna. Como o piloto já viu os estados, ela é alvo de estimação, não teste confirmatório.
- **H5.** A perda de peso de quem interrompe o remédio subiu de 0–4% para 2–7%, com base em dados de mundo real.
- **H6.** Ganha a comparação com quem só começou o remédio depois. O efeito medido vale como piso, pela época dos painéis.
- **Contrafactuais externos.** A mudança observada de 2022 a 2025 também será comparada com as projeções de Ward et al. (2019) e do IHME (2026).
- **Análises exploratórias novas.** A divergência entre Gallup e BRFSS por idade, e a cobertura do Medicaid para obesidade como experimento natural.

Os testes confirmatórios são H2, H3 e H6, com correção de Holm. H1 e H4 são alvos de estimação, e a H5 é uma checagem de consistência.

## Fontes

Páginas abertas em 12 e 13 de novembro de 2026.

- CDC, [BRFSS 2025 Annual Data](https://www.cdc.gov/brfss/annual_data/annual_2025.html) e [Calculated Variables 2025](https://www.cdc.gov/brfss/annual_data/2025/pdf/2025-calculated-variables-version4-508.pdf)
- CDC, [Adult Obesity Prevalence Maps](https://www.cdc.gov/obesity/data-and-statistics/adult-obesity-prevalence-maps.html), dados de 2025
- CDC, [Nutrition, Physical Activity, and Obesity – BRFSS](https://catalog.data.gov/dataset/nutrition-physical-activity-and-obesity-behavioral-risk-factor-surveillance-system), conjunto hn4x-zwk7, consultado pela [API](https://data.cdc.gov/resource/hn4x-zwk7.json)
- CMS, [Medicare Part D Prescribers by Geography and Drug](https://data.cms.gov/data-api/v1/dataset/c8ea3f8e-3a09-4fea-86f2-8902fb4b0920/data)
- CMS, [State Drug Utilization Data 2025](https://catalog.data.gov/dataset/state-drug-utilization-data-2025)
- The RX Index, [GLP-1 usage by state](https://therxindex.com/research/glp-1-usage-by-state/) e [Medicare GLP-1 prescriptions by state](https://therxindex.com/research/medicare-glp-1-prescriptions-by-state/)
- Pabau, [GLP-1 usage by state](https://pabau.com/blog/glp-1-usage-by-state/), que identifica a PurpleLab como origem do mapa de todos os pagadores
- KFF, [Health Tracking Poll, novembro de 2025](https://www.kff.org/public-opinion/kff-health-tracking-poll-prescription-drug-costs-views-on-trump-administration-actions-and-glp-1-use/)
- Gallup, [pesquisa de 28 de outubro de 2025](https://news.gallup.com/poll/696599/obesity-rate-declining.aspx) e [In U.S., GLP-1 Usage Reaches New High](https://news.gallup.com/poll/712157/glp-usage-reaches-new-high.aspx), de 7 de julho de 2026
- AHRQ, [MEPS HC-254A: 2024 Prescribed Medicines](https://meps.ahrq.gov/data_stats/download_data/pufs/h254a/h254adoc.shtml)
- Census Bureau, [população de 18 anos ou mais por estado, julho de 2024](https://files.hawaii.gov/dbedt/census/popestimate/2024/state-pop/SCPRC-EST2024-18+POP.pdf), em cópia hospedada pelo estado do Havaí

- AHRQ, [MEPS HC-256: 2024 Full Year Consolidated Data File](https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_detail.jsp?cboPufNumber=HC-256), com a [documentação](https://meps.ahrq.gov/mepsweb/data_stats/download_data/pufs/h256/h256doc.shtml) sobre o IMC adulto (ADBMI42)
- AHRQ, [MEPS HC-251: 2023 Full Year Consolidated Data File](https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_detail.jsp?cboPufNumber=HC-251) e as páginas dos demais arquivos de 2018 a 2023 (HC-209, HC-216, HC-224, HC-233, HC-243; HC-206A, HC-213A, HC-220A, HC-229A, HC-239A, HC-248A)
- AHRQ, [MEPS HC-245: Panel 24 Four-Year Longitudinal Data File](https://meps.ahrq.gov/mepsweb/data_stats/download_data/pufs/h245/h245doc.shtml) e [MEPS HC-236: Panel 23 Four-Year Longitudinal Data File](https://meps.ahrq.gov/mepsweb/data_stats/download_data_files_detail.jsp?cboPufNumber=HC-236)
- OSF, [Select a Registration Template](https://help.osf.io/hc/en-us/articles/360019738794-Select-a-Registration-Template)
- Van den Akker et al., [Preregistration of secondary data analysis: a template and tutorial](https://open.lnu.se/index.php/metapsychology/article/view/2625), Meta-Psychology
