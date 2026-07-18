import os
from functools import lru_cache

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def get_openrouter_model() -> str:
    return os.environ["OPENROUTER_MODEL"]


@lru_cache(maxsize=1)
def get_chat_model() -> ChatOpenAI:
    # temperature=0: this agent follows explicit rules (search before create,
    # never confirm before update, always confirm before delete) rather than
    # generating creative text — low temperature makes it follow those rules
    # more consistently. Doesn't guarantee determinism (tool-calling models
    # still vary run to run), but measurably reduces it.
    return ChatOpenAI(
        model=get_openrouter_model(),
        api_key=SecretStr(os.environ["OPENROUTER_API_KEY"]),
        base_url=OPENROUTER_BASE_URL,
        temperature=0,
    )
