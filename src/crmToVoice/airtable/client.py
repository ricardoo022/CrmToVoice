import os
from functools import lru_cache

from pyairtable import Api, Table
from pyairtable.api.types import RecordDict


@lru_cache(maxsize=1)
def get_api() -> Api:
    return Api(os.environ["AIRTABLE_API_KEY"])


def get_table(table_name: str) -> Table:
    return get_api().table(os.environ["AIRTABLE_BASE_ID"], table_name)


def get_records_by_ids(table_name: str, record_ids: list[str]) -> list[RecordDict]:
    table = get_table(table_name)
    return [table.get(record_id) for record_id in record_ids]
