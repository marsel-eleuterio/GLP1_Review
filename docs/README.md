# Documentos do estudo

Cópias de 14/nov/2026, tiradas de `initial_docs/`. As versões vivas ficam online e é lá que as edições
acontecem; ao atualizar, substitua o arquivo aqui e registre no commit.

| Arquivo | Conteúdo | Versão online |
| --- | --- | --- |
| [plano_de_estudo](plano_de_estudo.md) (.md e .pdf) | Plano de estudo, com os ajustes da revisão da literatura | https://claude.ai/artifact/FR5vRnExpkyoARUPSPtre8 |
| [preregistro_osf_rascunho](preregistro_osf_rascunho.md) (.md e .pdf) | As 25 respostas do pré-registro (Secondary Data Preregistration), em inglês | https://claude.ai/artifact/CNLPEMmVjupDYkQfUGnb6p |
| [revisao_da_literatura](revisao_da_literatura.md) (.md e .pdf) | Revisão da literatura, fechada em 14/nov | https://claude.ai/artifact/KjoyDLWaMUG6ZkTsDUeTuX |
| [preregistro_osf_v2](preregistro_osf_v2.md) | **Versão de trabalho** do pré-registro (14/nov), com os resultados dos scripts preenchidos. A v1 fica intacta | — |
| [pacote_de_trabalho](pacote_de_trabalho.md) | LEIAME original do pacote: ordem de trabalho, conferências e passos do OSF | — |

Nos .md, os dois gráficos do plano aparecem só como legenda; eles estão no PDF.

Licença: os documentos desta pasta estão sob [CC BY 4.0](../LICENSE-docs) (uso e adaptação livres, com
atribuição a Marsel Eleutério). O código do repositório segue a licença MIT ([LICENSE](../LICENSE)).

`pacote_de_trabalho.md` descreve o pacote original. Os caminhos dele (`scripts\`, `piloto\`,
`dados_brutos\`, `dados_limpos\`) valem neste repositório; os comandos `python ...` viram
`uv run python ...` (ver o README da raiz).

## De onde veio cada arquivo

`initial_docs/` é o conteúdo de `projeto_glp1.zip` (pacote de 14/nov/2026), extraído com a estrutura
original. As duas fontes são imutáveis. Os arquivos do projeto são cópias idênticas, byte a byte:

| Em `initial_docs/` | No projeto |
| --- | --- |
| `LEIAME.md` | `docs/pacote_de_trabalho.md` |
| `docs/*` | `docs/*` (mesmos nomes) |
| `piloto/**` | `piloto/**` (mesmos nomes) |
| `scripts/brfss_microdata.py`, `scripts/meps_microdata.py` | `scripts/` (mesmos nomes) |

Histórico: a primeira versão de `initial_docs/` (14/nov, manhã) era uma cópia achatada do pacote, com
nomes e conteúdos trocados e 5 arquivos faltando. Ela foi substituída pela extração do zip no mesmo dia.
