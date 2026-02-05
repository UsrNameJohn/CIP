# CIP Bulk Upload Web Tool

Web app that replaces the Excel bulk CIP template with a fast, validated UI and CSV export.

## Run locally
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000`.

## Render deploy
This repo is ready for Render Auto‑Deploy. After pushing to GitHub, Render will deploy the latest commit.

## Validation notes
- Salesline `CC` forces **All variants** and **All bundles** to `FALSE`.
- For percentage types, enter whole numbers (e.g. `10` = 10%).
- CIP stores are single‑select and filtered by salesline.

## CSV output
Filename format:
```
<homestore>-<customernumber>-<YYYY-MM-DD>-<numberofentries>.csv
```
Columns:
```
customer_number,customer_store,salesline,article_identifier,article_identifier_type,cip_store,exclusive_cip,all_variants,all_bundles,cip_value,cip_type,from_date,to_date,cip_reason_type,cip_reason_detail
```
