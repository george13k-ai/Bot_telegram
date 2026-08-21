from __future__ import annotations

from app.services.calculation import CalculationService

SAMPLE_STATEMENT_TEXT = """
26.01.2025 MOCOD251Q0000DB7 Комиссия за организацию страхования, в т.ч. НДС, СОКОЛОВ ОЛЕГ АЛЕКСЕЕВИЧ -600,02 RUR
26.03.2025 MOCOD253Q0000DII Комиссия за организацию страхования, в т.ч. НДС, СОКОЛОВ ОЛЕГ АЛЕКСЕЕВИЧ -659,54 RUR
26.04.2025 MOCOD254Q0000DEY Комиссия за организацию страхования, в т.ч. НДС, СОКОЛОВ ОЛЕГ АЛЕКСЕЕВИЧ -1 453,58 RUR
26.05.2025 MOCOD255Q0000BQ8 Комиссия за организацию страхования, в т.ч. НДС, СОКОЛОВ ОЛЕГ АЛЕКСЕЕВИЧ -764,08 RUR
26.06.2025 MOCOD256Q0000C24 Комиссия за организацию страхования, в т.ч. НДС, СОКОЛОВ ОЛЕГ АЛЕКСЕЕВИЧ -735,02 RUR
26.07.2025 MOCOD257Q0000BOV Комиссия за организацию страхования, в т.ч. НДС, СОКОЛОВ ОЛЕГ АЛЕКСЕЕВИЧ -746,06 RUR
26.12.2024 MAFG 26412002037 Комиссия за услугу "Альфа-Чек"за период с26.11.24 до26.12.24 Согласно тарифам Банка ASBMQB СОКОЛОВ ОЛЕГ АЛЕКСЕЕВИЧ -159,00 RUR
06.01.2025 LO3N#31222098447 СОКОЛОВ ОЛЕГ АЛЕКСЕЕВИЧ Предоставление транша Дог. F0LO3N20231222098447 от 261223 40 000,00 RUR
"""

EXPECTED_TOTAL = round(600.02 + 659.54 + 1453.58 + 764.08 + 735.02 + 746.06, 2)


def test_calculate_from_text_sums_matching_lines_only():
    service = CalculationService()
    result = service.calculate_from_text(SAMPLE_STATEMENT_TEXT, "страх")
    assert result == EXPECTED_TOTAL


def test_calculate_from_text_is_case_insensitive_and_matches_substring():
    service = CalculationService()
    text = "01.01.2025 Оплата СТРАХОВАНИЯ жизни -100,00 RUR"
    assert service.calculate_from_text(text, "страх") == 100.00


def test_calculate_from_text_returns_none_when_no_match():
    service = CalculationService()
    assert service.calculate_from_text("здесь нет нужного слова -100,00 RUR", "страх") is None


def test_calculate_from_text_returns_none_for_empty_input():
    service = CalculationService()
    assert service.calculate_from_text("", "страх") is None
    assert service.calculate_from_text(SAMPLE_STATEMENT_TEXT, "") is None


def test_calculate_from_text_handles_thousand_separator():
    service = CalculationService()
    text = "01.01.2025 Комиссия за страхование -12 345,67 RUR"
    assert service.calculate_from_text(text, "страх") == 12345.67


def test_calculate_from_pdf_bytes_returns_none_for_garbage_input():
    service = CalculationService()
    assert service.calculate_from_pdf_bytes(b"not a real pdf file", "страх") is None


def test_keyword_is_configurable():
    service = CalculationService()
    text = "01.01.2025 Комиссия каско -500,00 RUR"
    assert service.calculate_from_text(text, "страх") is None
    assert service.calculate_from_text(text, "каско") == 500.00


# Реальный формат Т-Банка: описание переносится на следующую строку (ключевое
# слово оказывается отдельно от суммы), разделитель копеек - точка, валюта - ₽,
# а сумма продублирована в двух колонках (нужно взять только одну).
TBANK_STYLE_TEXT = """\
Дата и время Дата Сумма в валюте Сумма операции Описание Номер
26.02.2026 26.02.2026 -1 922.68 ₽ -1 922.68 ₽ Плата за Программу —
23:27 23:27 страховой защиты
26.02.2026 26.02.2026 -99.00 ₽ -99.00 ₽ Плата за предоставление —
23:25 23:25 услуги Защита Карты
26.02.2026 26.02.2026 -8 755.12 ₽ -8 755.12 ₽ Проценты по кредиту —
22:27 22:27
"""


def test_calculate_from_text_handles_wrapped_description_lines():
    service = CalculationService()
    result = service.calculate_from_text(TBANK_STYLE_TEXT, "страх")
    # Only the "страховой защиты" row should count - not "Защита Карты" or
    # "Проценты по кредиту" - and each row's duplicated amount counts once.
    assert result == 1922.68


def test_calculate_from_text_handles_period_decimal_separator():
    service = CalculationService()
    text = "01.01.2025 Плата за страхование -1 234.56 ₽"
    assert service.calculate_from_text(text, "страх") == 1234.56
