import os
from functools import lru_cache

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def get_openrouter_model() -> str:
    return os.environ["OPENROUTER_MODEL"]


@lru_cache(maxsize=1)
def get_chat_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=get_openrouter_model(),
        api_key=SecretStr(os.environ["OPENROUTER_API_KEY"]),
        base_url=OPENROUTER_BASE_URL,
    )
