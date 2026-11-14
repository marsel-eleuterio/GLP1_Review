# Piloto: uso de GLP-1 e obesidade nos EUA (12/nov/2026)

Teste exploratório com dados agregados. Não é o estudo final.

## Como rodar

    python pilot_glp1_obesity.py dados dados      # análise principal (grava tabelas em dados/)
    python pilot_extra.py dados                   # estudo de eventos e robustez

Requer numpy e pandas. As saídas da rodada original estão em `saidas/`.

## Dados (pasta `dados/`)

| Arquivo | Conteúdo | Origem |
| --- | --- | --- |
| brfss_ob_total_*.csv | Obesidade adulta (%), IC 95% e n, por local e ano, 2011-2025 | CDC, API aberta, conjunto hn4x-zwk7 (questionid Q036, total) |
| brfss_us_total.csv | Obesidade (Q036) e sobrepeso (Q037), total nacional | idem |
| brfss_us_ob_by_age.csv, brfss_us_ow_by_age.csv | Obesidade e sobrepeso por faixa etária, nacional | idem |
| brfss_us_by_sex.csv | Obesidade e sobrepeso por sexo, nacional | idem |
| rxindex_medicaid_2025.csv | Receitas de GLP-1 no Medicaid por estado (2025), participação no Medicare (2024) e receitas por 100 habitantes de todos os pagadores (2024, PurpleLab via GLP-1 Newsroom) | The RX Index, glp-1-usage-by-state |
| rxindex_medicare_2024.csv, rxindex_medicare_claims_2019_2024.csv | Receitas de GLP-1 no Medicare Part D por estado do prescritor | The RX Index, medicare-glp-1-prescriptions-by-state |
| census_18plus_2024.csv | População de 18 anos ou mais por estado, 1/jul/2024 | Census Bureau, SCPRC-EST2024-18+POP |
| state-abbrevs.csv | Nome do estado -> sigla | github.com/jakevdp/data-USstates |

## Como os dados chegaram aqui

As tabelas foram lidas das páginas e da API e transcritas para CSV, porque o ambiente de
trabalho não baixa arquivos desses sites. Conferências feitas:

- BRFSS: soma dos valores, contagem e soma dos tamanhos de amostra de cada ano batem com
  agregados calculados no servidor do CDC (15 de 15 anos).
- Medicaid: taxa recalculada a partir de receitas e matrículas; soma das receitas = 11.193.556.
- Medicare: as duas tabelas têm os mesmos totais de 2024; crescimento anual recalculado.
- Census: soma dos estados = total nacional (266.978.268).

Antes de usar em artigo, refaça tudo a partir dos arquivos oficiais.

## Limitações

- BRFSS 2025 não tem CA, MS e NV; 2024 não tem TN; 2023 não tem KY e PA; 2021 não tem FL; 2019 não tem NJ.
- "Receitas por 100 habitantes" é contagem de receitas, não de pessoas, e vem de fonte comercial.
- Medicare: estado do prescritor, não do paciente.
