"""
Unit tests for email template variable substitution (FR-EMAIL-002).
"""

from backend.src.infrastructure.api.v1.endpoints.email import render_template


def test_render_template_substitutes_documented_variables():
    template = (
        "Уважаемый(ая) {contact_person},\n\n"
        "Наша компания {company_name} готова выполнить перевозку:\n\n"
        "Маршрут: {route}\n"
        "Детали груза: {cargo_details}\n"
        "Предлагаемая цена: {price}\n\n"
        "С уважением,\n{sender_signature}"
    )
    context = {
        "contact_person": "Иван Иванов",
        "company_name": "ООО «Перевозчик»",
        "route": "München → Warszawa",
        "cargo_details": "24t, Munich -> Warsaw",
        "price": "1250 EUR",
        "sender_signature": "MiniTMS",
    }
    rendered = render_template(template, context)
    assert "Иван Иванов" in rendered
    assert "ООО «Перевозчик»" in rendered
    assert "München → Warszawa" in rendered
    assert "24t, Munich -> Warsaw" in rendered
    assert "1250 EUR" in rendered
    assert "MiniTMS" in rendered
    assert "{" not in rendered
    assert "}" not in rendered


def test_render_template_leaves_unknown_placeholders_untouched():
    assert render_template("Цена: {price}, неизвестно {missing}", {"price": "100"}) == "Цена: 100, неизвестно {missing}"


def test_render_template_empty_context_returns_text_unchanged():
    assert render_template("Hello {name}", {}) == "Hello {name}"
