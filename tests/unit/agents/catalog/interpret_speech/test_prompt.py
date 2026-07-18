from datetime import date

from crmToVoice.agents.catalog.interpret_speech.prompt import (
    SYSTEM_PROMPT_TEMPLATE,
    render_system_prompt,
)


def test_system_prompt_template_is_non_empty_string():
    assert isinstance(SYSTEM_PROMPT_TEMPLATE, str)
    assert SYSTEM_PROMPT_TEMPLATE.strip() != ""


def test_system_prompt_template_mentions_search_before_create():
    assert "search_leads" in SYSTEM_PROMPT_TEMPLATE
    assert "search_imoveis" in SYSTEM_PROMPT_TEMPLATE


def test_system_prompt_template_mentions_confirm_before_delete():
    assert "confirma" in SYSTEM_PROMPT_TEMPLATE.lower()
    assert "delete_lead" in SYSTEM_PROMPT_TEMPLATE
    assert "delete_imovel" in SYSTEM_PROMPT_TEMPLATE
    assert "delete_visita" in SYSTEM_PROMPT_TEMPLATE


def test_system_prompt_template_mentions_asking_for_missing_info():
    assert "em falta" in SYSTEM_PROMPT_TEMPLATE.lower()


def test_system_prompt_template_instructs_free_form_portuguese_reply():
    assert "português" in SYSTEM_PROMPT_TEMPLATE.lower()
    assert "JSON" in SYSTEM_PROMPT_TEMPLATE


def test_render_system_prompt_defaults_to_todays_date():
    rendered = render_system_prompt()

    assert date.today().isoformat() in rendered


def test_render_system_prompt_accepts_explicit_date():
    rendered = render_system_prompt(today=date(2026, 1, 1))

    assert "2026-01-01" in rendered


def test_render_system_prompt_has_no_leftover_placeholder():
    rendered = render_system_prompt()

    assert "{{TODAY}}" not in rendered
    assert "{{WEEKDAY}}" not in rendered


def test_render_system_prompt_includes_weekday_name():
    monday = date(2026, 1, 5)

    assert "segunda-feira" in render_system_prompt(today=monday)
