from fastapi import FastAPI, Form
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from app.csv_generator import generate_csv
import io

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
def generate(
    customer_number: str = Form(...),
    customer_store: str = Form(...),
    from_date: str = Form(...),
    to_date: str = Form(...)
):
    csv_content = generate_csv(
        customer_number,
        customer_store,
        from_date,
        to_date
    )

    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=CIP_bulk_upload.csv"
        }
    )

