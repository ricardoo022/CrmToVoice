# CRM Imobiliário (Voz) — Documentação

Base Airtable: **CRM Imobiliário (Voz)** (workspace "Porjeto")
Base ID: `appiFiRN7rzTMqyff`

Objetivo: eliminar a fricção de registar visitas/interações manualmente. O agente imobiliário dita a nota ("Ei Siri, regista visita...") e o sistema estrutura a informação e escreve-a diretamente no CRM. A interação é **bidirecional**: para perguntas (ex: "que visitas tenho hoje?"), o Siri lê a resposta em voz alta.

---

## 1. Estrutura das Tabelas

### 1.1 Leads
Pessoas interessadas em comprar/vender/arrendar imóveis.

| Campo | Tipo | Pergunta se faltar? |
|---|---|---|
| Nome | Texto (campo primário) | Sim |
| Telefone | Telefone | Sim |
| Email | Email | Sim |
| Estado | Seleção única — Novo → Contactado → Qualificado → Em Negociação → Fechado / Perdido | Não — automático (default "Novo") |
| Tipo de Imóvel Procurado | Seleção única — Apartamento, Moradia, Terreno, Escritório, Outro | Sim |
| Orçamento | Moeda (€) | Sim |
| Origem | Seleção única — Referência, Portal Imobiliário, Redes Sociais, Walk-in, Outro | Sim |
| Sentimento | Seleção única — Positivo, Neutro, Negativo (última interação) | Não — inferido pelo agente |
| Próximo Passo | Texto | Sim |
| Data Última Interação | Data | Não — automático (agora) |
| Visitas *(automático)* | Ligação — todas as Visitas associadas a este lead | — |

### 1.2 Imóveis
Imóveis geridos pelo agente.

| Campo | Tipo | Pergunta se faltar? |
|---|---|---|
| Morada | Texto (campo primário) | Sim |
| Tipo | Seleção única — Apartamento, Moradia, Terreno, Escritório, Outro | Sim |
| Preço | Moeda (€) | Sim |
| Estado | Seleção única — Disponível, Reservado, Vendido | Não — automático (default "Disponível") |
| Visitas *(automático)* | Ligação — todas as Visitas associadas a este imóvel | — |

### 1.3 Visitas
Registo de visitas/interações — alimentado por voz via Siri Shortcut. É o núcleo do sistema.

| Campo | Tipo | Pergunta se faltar? |
|---|---|---|
| Título | Texto (campo primário, ex: "Visita — João Silva — 14/07") | Não — gerado pelo agente |
| Tipo | Seleção única — Visita, Chamada, Mensagem, Reunião | Não — automático (default "Visita") |
| Data | Data e hora | Não — automático (agora) |
| Resumo | Texto longo, gerado a partir da nota de voz | Sim |
| Sentimento | Seleção única — Positivo, Neutro, Negativo | Não — inferido pelo agente |
| Próximos Passos | Texto longo | Sim |
| Lead | Ligação → Leads | Sim (identificar ou criar) |
| Imóvel | Ligação → Imóveis | Sim |

---

## 2. Ações que a pessoa pode fazer por voz

Estas são as intenções (intents) que o agente em LangGraph terá de reconhecer a partir da fala e traduzir em operações no CRM.

### Criar

**2.1 Registar visita/interação** (ação principal)
> "Ei Siri, regista visita. Estive com o João Silva no apartamento da Rua X, ele gostou mas achou caro, vou enviar proposta amanhã."
- Verifica se o **Lead** já existe → associa; senão, cria lead novo.
- Verifica se o **Imóvel** mencionado existe → associa se identificado.
- Cria registo em **Visitas** com o que for extraído da fala; pergunta pelos campos em falta que exigem pergunta (ver tabela acima e mecanismo do wizard, secção 4).
- Atualiza **Data Última Interação** e **Sentimento** no Lead.

**2.2 Criar lead novo**
> "Ei Siri, novo lead. Maria Costa, quer um T2 até 250 mil, contacto por indicação da Ana."
- Cria registo em **Leads** com o que for extraído; segue o wizard para os campos em falta.

