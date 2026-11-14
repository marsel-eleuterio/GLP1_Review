# scripts/

| Script | Uso |
| --- | --- |
| `brfss_microdata.py` | Baixa, extrai e valida os microdados do BRFSS 2011-2025 |
| `meps_microdata.py` | Baixa e extrai os 16 arquivos do MEPS, liga os painéis e confere com os codebooks |
| `run_pilot.py` | Roda o piloto de 12/nov e grava em `resultados/piloto/` |

`brfss_microdata.py` e `meps_microdata.py` são cópias exatas do pacote original (`projeto_glp1.zip`) e
são os scripts citados no pré-registro. Não os reformate. Se precisar corrigir algo depois que rodar
com os arquivos reais, faça um commit separado e explique o motivo, porque eles vão para o OSF.

Os dois `selftest` passam neste ambiente (`.venv`, Python 3.12, com `pyreadstat`). No selftest do MEPS,
as linhas "not found" e MISMATCH são esperadas, porque ele roda em dados sintéticos.

## Ordem de execução (na raiz do repositório)

    # 1. testar a lógica, sem internet
    uv run python scripts/brfss_microdata.py selftest
    uv run python scripts/meps_microdata.py selftest

    # 2. baixar (cada script mostra o que vai baixar e pergunta antes)
    uv run python scripts/brfss_microdata.py download --out dados_brutos/brfss    # 15 arquivos, ~1 GB
    uv run python scripts/meps_microdata.py  download --out dados_brutos/meps     # 16 arquivos, ~110 MB

    # 3. extrair as colunas do estudo
    uv run python scripts/brfss_microdata.py extract --raw dados_brutos/brfss --out dados_limpos/brfss
    uv run python scripts/meps_microdata.py  extract --raw dados_brutos/meps  --out dados_limpos/meps

    # 4. validar o BRFSS contra a API do CDC usada no piloto
    uv run python scripts/brfss_microdata.py validate --clean dados_limpos/brfss --api piloto/dados

O que conferir depois: ver "O que conferir depois de rodar" em `docs/pacote_de_trabalho.md`.

## Ainda a escrever

Necessários para a análise, não para o registro: download de Medicare Part D e Medicaid direto da CMS
(H4) e dados do Census/ACS para a pós-estratificação (H1).
