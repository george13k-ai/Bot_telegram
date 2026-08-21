from __future__ import annotations

import io
import re

from app.utils.logging import get_logger

logger = get_logger(__name__)

# Матчит суммы вида "-600,02 RUR", "-1 453,58 RUR", "-1 922.68 ₽", "42 087,95 руб."
# Разные банки используют разные разделители копеек (запятая или точка) и
# разные обозначения валюты, поэтому оба варианта поддерживаются.
_AMOUNT_RE = re.compile(r"(-?\d[\d\s ]*[.,]\d{2})\s*(?:RUR|руб\.?|₽)", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"[\s ]")

# Строки транзакций в банковских выписках почти всегда начинаются с даты
# (ДД.ММ.ГГГГ). Если "Описание" переносится на следующую визуальную строку
# PDF (например, ключевое слово оказывается на строке ниже суммы), это
# позволяет склеить перенесённые строки обратно в одну логическую запись.
_DATE_LINE_RE = re.compile(r"^\s*\d{2}\.\d{2}\.\d{4}\b")


class CalculationService:
    """
    Расчёт потенциальной переплаты по загруженной пользователем банковской
    выписке (PDF).

    Формула: разбиваем текст выписки на "блоки" (одна транзакция = одна
    строка с датой в начале + все последующие строки без даты, которые
    относятся к ней из-за переноса текста), находим блоки, содержащие
    настраиваемое ключевое слово (по умолчанию "страх" - покрывает
    "страхование", "страховая защита" и т.п.), и суммируем модуль первой
    найденной в каждом таком блоке суммы (некоторые банки дублируют сумму
    в двух колонках - "сумма в валюте счёта" и "сумма в валюте карты",
    берём только одну, чтобы не задвоить).

    Если ни одна строка в выписке не начинается с даты (формат совсем не
    похож на банковскую выписку), откатываемся к простому построчному
    поиску, чтобы не потерять совпадения.

    Ключевое слово редактируется администратором (Настройки), поэтому сюда
    оно передаётся параметром, а не берётся из конфига напрямую - сервис
    не завязан на БД и легко тестируется.

    Если в файле не удалось найти ни одной подходящей записи (другой формат
    выписки, отсканированный документ без текстового слоя и т.п.) - метод
    возвращает None, и вызывающий код должен корректно показать пользователю
    "сумма пока не определена" + предложить написать специалисту.
    """

    def _extract_amount(self, block_text: str) -> float | None:
        match = _AMOUNT_RE.search(block_text)
        if not match:
            return None
        normalized = _WHITESPACE_RE.sub("", match.group(1)).replace(",", ".")
        try:
            return abs(float(normalized))
        except ValueError:
            return None

    def _group_into_blocks(self, text: str) -> list[str]:
        lines = text.splitlines()
        if not any(_DATE_LINE_RE.match(line) for line in lines):
            # Формат без дат в начале строки - работаем построчно как раньше.
            return lines

        blocks: list[str] = []
        current: list[str] = []
        for line in lines:
            if _DATE_LINE_RE.match(line):
                if current:
                    blocks.append(" ".join(current))
                current = [line]
            elif current:
                current.append(line)
        if current:
            blocks.append(" ".join(current))
        return blocks

    def calculate_from_text(self, text: str, keyword: str) -> float | None:
        keyword_lower = keyword.strip().lower()
        if not keyword_lower or not text:
            return None

        total = 0.0
        found = False
        for block in self._group_into_blocks(text):
            if keyword_lower in block.lower():
                amount = self._extract_amount(block)
                if amount is not None:
                    total += amount
                    found = True

        return round(total, 2) if found else None

    def calculate_from_pdf_bytes(self, pdf_bytes: bytes, keyword: str) -> float | None:
        try:
            import pdfplumber
        except ImportError:
            logger.error("pdfplumber_not_installed")
            return None

        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                text_parts = [page.extract_text() or "" for page in pdf.pages]
        except Exception as exc:  # noqa: BLE001 - PDF содержимое непредсказуемо, любая ошибка -> None
            logger.warning("pdf_parse_failed", error=str(exc))
            return None

        # Блоки группируем постранично, чтобы перенос записи с одной страницы
        # на другую не склеился с началом следующей таблицы.
        total = 0.0
        found = False
        for page_text in text_parts:
            page_amount = self.calculate_from_text(page_text or "", keyword)
            if page_amount is not None:
                total += page_amount
                found = True

        return round(total, 2) if found else None
