# Projeto GLP-1 e obesidade nos EUA: pacote de trabalho

Versão de 14 de novembro de 2026. Este pacote substitui os anteriores (`piloto_glp1_obesidade.zip`,
`brfss_microdados.zip` e `dados_glp1.zip`).

## O que tem aqui

| Pasta ou arquivo | Conteúdo |
| --- | --- |
| `scripts/brfss_microdata.py` | Baixa, extrai e valida os microdados do BRFSS 2011-2025 |
| `scripts/meps_microdata.py` | Baixa e extrai os 16 arquivos do MEPS e confere as contagens com os codebooks |
| `piloto/` | Código, dados e saídas do piloto de 12/nov, com LEIAME próprio |
| `docs/plano_de_estudo` (.pdf e .md) | Plano de estudo, já com os ajustes da revisão da literatura |
| `docs/preregistro_osf_rascunho` (.pdf e .md) | As 25 respostas do pré-registro, em inglês. Use o .md para copiar e colar no OSF |
| `docs/revisao_da_literatura` (.pdf e .md) | Revisão da literatura, fechada em 14/nov |

Os três documentos também existem online, e é lá que as próximas edições acontecem:

- Plano: https://claude.ai/artifact/FR5vRnExpkyoARUPSPtre8
- Pré-registro: https://claude.ai/artifact/CNLPEMmVjupDYkQfUGnb6p
- Revisão: https://claude.ai/artifact/KjoyDLWaMUG6ZkTsDUeTuX

Os arquivos em `docs/` são uma cópia do dia 14/nov. Nos .md, os dois gráficos do plano aparecem só como
legenda; eles estão no PDF.

## Ordem de trabalho no computador

Requisitos: Python 3.9 ou mais novo, com pandas e numpy (o Anaconda já traz). Descompacte o pacote, abra o
Anaconda Prompt e entre na pasta `projeto_glp1`. Os comandos abaixo criam as pastas `dados_brutos` e
`dados_limpos` dentro dela.

1. Teste a lógica, sem internet:

       python scripts\brfss_microdata.py selftest
       python scripts\meps_microdata.py selftest

2. Baixe os arquivos. Cada script mostra o que vai baixar e pergunta antes de começar:

       python scripts\brfss_microdata.py download --out dados_brutos\brfss
       python scripts\meps_microdata.py download --out dados_brutos\meps

   São 15 arquivos do cdc.gov (cerca de 1 GB) e 16 do meps.ahrq.gov (cerca de 110 MB).

3. Extraia as colunas do estudo:

       python scripts\brfss_microdata.py extract --raw dados_brutos\brfss --out dados_limpos\brfss
       python scripts\meps_microdata.py extract --raw dados_brutos\meps --out dados_limpos\meps

4. Valide o BRFSS contra os números da API do CDC usados no piloto:

       python scripts\brfss_microdata.py validate --clean dados_limpos\brfss --api piloto\dados

## O que conferir depois de rodar

- `dados_limpos\brfss\validation_state_year.csv`: diferenças de até cerca de 0,15 ponto são arredondamento.
  Acima disso, investigar antes de qualquer modelo.
- `dados_limpos\meps\checks.csv`: nenhuma linha pode trazer MISMATCH. "no reference" quer dizer conferir à
  mão no codebook daquele ano.
- `dados_limpos\brfss\coverage_report.csv`: mostra em que ano a pergunta de diabetes muda de nome. Vai para
  Q12, Q19 e Q23 do pré-registro.
- `dados_limpos\meps\inventory.txt`: quantos adultos têm IMC nas duas medidas e quantos começaram GLP-1 em
  cada painel. Vai para Q13 e Q21 e decide se a H6 fica no grupo de testes confirmatórios (mínimo de 30).
- `dados_brutos\brfss\manifest_sha256.csv` e `dados_brutos\meps\manifest_sha256.csv`: guarde. Eles
  registram o que foi baixado e vão para o projeto do OSF.

## Regra do pré-registro

Até o registro no OSF, os microdados só servem para reproduzir números já publicados e para contar casos.
Nada de IMC por diabetes, por quantil, por uso de GLP-1, nem tendência de altura. Os dois scripts respeitam
essa regra. A sequência é: rodar os scripts, completar o rascunho, registrar, e só então analisar.

## Para registrar no OSF

1. Criar o ORCID e a conta no osf.io, e abrir um projeto privado.
2. Subir `docs\plano_de_estudo.pdf`, a pasta `piloto`, a pasta `scripts` e os dois manifests.
3. Completar no rascunho o que está entre colchetes. A lista está no topo do documento.
4. "Add a Registration", modelo Secondary Data Preregistration, e colar as respostas.

## O que ainda não existe

- Script para baixar Medicare Part D e Medicaid direto da CMS (H4) e os dados do Census e da ACS para a
  pós-estratificação (H1). Não são necessários para registrar, mas são para começar a análise.
- O ambiente de análise com PyMC e o código dos modelos.

## O que foi testado

Os dois `selftest` passam em dados sintéticos, e o piloto reproduz as saídas de `piloto\saidas`. O download
e a leitura dos arquivos reais do CDC e da AHRQ não foram testados, porque o ambiente onde os scripts foram
escritos não alcança esses sites. Se algo falhar, a mensagem de erro basta para corrigir.
