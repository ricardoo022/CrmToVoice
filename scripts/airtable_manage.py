"""Manual Airtable smoke-testing CLI: add and delete test records.

Not part of the app; used via `make airtable-add` / `make airtable-delete`
to sanity-check AIRTABLE_API_KEY/AIRTABLE_BASE_ID against the real base.
`add` creates one of each — a Lead, an Imóvel, and a Visita linking them —
with every field filled in (invented but realistic data).
"""

import argparse
import random
import sys

from dotenv import load_dotenv

from crmToVoice.airtable import imoveis, leads, visitas
from crmToVoice.airtable.client import get_table
from crmToVoice.models import LeadFields, PropertyFields, VisitFields

TABLES = ("leads", "imoveis", "visitas")
AIRTABLE_TABLE_NAMES = {"leads": "Leads", "imoveis": "Imóveis", "visitas": "Visitas"}

NOMES = [
    "Ana Ferreira",
    "João Silva",
    "Mariana Costa",
    "Pedro Oliveira",
    "Beatriz Santos",
    "Ricardo Almeida",
]

MORADAS = [
    "Rua do Comércio, 45, Porto",
    "Avenida da Liberdade, 120, Lisboa",
    "Rua das Flores, 12, Braga",
    "Praça da República, 8, Coimbra",
    "Rua de Santa Catarina, 200, Porto",
]


def add() -> None:
    nome = random.choice(NOMES)
    morada = random.choice(MORADAS)

    lead_fields = LeadFields(
        nome=nome,
        telefone="912345678",
        email=f"{nome.lower().replace(' ', '.')}@example.com",
        estado="Contactado",
        tipo_de_imovel_procurado="Apartamento",
        orcamento=250000,
        origem="Portal Imobiliário",
        sentimento="Positivo",
        proximo_passo="Ligar amanhã",
        data_ultima_interacao="2026-07-16",
    ).model_dump(by_alias=True, exclude_none=True)
    lead = leads.create_lead(lead_fields)
    print(f"Created Lead {lead['id']!r} ({lead_fields['Nome']!r})")

    imovel_fields = PropertyFields(
        morada=morada,
        tipo="Apartamento",
        preco=350000,
        estado="Reservado",
    ).model_dump(by_alias=True, exclude_none=True)
    imovel = imoveis.create_imovel(imovel_fields)
    print(f"Created Imóvel {imovel['id']!r} ({imovel_fields['Morada']!r})")

    visita_fields = VisitFields(
        titulo=f"Visita — {nome} — 16/07",
        tipo="Visita",
        data="2026-07-16T15:00:00.000Z",
        resumo=f"Visita ao imóvel em {morada} com {nome}.",
        sentimento="Positivo",
        proximos_passos="Enviar proposta por email.",
        lead=[lead["id"]],
        imovel=[imovel["id"]],
    ).model_dump(by_alias=True, exclude_none=True)
    visita = visitas.create_visita(visita_fields)
    print(f"Created Visita {visita['id']!r} ({visita_fields['Título']!r})")

    print()
    print("To delete everything created above:")
    print(f"  make airtable-delete TABLE=visitas ID={visita['id']}")
    print(f"  make airtable-delete TABLE=leads ID={lead['id']}")
    print(f"  make airtable-delete TABLE=imoveis ID={imovel['id']}")


def delete(table: str, record_id: str) -> None:
    if table == "leads":
        leads.delete_lead(record_id)
        print(f"Deleted Lead {record_id!r}")
    elif table == "imoveis":
        imoveis.delete_imovel(record_id)
        print(f"Deleted Imóvel {record_id!r}")
    elif table == "visitas":
        visitas.delete_visita(record_id)
        print(f"Deleted Visita {record_id!r}")


def delete_all(*, yes: bool) -> None:
    records = {key: get_table(name).all() for key, name in AIRTABLE_TABLE_NAMES.items()}
    total = sum(len(v) for v in records.values())

    if total == 0:
        print("Leads, Imóveis and Visitas are all already empty — nothing to delete.")
        return

    print("This will permanently delete ALL records from the real Airtable base:")
    for key, name in AIRTABLE_TABLE_NAMES.items():
        print(f"  {name}: {len(records[key])} record(s)")

    if not yes:
        confirm = input(f"\nType 'DELETE ALL' to permanently delete {total} record(s): ")
        if confirm != "DELETE ALL":
            print("Aborted, nothing deleted.")
            return

    # Delete Visitas first since they link to Leads/Imóveis.
    for record in records["visitas"]:
        visitas.delete_visita(record["id"])
    for record in records["leads"]:
        leads.delete_lead(record["id"])
    for record in records["imoveis"]:
        imoveis.delete_imovel(record["id"])

    print(f"Deleted {total} record(s) from Leads, Imóveis and Visitas.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("add", help="Create a Lead + Imóvel + Visita, all fields filled")

    delete_parser = subparsers.add_parser(
        "delete", help="Delete a record by ID, or every record in all three tables if none given"
    )
    delete_parser.add_argument(
        "table", nargs="?", choices=TABLES, help="Table the record belongs to"
    )
    delete_parser.add_argument(
        "record_id", nargs="?", help="Airtable record ID, e.g. recXXXXXXXXXXXXXX"
    )
    delete_parser.add_argument(
        "--yes", action="store_true", help="Skip the confirmation prompt when deleting all"
    )

    args = parser.parse_args()

    load_dotenv()

    if args.command == "add":
        add()
    elif args.command == "delete":
        if args.table and args.record_id:
            delete(args.table, args.record_id)
        elif not args.table and not args.record_id:
            delete_all(yes=args.yes)
        else:
            parser.error("provide both 'table' and 'record_id', or neither (to delete all)")


if __name__ == "__main__":
    sys.exit(main())
