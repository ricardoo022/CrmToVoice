# Epic 01 — Base de Dados (Airtable)

**Estado: ✅ Concluído (2026-07-15).** Implementado em
`src/crmToVoice/airtable/` (`client.py`, `leads.py`, `imoveis.py`,
`visitas.py`), com testes unitários (mocked) em `tests/unit/airtable/` e
testes de integração (Airtable real, com limpeza automática dos registos
criados) em `tests/integration/airtable/`. `make check` e `make test`
passam: lint, typecheck, 31 testes unitários, 18 testes de integração.

**Objetivo:** ter as funções de acesso aos dados sobre a base Airtable
"CRM Imobiliário (Voz)" (`appiFiRN7rzTMqyff`), para que o agente (Epic 02)
nunca fale diretamente com a API do Airtable — só com funções já prontas
para criar, ler, atualizar, apagar e pesquisar registos.

**Fora de âmbito desta epic:** classificação de intenção, o wizard de
perguntas, o grafo LangGraph, o checkpointer, o webhook. Essas entram na
Epic 02 (Agente) e Epic 03 (Webhook), que consomem o que aqui é construído.

**Estado atual (verificado em Airtable, 2026-07-15):** a base já existe e
as três tabelas (Leads, Imóveis, Visitas) já têm exatamente os campos
descritos em `docs/CRM.md` §1. Não há trabalho de desenho de esquema nesta
epic — só as funções de acesso.

---

## US-DB-01 — Ligação à base Airtable

Como developer
Quero configurar o acesso autenticado à base Airtable a partir do código
Para que qualquer funcionalidade futura possa ler/escrever na base sem
repetir lógica de autenticação

**Critérios de Aceitação:**

- [x] Token de acesso ao Airtable (Personal Access Token) é lido de
      variável de ambiente — nunca hardcoded no código nem commitado
      (`client.get_api()`, lê `AIRTABLE_API_KEY` via `os.environ`)
- [x] `.env.example` documenta as variáveis necessárias (ex: `AIRTABLE_API_KEY`,
      `AIRTABLE_BASE_ID`)
- [x] Existe uma função/cliente único de ligação à base, reutilizado por
      todas as outras funções de acesso a dados (`client.get_table()`,
      cacheado via `get_api()`; `leads.py`/`imoveis.py`/`visitas.py`
      passam todos por aqui)

---

## US-DB-02 — Repositório de Leads (criar / ler / atualizar / apagar / pesquisar)

Como developer
Quero funções que criam, leem, atualizam, apagam e pesquisam Leads
Para que o agente nunca construa chamadas Airtable à mão — só chame estas
funções

**Critérios de Aceitação:**

- [x] Função para criar um Lead, aceitando qualquer campo de
      `docs/CRM.md` §1.1 (`leads.create_lead`)
- [x] Função para atualizar um Lead existente por ID, aceitando qualquer
      campo da tabela — incluindo campos "automático" na criação
      (`Estado`, `Sentimento`, `Data Última Interação`); essa
      classificação (`docs/CRM.md` §3) só governa o wizard de criação, não
      limita o que esta função pode escrever (atualizar `Estado` é uma
      ação suportada — §2.3) (`leads.update_lead`)
- [x] Função para apagar um Lead por ID (`leads.delete_lead`)
- [x] Função para procurar Leads por nome (correspondência
      case-insensitive, parcial), devolvendo lista de correspondências
      (`leads.search_leads`)
- [x] Função para ler um Lead por ID, incluindo as Visitas associadas
      (`leads.get_lead`)

---

## US-DB-03 — Repositório de Imóveis (criar / ler / atualizar / apagar / pesquisar)

Como developer
Quero funções que criam, leem, atualizam, apagam e pesquisam Imóveis
Para que o agente nunca construa chamadas Airtable à mão para Imóveis

**Critérios de Aceitação:**

- [x] Função para criar um Imóvel, aceitando qualquer campo de
      `docs/CRM.md` §1.2 (`imoveis.create_imovel`)
- [x] Função para atualizar um Imóvel existente por ID, aceitando
      qualquer campo da tabela — incluindo `Estado` (automático na
      criação, mas explicitamente atualizável via voz — §2.6b)
      (`imoveis.update_imovel`)
- [x] Função para apagar um Imóvel por ID (`imoveis.delete_imovel`)
- [x] Função para procurar Imóveis por morada (correspondência
      case-insensitive, parcial), devolvendo lista de correspondências
      (`imoveis.search_imoveis`)
- [x] Função para ler um Imóvel por ID, incluindo as Visitas associadas
      (`imoveis.get_imovel`)

---

## US-DB-04 — Repositório de Visitas (criar / ler / atualizar / apagar / consultar)

Como developer
Quero funções que criam, leem, atualizam, apagam e consultam Visitas,
incluindo por data e por Lead associado
Para suportar o registo de visitas, a correção de uma visita mal
registada (§2.12) e as perguntas de leitura por voz (§2.8–2.11)

**Critérios de Aceitação:**

- [x] Função para criar uma Visita, ligando-a a um Lead (obrigatório) e
      opcionalmente a um Imóvel, aceitando qualquer campo de
      `docs/CRM.md` §1.3 (`visitas.create_visita`, valida que `Lead` não
      é vazio e levanta `ValueError` caso contrário)
- [x] Função para atualizar uma Visita existente por ID, aceitando
      qualquer campo da tabela — incluindo reatribuir os campos de
      ligação `Lead`/`Imóvel` (§2.7 "associar lead a imóvel")
      (`visitas.update_visita`)
- [x] Função para apagar uma Visita por ID (confirmação de voz antes de
      chamar esta função é responsabilidade da Epic 02, não desta função)
      (`visitas.delete_visita`)
- [x] Função para ler uma Visita por ID (`visitas.get_visita`)
- [x] Função para listar Visitas por intervalo de datas (suporta "que
      visitas tenho hoje?") (`visitas.list_visitas_by_date_range`)
- [x] Função para listar Visitas associadas a um Lead específico,
      ordenadas por data (suporta "qual é o próximo passo com a Maria?")
      (`visitas.list_visitas_by_lead`)

---

## Notas em aberto para revisão

- **Pesquisa por nome/morada:** implementada como correspondência parcial
  case-insensitive (fórmula Airtable `SEARCH(LOWER(...), LOWER(...))`).
  Continua por decidir se isto chega, ou se é preciso lidar com erros de
  dicionário/dictation (acentos, variações fonéticas) — ainda não
  testado com dictation real.
- Nenhuma story aqui cobre o Context Middleware em si (resolver
  Lead/Imóvel mencionados no texto antes do LLM correr, ou o que fazer
  com múltiplos resultados de pesquisa) — isso pertence à Epic 02, usando
  as funções de pesquisa daqui.
- Validação de campos, tratamento de erros da API e paginação continuam
  fora de âmbito, tal como planeado. Isolamento de dados de teste não
  tem uma estratégia formal (não há base Airtable de sandbox — os testes
  de integração correm contra a base real), mas cada teste que cria um
  registo limpa-o a seguir (fixture `cleanup`/`finally`); confirmado
  sem registos órfãos após várias execuções.
