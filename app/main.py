# ===== Imports =====
# De 'date' klasse gebruiken we straks om datums te valideren.
from datetime import date

# FastAPI is het webframework. 'Form' gebruiken we om waarden uit HTML forms op te halen.
from fastapi import FastAPI, Form

# HTMLResponse: hiermee geef je HTML terug in de browser.
# StreamingResponse: hiermee kunnen we bestanden (zoals CSV) als download terugsturen.
from fastapi.responses import HTMLResponse, StreamingResponse

# Jinja2Templates: hiermee kunnen we HTML templates gebruiken met variabelen erin.
# Request: nodig om informatie over het HTTP‑verzoek door te geven aan templates.
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

# StaticFiles: hiermee kunnen we een map met CSS/JS bestanden publiceren.
from fastapi.staticfiles import StaticFiles

# OS-module om veilige padnamen te maken en mappen te controleren.
import os

# Dit is een eigen module met een functie die de CSV inhoud genereert.
from app.csv_generator import generate_csv

# IO gebruiken we om tekst te behandelen alsof het een bestand is (handig voor downloads).
import io


# ===== App initialisatie =====

# Hiermee maak je de FastAPI webapplicatie aan.
app = FastAPI()

# We geven aan waar de HTML template bestanden staan.
templates = Jinja2Templates(directory="app/templates")

# We bouwen een pad naar de 'static' map met CSS/JS bestanden.
static_dir = os.path.join(os.path.dirname(__file__), "static")

# Alleen als de map bestaat wordt hij onder /static gepubliceerd.
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ===== Vaste lijsten =====
# Hieronder staan lijsten met vaste keuzes. Deze gebruiken we in dropdowns
# en ook in de validatie van het formulier.

SALES_LINES = ["FSD", "CC"]
ARTICLE_IDENTIFIER_TYPES = ["SUBSYS", "MGB"]
BOOLEAN_CHOICES = ["TRUE", "FALSE"]

CIP_TYPES = [
    "DISCOUNT_PERCENTAGE",
    "DISCOUNT_RELATIVE",
    "MARKUP_PERCENTAGE",
    "MARKUP_RELATIVE",
    "FIXED",
]

HOME_STORES = [
    "1", "2", "3", "4", "5", "6", "7", "8", "10",
    "51", "52", "53", "54", "55", "56", "57", "58", "59",
]

CIP_REASON_TYPES = [
    "COMPETITORS_PRICING",
    "NEW_ARTICLE_INTRODUCTION",
    "CUSTOMER_RETENTION",
    "WIN_BACK_LOST_CUSTOMERS",
    "GAIN_A_NEW_CUSTOMER",
    "PRICE_STABILITY",
    "CLOSE_A_DEAL",
    "OTHER_REASON",
]

# STORE lijst voor achterliggende validatie & dropdowns
STORES = [
    {"name": "Depot", "number": "86", "groups": ["fsd"]},
    {"name": "Depot II", "number": "84", "groups": ["fsd"]},
    {"name": "Amsterdam", "number": "1", "groups": ["cc"]},
    {"name": "Delft", "number": "2", "groups": ["cc"]},
    {"name": "Breda", "number": "3", "groups": ["cc"]},
    {"name": "Nuth", "number": "4", "groups": ["cc"]},
    {"name": "Best", "number": "5", "groups": ["cc"]},
    {"name": "Duiven", "number": "6", "groups": ["cc"]},
    {"name": "Hengelo", "number": "7", "groups": ["cc"]},
    {"name": "Vianen", "number": "8", "groups": ["cc"]},
    {"name": "Groningen", "number": "10", "groups": ["cc"]},
    {"name": "Leeuwarden", "number": "52", "groups": ["cc", "fsd"]},
    {"name": "Nieuwegein", "number": "53", "groups": ["cc"]},
    {"name": "Beverwijk", "number": "54", "groups": ["cc"]},
    {"name": "Barendrecht", "number": "55", "groups": ["cc"]},
    {"name": "Nijmegen", "number": "56", "groups": ["cc"]},
    {"name": "Den Bosch", "number": "57", "groups": ["cc"]},
    {"name": "Wateringen", "number": "58", "groups": ["cc"]},
]


# ===== Helper functies =====