**2.5 Registar chamada ou mensagem** (variante da 2.1)
> "Ei Siri, liguei ao João, ainda está a pensar."
- Mesmo fluxo da 2.1, mas Tipo = "Chamada" ou "Mensagem".

**2.6 Adicionar imóvel** *(gestão de carteira — opcional)*
> "Ei Siri, novo imóvel. Apartamento na Rua X, T3, 320 mil, disponível."
- Cria registo em **Imóveis**; segue o wizard para os campos em falta.

### Ler / Perguntar (Siri responde por voz)

**2.8 Consultar agenda/visitas**
> "Ei Siri, que visitas tenho hoje?" → *"Tens 2 visitas hoje: João às 15h e Maria às 17h."*

**2.9 Consultar estado de um lead**
> "Ei Siri, qual é o estado do João?" → *"O João está em negociação, último contacto há 3 dias."*

**2.10 Consultar métricas**
> "Ei Siri, quantos leads tenho em negociação?" → *"Tens 5 leads em negociação."*

**2.11 Consultar próximo passo**
> "Ei Siri, qual é o próximo passo com a Maria?" → *"Enviar proposta esta semana."*

### Atualizar

**2.3 Atualizar estado do lead**
> "Ei Siri, o Zé já não está interessado." / "Ei Siri, a Maria fechou negócio."
- Localiza o Lead e atualiza **Estado**.

**2.4 Definir próximo passo / lembrete**
> "Ei Siri, lembrete: ligar ao João amanhã."
- Atualiza **Próximo Passo** no Lead correspondente.

**2.6b Atualizar imóvel**
> "Ei Siri, o imóvel da Rua X está reservado."
- Atualiza registo em **Imóveis**.

**2.7 Associar lead a imóvel**
> "Ei Siri, o João está interessado no apartamento da Rua X."
- Cria/atualiza ligação entre Lead e Imóvel.

### Apagar

**2.12 Apagar lead / visita / imóvel**
> "Ei Siri, apaga o lead do João."
- **Exige sempre confirmação** antes de executar: Siri pergunta *"De certeza que queres apagar o lead do João Silva?"* e só apaga após confirmação explícita ("sim"/"confirmo"). Sem confirmação clara, a ação é cancelada.

---

## 3. Classificação de campos (por ação de criação/atualização)

- **Automático** — o sistema preenche sozinho (datas, título, estado inicial, sentimento inferido do texto). Nunca é perguntado.
- **Pergunta se faltar** — todos os restantes campos. Se não vierem na frase inicial da pessoa, o agente pergunta.

---

## 4. Mecanismo do diálogo guiado (wizard)

Quando faltam campos que exigem pergunta, o agente não pergunta um a um sem critério — agrupa por tema para reduzir o número de idas-e-voltas:

- **Grupo "contacto"**: Telefone + Email → *"Qual o contacto dele?"*
- **Grupo "o que procura"**: Tipo de Imóvel + Orçamento → *"O que procura, e com que orçamento?"*
- Campos sem grupo natural (ex: Nome, Resumo, Morada) são perguntados isoladamente.

Regras do wizard:
1. Pergunta o grupo/campo em falta.
2. Se a resposta cobrir só parte do grupo, pergunta de seguimento **apenas pelo campo que ainda falta** (ex: só *"E o orçamento?"*).
3. Se a pessoa disser "não sei" / "salta" / equivalente, o agente avança sem preencher esse campo — nunca insiste.
4. O diálogo continua até não haver mais campos "pergunta se faltar" por preencher (ou todos terem sido salteados).

---

## 5. Fluxo de decisão (resumo)

Para qualquer ação por voz, o agente precisa de:
1. **Classificar a intenção** (Criar / Ler / Atualizar / Apagar, e qual entidade).
2. **Extrair entidades** do que já foi dito.
3. **Verificar existência** do Lead/Imóvel no CRM (procura por nome/morada).
4. Se for **Apagar** → pedir confirmação antes de executar.
5. Se for **Criar/Atualizar** e faltarem campos → seguir o wizard guiado (secção 4).
6. Se for **Ler** → consultar o CRM e devolver resposta em texto para o Shortcut falar.
7. **Executar** a operação no Airtable.

*(O desenho do grafo LangGraph que implementa este fluxo será discutido separadamente.)*
