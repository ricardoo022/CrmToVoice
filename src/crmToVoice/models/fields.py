"""Pydantic models for CRM entity data accumulated during the voice wizard.

A `*Fields` instance represents a possibly-partial, in-progress record
accumulated across multiple wizard turns (see `docs/CRM.md` §4 — the agent
asks grouped questions and fills fields in over several turns, accepting
"I don't know"/skip), NOT a guaranteed-complete Airtable row.

These models interoperate with the Epic 01 Airtable layer
(`crmToVoice.airtable.leads`/`imoveis`/`visitas`), whose `create_*`/`update_*`
functions expect a plain dict keyed by literal Airtable field names (e.g.
`{"Nome": "Maria", "Orçamento": 250000}`). Every field therefore has both a
clean Python attribute name and an Airtable alias (the exact Airtable field
name, e.g. `"Tipo de Imóvel Procurado"`). The alias is set via
`validation_alias`/`serialization_alias` (rather than the single `alias`
parameter) purely so static type checkers still recognize the plain
attribute name as a valid constructor keyword — `populate_by_name=True`
below is what actually makes both names interchangeable for construction at
runtime; `by_alias=True` uses `serialization_alias` on dump. The
`validation_alias`/`serialization_alias` pair is behaviorally equivalent to
`alias` here (both accept/emit the Airtable name), so any use of "alias" in
this docstring below refers to that pair.

Every model sets `model_config = ConfigDict(populate_by_name=True)` so it
can be constructed either by Python attribute name or by the Airtable
alias.

Critical usage contract: callers must always dump with
`.model_dump(by_alias=True, exclude_none=True)` (never the bare
`.model_dump()`) to get a dict with literal Airtable keys and no
`None`-valued fields, ready to hand directly to `create_lead`/`update_lead`/
etc.

Optional-ness rule: every "asked if missing" field (per `docs/CRM.md` §1 —
this includes primary fields like `Nome`/`Morada`, since they may genuinely
be unfilled before the wizard runs) is `Optional`, default `None`.
"Automatic" fields with a fixed documented default value (Lead `Estado`
default "Novo", Property `Estado` default "Disponível", Visit `Tipo` default
"Visita") get that literal string as their Pydantic default. "Automatic"
fields computed at runtime (dates, LLM-inferred `Sentimento`, agent-generated
`Título`) are `Optional`/`None` — a later graph node fills these in, this
model can't know them at construction.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LeadFields(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    nome: str | None = Field(default=None, validation_alias="Nome", serialization_alias="Nome")
    telefone: str | None = Field(
        default=None, validation_alias="Telefone", serialization_alias="Telefone"
    )
    email: str | None = Field(default=None, validation_alias="Email", serialization_alias="Email")
    estado: Literal["Novo", "Contactado", "Qualificado", "Em Negociação", "Fechado", "Perdido"] = (
        Field(default="Novo", validation_alias="Estado", serialization_alias="Estado")
    )
    tipo_de_imovel_procurado: (
        Literal["Apartamento", "Moradia", "Terreno", "Escritório", "Outro"] | None
    ) = Field(
        default=None,
        validation_alias="Tipo de Imóvel Procurado",
        serialization_alias="Tipo de Imóvel Procurado",
    )
    orcamento: float | None = Field(
        default=None, validation_alias="Orçamento", serialization_alias="Orçamento"
    )
    origem: (
        Literal["Referência", "Portal Imobiliário", "Redes Sociais", "Walk-in", "Outro"] | None
    ) = Field(default=None, validation_alias="Origem", serialization_alias="Origem")
    sentimento: Literal["Positivo", "Neutro", "Negativo"] | None = Field(
        default=None, validation_alias="Sentimento", serialization_alias="Sentimento"
    )
    proximo_passo: str | None = Field(
        default=None, validation_alias="Próximo Passo", serialization_alias="Próximo Passo"
    )
    data_ultima_interacao: str | None = Field(
        default=None,
        validation_alias="Data Última Interação",
        serialization_alias="Data Última Interação",
    )
    visitas: list[str] | None = Field(
        default=None, validation_alias="Visitas", serialization_alias="Visitas"
    )


class PropertyFields(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    morada: str | None = Field(
        default=None, validation_alias="Morada", serialization_alias="Morada"
    )
    tipo: Literal["Apartamento", "Moradia", "Terreno", "Escritório", "Outro"] | None = Field(
        default=None, validation_alias="Tipo", serialization_alias="Tipo"
    )
    preco: float | None = Field(default=None, validation_alias="Preço", serialization_alias="Preço")
    estado: Literal["Disponível", "Reservado", "Vendido"] = Field(
        default="Disponível", validation_alias="Estado", serialization_alias="Estado"
    )
    visitas: list[str] | None = Field(
        default=None, validation_alias="Visitas", serialization_alias="Visitas"
    )


class VisitFields(BaseModel):
    """In-progress Visit (Visita) data accumulated during the wizard.

    `lead` is kept Optional (not a hard-required Pydantic field) even though
    `airtable/visitas.py::create_visita` raises `ValueError` if
    `fields["Lead"]` is empty at write time. This is deliberate layering:
    this model's optionality is representational (it needs to be able to
    hold a genuinely-partial in-progress Visit while a future wizard node is
    still asking for the Lead), while `create_visita`'s check is the actual
    enforcement gate at write time. A later epic's `create_check_fields`
    node must still treat `Lead` as required-to-ask regardless of this
    model's type — the Optional type here does not by itself enforce that
    requirement.
    """

    model_config = ConfigDict(populate_by_name=True)

    titulo: str | None = Field(
        default=None, validation_alias="Título", serialization_alias="Título"
    )
    tipo: Literal["Visita", "Chamada", "Mensagem", "Reunião"] = Field(
        default="Visita", validation_alias="Tipo", serialization_alias="Tipo"
    )
    data: str | None = Field(default=None, validation_alias="Data", serialization_alias="Data")
    resumo: str | None = Field(
        default=None, validation_alias="Resumo", serialization_alias="Resumo"
    )
    sentimento: Literal["Positivo", "Neutro", "Negativo"] | None = Field(
        default=None, validation_alias="Sentimento", serialization_alias="Sentimento"
    )
    proximos_passos: str | None = Field(
        default=None, validation_alias="Próximos Passos", serialization_alias="Próximos Passos"
    )
    lead: list[str] | None = Field(
        default=None, validation_alias="Lead", serialization_alias="Lead"
    )
    imovel: list[str] | None = Field(
        default=None, validation_alias="Imóvel", serialization_alias="Imóvel"
    )
