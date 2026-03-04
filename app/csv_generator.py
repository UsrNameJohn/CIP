# CSV-module om CSV-bestanden/tekst te kunnen schrijven.
import csv
# io.StringIO gebruiken we om een tekstbuffer te maken waar we 'in' kunnen schrijven
# alsof het een bestand is, en daarna de tekst kunnen ophalen.
import io
# 'date' gebruiken we om ISO-datums te parsen en weer netjes te formatteren.
from datetime import date
# Decimal gebruiken we om geld/percentages met vaste precisie te verwerken.
# InvalidOperation is de fout die optreedt als een string geen geldig getal is.
from decimal import Decimal, InvalidOperation


# Een set met CIP-types die percentages voorstellen.
# Handig om snel te testen of we procent-logica moeten toepassen.
PERCENTAGE_TYPES = {"DISCOUNT_PERCENTAGE", "MARKUP_PERCENTAGE"}

# De kolomnamen (header) voor het CSV-bestand.
# Dit bepaalt de volgorde van de velden in elke CSV-regel.
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
    """
    Zet een string om naar een strak geformatteerde decimale representatie:
    - Vervangt komma door punt (EU-notatie naar programmeer-notatie).
    - Probeert een Decimal te maken; als dat niet lukt, geef de originele (gestripte) string terug.
    - Normaliseert Decimal zodat overbodige nullen verdwijnen.
    - Als het een heel getal is (bijv. 10.0), geef dan '10' terug i.p.v. '10.0'.
    - Anders geef een 'plain' string zonder trailing nullen of punt.
    """
    # Eerst , -> . en spaties eraf
    cleaned = value.replace(",", ".").strip()
    try:
        dec = Decimal(cleaned)  # Probeer om te zetten naar Decimal (betrouwbaarder dan float)
    except InvalidOperation:
        # Geen geldig getal: retourneer de input (al opgeschoond), zodat de caller dit kan afhandelen
        return cleaned

    # normalize() haalt exponenten en overbodige nullen weg (bijv. Decimal('10.0') -> Decimal('10'))
    normalized = dec.normalize()

    # Als het een heel getal is na normalisatie, formatteren als integer-string
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))  # Forceer geen decimalen

    # Anders: 'f' geeft plain notatie; strip overbodige trailing nullen en eventueel losse punt
    return format(normalized, "f").rstrip("0").rstrip(".")


def _format_cip_value(cip_value: str, cip_type: str) -> str:
    """
    Formatteert de CIP-waarde afhankelijk van het CIP-type:
    - Vervangt komma door punt.
    - Probeert Decimal te maken; lukt dat niet, geef de opgeschoonde input terug.
    - Voor percentage-typen:
        Gebruikers vullen vaak '10' in voor 10%. Als ze '0.1' invullen (fractienotatie),
        dan schalen we dit *alleen* als het getal eruitziet als een fractie (|x| <= 1),
        dus 0.1 -> 10.
    - Resultaat wordt door _format_decimal gehaald om netjes te formatteren.
    """
    cleaned = cip_value.replace(",", ".").strip()
    try:
        dec = Decimal(cleaned)
    except InvalidOperation:
        # Geen geldig getal: laat door zoals het is (de validatie gebeurt elders)
        return cleaned

    if cip_type in PERCENTAGE_TYPES:
        # Als het absolute getal kleiner of gelijk is aan 1, interpreteren we het als fractie en schalen naar %
        # Voorbeelden:
        #  0.1  -> 10
        #  1    -> 100
        #  10   -> 10  (blijft 10, want niet <= 1)
        if abs(dec) <= Decimal("1"):
            dec = dec * 100

    # Retourneer als nette string zonder onnodige nullen
    return _format_decimal(str(dec))


def _format_date(value: str) -> str:
    """
    Probeert een ISO-datum (YYYY-MM-DD) te parsen en daarna
    als 'YYYY-MM-DD' te formatteren (consistentie).
    Als parsen mislukt, geven we de originele string terug.
    """
    try:
        dt = date.fromisoformat(value)  # Verwacht 'YYYY-MM-DD'
    except ValueError:
        return value  # Onbekend formaat: laat staan zoals het is
    return dt.strftime("%Y-%m-%d")


def generate_csv(header: dict, article_rows: list[dict]) -> str:
    """
    Bouwt de volledige CSV-tekst op in geheugen en geeft die als string terug.

    Parameters:
    - header: dict met formulierwaarden (customer_number, dates, cip_type, etc.)
    - article_rows: lijst met dicts met minimaal:
        * 'article_number'
        * 'cip_value'

    Werking:
    - Schrijft eerst de CSV headers.
    - Voor elke artikelrij schrijft hij één CSV-regel waarin:
        * bepaalde velden uit 'header' worden overgenomen
        * waarden netjes worden geformatteerd (cip_value / datums)
    """
    # Maak een in-memory tekstbuffer. Hierin schrijven we CSV-tekst.
    output = io.StringIO()

    # CSV writer die in onze buffer schrijft, met komma-gescheiden velden en UNIX newlines.
    writer = csv.writer(output, delimiter=",", lineterminator="\n")

    # Schrijf de headerregel
    writer.writerow(CSV_HEADERS)

    # Loop door alle artikelregels en schrijf telkens een CSV-regel
    for row in article_rows:
        writer.writerow([
            header["customer_number"],                         # klantnummer
            header["customer_home_store"],                     # klant-winkel (home store)
            header["salesline"],                               # FSD/CC
            row["article_number"],                             # artikelnummer uit de rij
            header["article_identifier_type"],                 # SUBSYS/MGB
            header["cip_stores"],                              # één of meerdere stores (bijv. '1|2|52')
            header["exclusive_cip"],                           # TRUE/FALSE
            header["all_variants"],                            # TRUE/FALSE
            header["all_bundles"],                             # TRUE/FALSE
            _format_cip_value(row["cip_value"], header["cip_type"]),  # CIP-waarde netjes geformatteerd
            header["cip_type"],                                # type (percentage/relatief/fixed/etc.)
            _format_date(header["from_date"]),                 # startdatum in YYYY-MM-DD
            _format_date(header["to_date"]),                   # einddatum in YYYY-MM-DD
            header["cip_reason_type"],                         # reden-code
            header["cip_reason_detail"],                       # optionele reden toelichting
        ])

    # Haal de volledige CSV-tekst uit de buffer
    return output.getvalue()