def _normalize_article_rows(article_numbers, cip_values) -> list[dict]:
    """
    Deze functie combineert artikel- en CIP-waarden per regel.
    - haalt spaties weg
    - verwijdert % tekens
    - slaat lege regels over
    """
    rows = []

    # Loop door alle ingevoerde artikelen
    for idx in range(len(article_numbers)):
        article = (article_numbers[idx] or "").strip()
        value = (cip_values[idx] or "").strip()

        # Verwijder % tekens zodat Excel-plakfouten geen problemen geven
        value = value.replace("%", "").strip()

        # Lege regels overslaan
        if not article and not value:
            continue

        # Bouw een net record per regel
        rows.append({
            "row": idx + 1,                # Regelnummer (voor foutmeldingen)
            "article_number": article,     # Artikelnummer
            "cip_value": value,            # Bijbehorende CIP waarde
        })

    return rows


def _valid_store_numbers_for_salesline(salesline: str) -> set[str]:
    """
    Geeft terug welke winkelcodes toegestaan zijn voor een bepaalde salesline.
    """
    if salesline == "FSD":
        return {"52", "86", "84"}  # FSD winkels

    if salesline == "CC":
        return {
            "1", "2", "3", "4", "5", "6", "7", "8", "10",
            "52", "53", "54", "55", "56", "57", "58",
        }

    return set()  # Geen geldige output → iets klopt niet.


def _validate_form(data: dict) -> list[str]:
    """
    Controleert ALLE velden uit het formulier.
    Retourneert een lijst met foutmeldingen.
    """
    errors = []

    # === Home store checken ===
    customer_home_store = data.get("customer_home_store", "").strip()
    if customer_home_store not in HOME_STORES:
        errors.append("Customer home store must be one of the allowed store numbers.")

    # === Klantnummer checken ===
    customer_number = data.get("customer_number", "").strip()
    if not customer_number.isdigit() or len(customer_number) > 6:
        errors.append("Customer number must be numeric and at most 6 digits.")

    # === Salesline checken ===
    salesline = data.get("salesline", "").strip()
    if salesline not in SALES_LINES:
        errors.append("Salesline must be FSD or CC.")

    # === Artikel identifier type ===
    article_identifier_type = data.get("article_identifier_type", "").strip()
    if article_identifier_type not in ARTICLE_IDENTIFIER_TYPES:
        errors.append("Article identifier type must be SUBSYS or MGB.")

    # === CIP stores ===
    cip_stores = data.get("cip_stores", "").strip()
    if not cip_stores:
        errors.append("Please choose CIP store(s).")
    else:
        allowed = _valid_store_numbers_for_salesline(salesline)
        selected = {store for store in cip_stores.split("|") if store}

        if allowed and not selected.issubset(allowed):
            errors.append("Selected stores are not valid for the chosen salesline.")

    # === Boolean velden ===
    for key, label in [
        ("exclusive_cip", "Exclusive CIP"),
        ("all_variants", "All variants"),
        ("all_bundles", "All bundles"),
    ]:
        value = data.get(key, "").strip()
        if value not in BOOLEAN_CHOICES:
            errors.append(f"{label} must be TRUE or FALSE.")

    # === CC regels ===
    if salesline == "CC":
        # CC mag geen 'all variants' gebruiken
        if data.get("all_variants", "").strip() != "FALSE":
            errors.append("All variants must be FALSE for CC.")
        if data.get("all_bundles", "").strip() != "FALSE":
            errors.append("All bundles must be FALSE for CC.")

    # === CIP type ===
    cip_type = data.get("cip_type", "").strip()
    if cip_type not in CIP_TYPES:
        errors.append("CIP type is invalid.")

    # === Datum validatie ===
    from_date = data.get("from_date", "").strip()
    to_date = data.get("to_date", "").strip()

    try:
        from_dt = date.fromisoformat(from_date)
    except ValueError:
        errors.append("From date must be a valid date.")
        from_dt = None

    try:
        to_dt = date.fromisoformat(to_date)
    except ValueError:
        errors.append("To date must be a valid date.")
        to_dt = None

    if from_dt and to_dt and from_dt > to_dt:
        errors.append("From date cannot be after To date.")

    # === Reden + reden detail ===
    reason = data.get("cip_reason_type", "").strip()
    if reason not in CIP_REASON_TYPES:
        errors.append("Reason must be one of the allowed values.")

    reason_detail = data.get("cip_reason_detail", "").strip()
    if reason == "OTHER_REASON" and not reason_detail:
        errors.append("Reason detail is required when Reason is OTHER_REASON.")

    # === Artikel regels ===
    article_rows = data.get("article_rows", [])
    if not article_rows:
        errors.append("Please add at least one article row.")

    # Artikel + CIP waarde validatie
    for row in article_rows:
        article = row["article_number"]
        value = row["cip_value"]

        # artikelnummer moet alleen cijfers bevatten
        if not article.isdigit():
            errors.append(f"Article # on row {row['row']} must be numeric.")

        # CIP waarde moet een getal zijn (komma wordt punt)
        try:
            float(value.replace(",", "."))
        except ValueError:
            errors.append(f"CIP value on row {row['row']} must be numeric.")

    return errors


