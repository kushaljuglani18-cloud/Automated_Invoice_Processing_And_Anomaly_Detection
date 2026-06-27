# main.py
from ocr_engine import extract_text_from_path
from parser import parse_invoice, build_dataframe
from anomaly_detector import flag_anomalies
from validator import run_validation
import os
import glob

invoice_files = sorted(glob.glob("sample_invoices/**/*.png", recursive=True))
print(f"Found {len(invoice_files)} invoices to process.\n")

all_invoices = []

for i, file_path in enumerate(invoice_files):
    print(f"Processing invoice {i+1}...")
    raw_text = extract_text_from_path(file_path, save_preprocessed=True)
    invoice_data = parse_invoice(raw_text, invoice_id=i+1)
    all_invoices.append(invoice_data)


df = build_dataframe(all_invoices)
df = run_validation(df)

df = flag_anomalies(df)

print("\n---- FINAL RESULTS ----")
print(df[["invoice_id", "invoice_number", "vendor", "grand_total", "math_valid", "date_status", "is_anomaly", "anomaly_reason"]])

os.makedirs("output", exist_ok=True)
output_columns = [
    "invoice_id",
    "invoice_number",
    "date",
    "vendor",
    "num_line_items",
    "quantity",
    "unit_price",
    "line_total",
    "grand_total",
    "math_valid",
    "date_status",
    "is_anomaly",
    "rule_anomaly_reason",
    "ml_anomaly_reason",
    "anomaly_reason",
]
df[output_columns].to_csv("output/processed_invoices.csv", index=False)

print("\nSaved to output/processed_invoices.csv")
print("Done!")
