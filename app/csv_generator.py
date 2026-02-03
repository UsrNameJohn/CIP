import csv
import io

def generate_csv(customer_number, customer_store, from_date, to_date):
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    # Example structure — will be aligned 1:1 with Excel
    writer.writerow(["HDR", customer_number])
    writer.writerow([
        "DTL",
        customer_store,
        from_date,
        to_date
    ])
    writer.writerow(["TRL", "END"])

    return output.getvalue()