def _render_form(request: Request, errors: list[str], form: dict, article_rows: list[dict]):
    """
    Render de HTML pagina opnieuw met:
    - fouten
    - huidige invoer
    - dropdown opties
    - artikelregels
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "errors": errors,
            "success": None,
            "form": form,
            "sales_lines": SALES_LINES,
            "article_identifier_types": ARTICLE_IDENTIFIER_TYPES,
            "boolean_choices": BOOLEAN_CHOICES,
            "cip_types": CIP_TYPES,
            "home_stores": HOME_STORES,
            "cip_reason_types": CIP_REASON_TYPES,
            "stores": STORES,
            "article_rows": article_rows,
        },
    )


def _build_filename(form: dict, line_count: int) -> str:
    """
    Bouwt een bestandsnaam voor het CSV bestand, zoals:
    1-123456-2026-03-04-5.csv
    """
    today = date.today().strftime("%Y-%m-%d")
    customer_number = form["customer_number"]
    home_store = form["customer_home_store"]
    return f"{home_store}-{customer_number}-{today}-{line_count}.csv"


# ===== Routes =====

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    Laat de beginpagina zien met een leeg formulier.
    """
    return _render_form(request, [], {}, [])


@app.post("/generate", response_class=HTMLResponse)
def generate(
    request: Request,
    customer_home_store: str = Form(...),
    customer_number: str = Form(...),
    salesline: str = Form(...),
    article_identifier_type: str = Form(...),
    cip_stores: str = Form(...),
    exclusive_cip: str = Form(...),
    all_variants: str = Form(...),
    all_bundles: str = Form(...),
    cip_type: str = Form(...),
    from_date: str = Form(...),
    to_date: str = Form(...),
    cip_reason_type: str = Form(...),
    cip_reason_detail: str = Form(""),
    article_number: list[str] = Form([]),
    cip_value: list[str] = Form([]),
):
    """
    Dit is de POST route die wordt aangeroepen wanneer het formulier wordt verstuurd.
    Hier worden:
    - artikelregels verwerkt
    - gegevens gevalideerd
    - CSV gegenereerd bij succes
    """

    # Bouw nette artikelrecords
    article_rows = _normalize_article_rows(article_number, cip_value)

    # Verzamel alle formuliervelden in één dict
    form = {
        "customer_home_store": customer_home_store,
        "customer_number": customer_number,
        "salesline": salesline,
        "article_identifier_type": article_identifier_type,
        "cip_stores": cip_stores,
        "exclusive_cip": exclusive_cip,
        "all_variants": all_variants,
        "all_bundles": all_bundles,
        "cip_type": cip_type,
        "from_date": from_date,
        "to_date": to_date,
        "cip_reason_type": cip_reason_type,
        "cip_reason_detail": cip_reason_detail,
    }

    # Validatie uitvoeren
    errors = _validate_form({**form, "article_rows": article_rows})

    # Als er fouten zijn → formulier opnieuw renderen
    if errors:
        return _render_form(request, errors, form, article_rows)

    # CSV genereren (inhoud als tekst)
    csv_content = generate_csv(form, article_rows)

    # Bestandsnaam bouwen
    filename = _build_filename(form, len(article_rows))

    # Download terugsturen als CSV bestand
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
