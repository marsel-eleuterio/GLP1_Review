# scripts/

| Script | Uso |
| --- | --- |
| `brfss_microdata.py` | Original do pacote: baixa, extrai e valida os microdados do BRFSS 2011-2025 |
| `meps_microdata.py` | Original do pacote: baixa e extrai os 16 arquivos do MEPS, liga os painéis e confere com os codebooks |
| `brfss_hf_download.py` | **Caminho usado para o BRFSS:** baixa os arquivos anuais em Parquet (Hugging Face, revisão fixa) |
| `brfss_extract_parquet.py` | Extrai as colunas do estudo do Parquet usando a lógica do `brfss_microdata.py` |
| `brfss_wayback_download.py` | Alternativa: baixa os zips XPT das capturas do cdc.gov no Internet Archive |
| `run_pilot.py` | Roda o piloto de 12/nov e grava em `resultados/piloto/` |

`brfss_microdata.py` e `meps_microdata.py` são cópias exatas do pacote original (`projeto_glp1.zip`) e
são os scripts citados no pré-registro. Não os reformate. Se precisar corrigir algo depois que rodar
com os arquivos reais, faça um commit separado e explique o motivo, porque eles vão para o OSF.

Os dois `selftest` passam neste ambiente (`.venv`, Python 3.12, com `pyreadstat`). No selftest do MEPS,
as linhas "not found" e MISMATCH são esperadas, porque ele roda em dados sintéticos.

## Ordem de execução (na raiz do repositório), como rodada em 14/nov/2026

    # 1. testar a lógica, sem internet
    uv run python scripts/brfss_microdata.py selftest
    uv run python scripts/meps_microdata.py selftest

    # 2. MEPS: baixar e extrair (script original)
    uv run python scripts/meps_microdata.py download --out dados_brutos/meps --yes
    uv run python scripts/meps_microdata.py extract  --raw dados_brutos/meps --out dados_limpos/meps

    # 3. BRFSS: baixar em Parquet, extrair, validar com o script original
    uv run python scripts/brfss_hf_download.py                     # dados_brutos/brfss_hf/ + provenance_hf.csv
    uv run python scripts/brfss_extract_parquet.py                 # dados_limpos/brfss/ + coverage_report.csv
    uv run python scripts/brfss_microdata.py validate --clean dados_limpos/brfss --api piloto/dados

O que conferir depois: ver "O que conferir depois de rodar" em `docs/pacote_de_trabalho.md`.

## Por que o BRFSS não veio do cdc.gov

Tentativas em 14/nov/2026, em ordem:

1. **`brfss_microdata.py download`:** HTTP 403 nos 15 anos, já no primeiro pedido. O www.cdc.gov
   (Akamai) recusa qualquer cliente automatizado, inclusive as páginas HTML. O endereço dos arquivos
   está correto (conferido na página `annual_2024.html`). Não tentamos contornar o bloqueio, por
   exemplo trocando o User-Agent.
2. **`ftp.cdc.gov`:** não tem o BRFSS.
3. **Internet Archive (`brfss_wayback_download.py`):** há capturas dos 15 zips, mas o
   `web.archive.org` estava fora do ar (conexão sem resposta).
4. **Hugging Face, `jamesjiadazhan/BRFSS` (usado):** é uma conversão coluna a coluna dos XPT do CDC
   ("original public-use codes; nothing recoded, imputed or dropped"). Foi feita a partir das
   **mesmas capturas do Wayback** (as datas batem com as da tentativa 3), verificadas pelo autor por
   SHA-1. O conjunto traz em `metadata/FILES.parquet` a URL do CDC e o MD5 de cada zip original, e
   em `pipeline/` o código da conversão.

Rastreabilidade: `dados_brutos/brfss_hf/provenance_hf.csv` registra, por ano, a revisão do
repositório (`6e0af47…`), a URL, o tamanho, o sha256 do Parquet, o número de linhas conferido com os
metadados, a URL do CDC, o MD5 do zip do CDC e a captura de origem. Esse arquivo vai para o OSF.

A garantia de que os dados são os do CDC vem do `validate`, rodado com o script original. Resultado em
14/nov/2026: 792 pares estado-ano comparados com a API aberta do CDC, diferença média de 0,025 ponto,
máxima de 0,12, nenhum acima de 0,2 ponto. A série nacional bate com a do CDC em até 0,05 ponto em
todos os anos.

Ressalva para o pré-registro (Q8): as capturas são de 26/jul/2026 (2011 a 2024) e 18/set/2026 (2025).
Uma reedição posterior de algum arquivo pelo CDC não estaria refletida.

## Cobertura das variáveis (coverage_report.csv, 14/nov/2026)

| Variável | Achado | Consequência |
| --- | --- | --- |
| diabetes | `DIABETE3` em 2011-2018, `DIABETE4` a partir de 2019 | Resposta para Q12, Q19 e Q23: a pergunta muda de nome em 2019 |
| sexo | Vazio em 2011-2018: o nome era `SEX` (2011-2017) e `SEX1` (2018) | **Corrigido** (ver abaixo) |
| plano de saúde | Vazio em 2024-2025: renomeado para `_HLTHPL2` | **Corrigido** (ver abaixo) |
| raça | Vazio em 2015-2016: `_IMPRACE` não existe nesses anos | **Mantido vazio** (ver abaixo) |

### Alteração no `brfss_microdata.py` (14/nov/2026, antes do registro)

A lista `CANDIDATES` do script original não cobria esses nomes. Diferenças em relação ao
`initial_docs/scripts/brfss_microdata.py`:

- **`sex`:** acrescentados `SEX1` e `SEX`. Os códigos, conferidos no dicionário do CDC, são os mesmos de
  `_SEX` (1 masculino, 2 feminino). `SEX` e `SEX1` têm ainda 7 e 9 (não sabe, recusou), que precisam ser
  tratados como faltantes na análise.
- **`plan_raw`:** acrescentado `_HLTHPL2`. Mesmos códigos e proporções de `_HLTHPL1`/`_HLTHPLN` (1 tem
  plano, 2 não tem, 9 não sabe ou faltante). Até 2020 a fonte é a pergunta bruta `HLTHPLN1` (1, 2, 7, 9),
  como já estava no script original.
- **`race`:** sem alteração. Em 2015-2016 só existe `_RACE`, com 9 categorias sem imputação, enquanto
  `_IMPRACE` tem 6 categorias imputadas. Misturar as duas quebraria a série. Raça não entra nas hipóteses;
  se for usada na pós-estratificação (H1), tratar 2015-2016 à parte.

Depois da alteração: selftest ok, extração sem colunas faltando (fora raça 2015-2016), validação
inalterada (792 pares estado-ano, máxima de 0,12 ponto).

## Ainda a escrever

Necessários para a análise, não para o registro: download de Medicare Part D e Medicaid direto da CMS
(H4) e dados do Census/ACS para a pós-estratificação (H1).
