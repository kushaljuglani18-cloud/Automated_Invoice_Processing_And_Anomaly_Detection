# create_samples.py
# Creates repeatable labelled and tabular invoice samples.
# Generated files go under sample_invoices/generated so manually added samples
# in sample_invoices are not overwritten.

import csv
import os
import random

from PIL import Image, ImageDraw, ImageFont


RANDOM_SEED = 42
OUTPUT_DIR = os.path.join("sample_invoices", "generated")
EXPECTED_RESULTS_FILE = os.path.join(OUTPUT_DIR, "expected_results.csv")

random.seed(RANDOM_SEED)


def create_sample_invoice(filename, invoice_lines):
    """
    Creates a simple white invoice image with OCR-friendly text.
    """
    img = Image.new("RGB", (1600, 2200), color="white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=36)

    y_position = 80
    for line in invoice_lines:
        draw.text((80, y_position), line, fill="black", font=font)
        y_position += 60

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    img.save(filename, dpi=(300, 300))
    print(f"Created: {filename}")


def build_labelled_invoice_lines(inv_number, date, vendor, line_items, grand_total):
    """
    Builds the older line-by-line invoice format.
    line_items = list of (description, qty, unit_price, optional_line_total)
    """
    lines = [
        "INVOICE",
        "====================",
        f"Invoice Number: {inv_number}",
        f"Invoice Date: {date}",
        f"Vendor Name: {vendor}",
        "",
        "Line Items:",
    ]

    for item in line_items:
        description, qty, unit_price, line_total = normalize_item(item)
        lines += [
            f"Description: {description}",
            f"Quantity: {qty}",
            f"Unit Price: {unit_price:.2f}",
            f"Line Total: {line_total:.2f}",
            "",
        ]

    lines += [
        "====================",
        f"Grand Total: {grand_total:.2f}",
    ]
    return lines


def build_table_invoice_lines(inv_number, date, vendor, line_items, grand_total):
    """
    Builds a true table-style invoice to exercise OCR table parsing.
    """
    lines = [
        "INVOICE",
        "",
        f"Invoice ID: {inv_number}",
        f"Vendor: {vendor}",
        f"Date: {date}",
        "",
        "Description              Qty   Unit Price   Line Total",
    ]

    for item in line_items:
        description, qty, unit_price, line_total = normalize_item(item)
        lines.append(
            f"{description:<24}{qty:>3}   {unit_price:>10.2f}   {line_total:>10.2f}"
        )

    lines += [
        "",
        f"Grand Total: ${grand_total:.2f}",
    ]
    return lines


def normalize_item(item):
    """
    Accepts either (description, qty, unit_price) or
    (description, qty, unit_price, line_total).
    """
    if len(item) == 3:
        description, qty, unit_price = item
        line_total = qty * unit_price
    else:
        description, qty, unit_price, line_total = item

    return description, qty, float(unit_price), float(line_total)


def item_sum(line_items):
    return sum(normalize_item(item)[3] for item in line_items)


def random_date(start_day=1, end_day=24, month="06", year="2026"):
    day = random.randint(start_day, end_day)
    return f"{day:02d}/{month}/{year}"


def random_line_items(profile, min_items=1, max_items=3):
    item_count = random.randint(min_items, max_items)
    descriptions = random.sample(profile["descriptions"], item_count)
    line_items = []

    for description in descriptions:
        qty = random.randint(*profile["qty_range"])
        unit_price = round(random.uniform(*profile["price_range"]), 2)
        line_items.append((description, qty, unit_price))

    return line_items


def add_invoice(samples, inv_number, date, vendor, line_items, style="table",
                grand_total=None, expected_math_valid=True, expected_rule="None"):
    if grand_total is None:
        grand_total = item_sum(line_items)

    samples.append({
        "invoice_number": inv_number,
        "date": date,
        "vendor": vendor,
        "line_items": line_items,
        "grand_total": grand_total,
        "style": style,
        "expected_math_valid": expected_math_valid,
        "expected_rule_anomaly": expected_rule,
    })


def build_samples():
    vendor_profiles = {
        "TechSupplies Co.": {
            "descriptions": ["Office Laptops", "Monitors", "Keyboards", "Webcams", "Docking Stations"],
            "qty_range": (1, 10),
            "price_range": (25.00, 700.00),
        },
        "OfficeMart Ltd.": {
            "descriptions": ["Office Chairs", "Desk Lamps", "Stationery Pack", "Filing Cabinets", "Whiteboards"],
            "qty_range": (2, 25),
            "price_range": (10.00, 200.00),
        },
        "GlobalParts Inc.": {
            "descriptions": ["Network Switches", "Cables and Adapters", "Routers", "Server Racks"],
            "qty_range": (2, 25),
            "price_range": (15.00, 450.00),
        },
        "Skyline Logistics": {
            "descriptions": ["Freight Services", "Warehouse Rental", "Delivery Services"],
            "qty_range": (1, 3),
            "price_range": (500.00, 7500.00),
        },
    }

    samples = []
    counter = 1

    for vendor, profile in vendor_profiles.items():
        for _ in range(8):
            inv_number = f"INV-GEN-2026-{counter:03d}"
            style = "table" if counter % 2 else "labelled"
            add_invoice(
                samples,
                inv_number,
                random_date(),
                vendor,
                random_line_items(profile),
                style=style,
            )
            counter += 1

    add_invoice(
        samples,
        "INV-GEN-TABLE-VALID",
        "20/06/2026",
        "TechSupplies Co.",
        [("Monitor", 2, 275.00), ("Keyboard", 5, 55.00), ("Mouse", 5, 25.00)],
        style="table",
    )

    add_invoice(
        samples,
        "INV-GEN-BAD-LINE",
        "21/06/2026",
        "OfficeMart Ltd.",
        [("Office Chair", 4, 220.00), ("Desk Lamp", 6, 45.00, 999.00)],
        style="table",
        grand_total=1879.00,
        expected_math_valid=False,
        expected_rule="Line-item math does not match invoice total",
    )

    add_invoice(
        samples,
        "INV-GEN-BAD-GRAND",
        "22/06/2026",
        "GlobalParts Inc.",
        [("Bearing", 20, 82.00), ("Bolt Pack", 10, 35.00)],
        style="table",
        grand_total=2500.00,
        expected_math_valid=False,
        expected_rule="Line-item math does not match invoice total",
    )

    duplicate_items = [("Network Switches", 5, 420.00)]
    add_invoice(
        samples,
        "INV-GEN-DUP-A",
        "23/06/2026",
        "GlobalParts Inc.",
        duplicate_items,
        style="table",
        expected_rule="Possible duplicate invoice details",
    )
    add_invoice(
        samples,
        "INV-GEN-DUP-B",
        "23/06/2026",
        "GlobalParts Inc.",
        duplicate_items,
        style="table",
        expected_rule="Possible duplicate invoice details",
    )

    add_invoice(
        samples,
        "INV-GEN-HIGH-AMOUNT",
        "24/06/2026",
        "TechSupplies Co.",
        [("Server Equipment", 1, 15000.00)],
        style="table",
    )

    add_invoice(
        samples,
        "INV-GEN-FUTURE-DATE",
        "25/12/2026",
        "Skyline Logistics",
        [("Warehouse Rental", 1, 5400.00)],
        style="table",
        expected_rule="Invoice date is in the future",
    )

    return samples


def write_expected_results(samples):
    with open(EXPECTED_RESULTS_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "invoice_number",
                "style",
                "expected_math_valid",
                "expected_rule_anomaly",
            ],
        )
        writer.writeheader()
        for sample in samples:
            writer.writerow({
                "invoice_number": sample["invoice_number"],
                "style": sample["style"],
                "expected_math_valid": sample["expected_math_valid"],
                "expected_rule_anomaly": sample["expected_rule_anomaly"],
            })

    print(f"Created: {EXPECTED_RESULTS_FILE}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    samples = build_samples()

    for sample in samples:
        if sample["style"] == "labelled":
            lines = build_labelled_invoice_lines(
                sample["invoice_number"],
                sample["date"],
                sample["vendor"],
                sample["line_items"],
                sample["grand_total"],
            )
        else:
            lines = build_table_invoice_lines(
                sample["invoice_number"],
                sample["date"],
                sample["vendor"],
                sample["line_items"],
                sample["grand_total"],
            )

        filename = os.path.join(OUTPUT_DIR, f"{sample['invoice_number']}.png")
        create_sample_invoice(filename, lines)

    write_expected_results(samples)
    print(f"\nAll {len(samples)} generated sample invoices created successfully.")
    print(f"Manual samples in sample_invoices were left untouched.")


if __name__ == "__main__":
    main()
