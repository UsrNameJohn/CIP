import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation

PERCENTAGE_TYPES = {"DISCOUNT_PERCENTAGE", "MARKUP_PERCENTAGE"}
CSV_HEADERS = [
    "customer_number",
    "customer_store",
    "salesline",
    "article_identifier",
    "article_identifier_type",
    "cip_store",
    "exclusive_cip",
    "all_variants",
    "all_bundles",
    "cip_value",
    "cip_type",
    "from_date",
    "to_date",
    "cip_reason_type",
    "cip_reason_detail",
]


def _format_decimal(value: str) -> str:
    cleaned = value.replace(",", ".").strip()
    try:
        dec = Decimal(cleaned)
    except InvalidOperation:
        return cleaned
    normalized = dec.normalize()
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))
    return format(normalized, "f").rstrip("0").rstrip(".")


def _format_cip_value(cip_value: str, cip_type: str) -> str:
    cleaned = cip_value.replace(",", ".").strip()
    try:
        dec = Decimal(cleaned)
    except InvalidOperation:
        return cleaned
    if cip_type in PERCENTAGE_TYPES:
        # Users enter percentages as whole numbers (e.g., 10 for 10%).
        # Only scale values that look like fractions (e.g., 0.1).
        if abs(dec) <= Decimal("1"):
            dec = dec * 100
    return _format_decimal(str(dec))


def _format_date(value: str) -> str:
    try:
        dt = date.fromisoformat(value)
    except ValueError:
        return value
    return dt.strftime("%Y-%m-%d")


def generate_csv(header: dict, article_rows: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, delimiter=",", lineterminator="\n")

    writer.writerow(CSV_HEADERS)

    for row in article_rows:
        writer.writerow([
            header["customer_number"],
            header["customer_home_store"],
            header["salesline"],
            row["article_number"],
            header["article_identifier_type"],
            header["cip_stores"],
            header["exclusive_cip"],
            header["all_variants"],
            header["all_bundles"],
            _format_cip_value(row["cip_value"], header["cip_type"]),
            header["cip_type"],
            _format_date(header["from_date"]),
            _format_date(header["to_date"]),
            header["cip_reason_type"],
            header["cip_reason_detail"],
        ])

    return output.getvalue()
