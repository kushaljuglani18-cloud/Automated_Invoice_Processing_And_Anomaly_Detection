# parser.py
# Station 3: Extract specific fields from raw OCR text

import re  # re = Regular Expressions, built into Python
import pandas as pd  # Pandas = for creating DataFrames (tables)


MONEY_RE = r'[₹$€£]?\s*[\d,]+(?:\.\d{1,2})?'
QTY_RE = r'\d{1,4}\.?|[iIl|]'


def parse_money(value):
    """
    Converts OCR money text like '$2,200' or '275.00' into a float.
    """
    if value is None:
        return None

    cleaned = re.sub(r'[^\d.]', '', value)
    if not cleaned:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_quantity_value(value):
    """
    Converts quantity text into an int, including common OCR mistakes where
    a single 1 is read as i, I, l, or |.
    """
    if value is None:
        return None

    cleaned = value.strip().rstrip(".")
    if re.fullmatch(r'[iIl|]', cleaned):
        return 1

    if re.fullmatch(r'\d{1,4}', cleaned):
        return int(cleaned)

    return None

def extract_invoice_number(text):
    """
    Now looks for multiple patterns:
    - INV-2024-001 (ideal)
    - Any sequence that looks like an invoice number
    """
    # Try exact pattern first
    pattern1 = r'INV-[\w-]+'
    match = re.search(pattern1, text, re.IGNORECASE)
    if match:
        return match.group()

    # Try looser pattern - "Number:" followed by anything
    pattern2 = r'(?:Number|Naber|Numbe|ID)[:\s]*([\w-]+)'
    match = re.search(pattern2, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return "NOT FOUND"


def extract_date(text):
    """
    Looks for date patterns in multiple formats.
    """
    
    pattern1 = r'\d{2}[/.-]\d{2}[/.-]\d{4}'
    match = re.search(pattern1, text)
    if match:
        return match.group()

    pattern2 = r'\d{8}'
    match = re.search(pattern2, text)
    if match:
        raw = match.group()
        # Reformat it as DD/MM/YYYY
        return f"{raw[:2]}/{raw[2:4]}/{raw[4:]}"
    
    pattern3 = r'\d{4}[/.-]\d{2}[/.-]\d{2}'
    match = re.search(pattern3, text)
    if match:
        parts = re.split(r'[/.-]', match.group())
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    
    return "NOT FOUND"

    
def extract_amounts(text):
    """
    Looks for all money amounts like 2750.00 or 500.00
    """
    amount_pattern = r'[₹$€£]\s*[\d,]+(?:\.\d{1,2})?|\d+\.\d{2}'
    matches = re.findall(amount_pattern, text)
    return [match.strip() for match in matches if re.search(r'\d', match)]


def extract_vendor(text):
    """
    Extract vendor name. Handles:
    - 'Vendor Name: TechSupplies Co.'
    - 'Vendor: TechSupplies Co.'
    """
    pattern1 = r'Vendor\s+Name[:\s]+(.+)'
    match = re.search(pattern1, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    pattern2 = r'Vendor[:\s]+(.+)'
    match = re.search(pattern2, text, re.IGNORECASE)
    if match:
        result = match.group(1).strip()
        if result.lower().startswith('name'):
            result = re.sub(r'^[Nn]ame[:\s]+', '', result).strip()
        return result
    
    return "NOT FOUND"


def extract_grand_total(text):
    """
    Looks for Grand Total with flexible matching.
    Handles OCR errors like "Grand Toth" or "Grend Total"
    Also handles formats:
    - 'Grand Total: 2200.00'
    - 'Grand Total: $2,200
    - 'Grand Total: 
    """
    pattern = r'(?:Grand|Grend|Grana)\s+(?:Total|Toth|Totsl)[:\s]*[₹$€£]?\s*([\d,]+\.?\d*)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        amount = parse_money(match.group(1))
        return amount if amount is not None else 0.0

    all_amounts = [parse_money(match) for match in re.findall(MONEY_RE, text)]
    all_amounts = [amount for amount in all_amounts if amount is not None]
    if all_amounts:
        return all_amounts[-1]

    return 0.0


def extract_quantity(text):
    """
    Handles:
    - 'Quantity: 8'     (labeled, our synthetic format)
    - 'Monitors 8'      (tabular format - description followed by number)
    """
    pattern1 = r'(?:Quantity|Qty|Ouneey|Ounety)[:\s]*(\d+)'
    match = re.search(pattern1, text, re.IGNORECASE)
    if match:
        return int(match.group(1))

    pattern2 = r'^[A-Za-z\s]+\b(\d{1,3})\s*$'
    match = re.search(pattern2, text, re.MULTILINE)
    if match:
        return int(match.group(1))

    return None


def extract_unit_price(text):
    """
    Handles:
    - 'Unit Price: 275.00'   (labeled)
    - '$275'                 (standalone dollar amount)
    """
    pattern1 = r'(?:Unit\s*Pr[a-z]*)[:\s]*[₹$€£]?\s*([\d,]+\.?\d*)'
    match = re.search(pattern1, text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(',', ''))

    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if re.match(r'^\$[\d,]+\.?\d*$', line):
            return parse_money(line)

    return None

def extract_line_total(text):
    """
    Looks for 'Line Total: 2500.00' style lines.
    Handles OCR misreading 'Line' as 'Une', 'Lne', etc.
    """
    pattern = r'(?:Line|Une|Lne|L1ne)\s*Tot[a-z]*[:\s]*\[?\$?(\d+\.?\d*)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return parse_money(match.group(1))
    return None


def _is_table_noise(line):
    noise_patterns = [
        r'^invoice\b',
        r'^invoice\s+(id|number|date)',
        r'^vendor\b',
        r'^date\b',
        r'^description\b',
        r'^qty\b',
        r'^unit\s+price\b',
        r'^total\b',
        r'^line\s+items\b',
        r'^grand\s+total\b',
        r'^=+$',
    ]
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in noise_patterns)


def _make_item(description, qty, unit_price, line_total=None):
    if line_total is None and qty is not None and unit_price is not None:
        line_total = qty * unit_price

    return {
        "description": description.strip(" :-,.") or "Unknown",
        "qty": qty,
        "unit_price": unit_price,
        "line_total": line_total,
    }


def _clean_table_line(line):
    """
    Removes small OCR artifacts that appear before table rows, such as a comma
    at the start of ', Keyboard 5 55 275'.
    """
    return re.sub(r'^[^\w₹$€£]+', '', line).strip()


def extract_tabular_line_items(text):
    """
    Extracts line items from standard table OCR output, for example:
    'Office Chairs 10 $190 $1,900'
    or a split OCR pair:
    'Office Chairs 10'
    '$190 $1,900'
    """
    items = []
    lines = [
        _clean_table_line(line)
        for line in text.splitlines()
        if _clean_table_line(line)
    ]

    direct_row = re.compile(
        rf'^(?P<description>[A-Za-z][A-Za-z0-9 &/.,()-]*?)\s+'
        rf'(?P<qty>{QTY_RE})\s+'
        rf'(?P<unit>{MONEY_RE})'
        rf'(?:\s+(?P<total>{MONEY_RE}))?\s*$',
        re.IGNORECASE
    )
    desc_qty_row = re.compile(
        rf'^(?P<description>[A-Za-z][A-Za-z0-9 &/.,()-]*?)\s+(?P<qty>{QTY_RE})\s*$',
        re.IGNORECASE
    )
    money_only_row = re.compile(rf'^(?P<amounts>{MONEY_RE}(?:\s+{MONEY_RE})*)\s*$')

    for index, line in enumerate(lines):
        if _is_table_noise(line):
            continue

        match = direct_row.match(line)
        if match:
            qty = parse_quantity_value(match.group("qty"))
            unit_price = parse_money(match.group("unit"))
            line_total = parse_money(match.group("total"))
            items.append(_make_item(match.group("description"), qty, unit_price, line_total))
            continue

        match = desc_qty_row.match(line)
        if not match:
            continue

        next_money_line = None
        for next_line in lines[index + 1:index + 5]:
            if _is_table_noise(next_line):
                continue
            if money_only_row.match(next_line):
                next_money_line = next_line
                break

        if not next_money_line:
            continue

        amounts = [parse_money(value) for value in re.findall(MONEY_RE, next_money_line)]
        amounts = [amount for amount in amounts if amount is not None]
        if not amounts:
            continue

        qty = parse_quantity_value(match.group("qty"))
        unit_price = amounts[0]
        line_total = amounts[1] if len(amounts) > 1 else None
        items.append(_make_item(match.group("description"), qty, unit_price, line_total))

    return items


def extract_line_items(text):
    """
    Extracts ALL line items from an invoice by finding every
    'Description:' block and parsing qty/price/total within each.

    Returns a list of dictionaries, one per line item:
    [
        {"description": "Laptops", "qty": 5, "unit_price": 650.0, "line_total": 3250.0},
        {"description": "Keyboards", "qty": 10, "unit_price": 25.0, "line_total": 250.0},
    ]
    """
    items = []

    # Split text into blocks — each starting at "Description:"
    blocks = re.split(r'(?=Description:)', text, flags=re.IGNORECASE)

    for block in blocks:
        if not re.search(r'Description:', block, re.IGNORECASE):
            continue  # skip blocks with no description (header text etc.)

        # Extract description
        desc_match = re.search(r'Description:\s*(.+)', block, re.IGNORECASE)
        desc = desc_match.group(1).strip() if desc_match else "Unknown"

        # Extract quantity
        qty_match = re.search(
            r'(?:Quantity|Qty|Ouneey|Ounety)[:\s]*(\d+)',
            block, re.IGNORECASE
        )
        qty = int(qty_match.group(1)) if qty_match else None

        # Extract unit price
        price_match = re.search(
            r'(?:Unit\s*Pr[a-z]*)[:\s]*\$?(\d+\.?\d*)',
            block, re.IGNORECASE
        )
        unit_price = parse_money(price_match.group(1)) if price_match else None

        # Extract line total
        total_match = re.search(
            r'(?:Line|Une|Lne)\s*Tot[a-z]*[:\s]*\$?(\d+\.?\d*)',
            block, re.IGNORECASE
        )
        line_total = parse_money(total_match.group(1)) if total_match else None

        items.append(_make_item(desc, qty, unit_price, line_total))

    if items:
        return items

    return extract_tabular_line_items(text)


def corrected_grand_total(raw_text, line_items):
    """
    Uses line item totals only when the Grand Total OCR line is visibly damaged
    or missing. Normal mismatches are left alone so validation can flag them.
    """
    grand_total = extract_grand_total(raw_text)
    item_totals = [
        item.get("line_total")
        for item in line_items
        if item.get("line_total") is not None
    ]
    if not item_totals:
        return grand_total

    calculated_total = sum(item_totals)
    grand_total_line = re.search(r'Grand\s+Total[^\n]*', raw_text, re.IGNORECASE)
    grand_total_text = grand_total_line.group() if grand_total_line else ""
    amount_text = grand_total_text.split(":", 1)[-1] if ":" in grand_total_text else grand_total_text
    looks_corrupted = bool(re.search(r'[!|IlOo]', amount_text))

    if grand_total == 0 or (looks_corrupted and abs(calculated_total - grand_total) > 1.0):
        return calculated_total

    return grand_total


def parse_invoice(raw_text, invoice_id):
    """
    THE MAIN FUNCTION - runs all extractions and returns
    a dictionary representing one invoice row.
    Now supports multiple line items.
    """
    line_items = extract_line_items(raw_text)

     # For backward compatibility with anomaly detector,
    # we store first item's qty/price/total as top-level fields
    # AND store all items as a list for validation
    first_item = line_items[0] if line_items else {}

    grand_total = corrected_grand_total(raw_text, line_items)

    invoice_data = {
        "invoice_id":       invoice_id,
        "invoice_number":   extract_invoice_number(raw_text),
        "date":             extract_date(raw_text),
        "vendor":           extract_vendor(raw_text),
        "quantity":         first_item.get("qty") or extract_quantity(raw_text),
        "unit_price":       first_item.get("unit_price") or extract_unit_price(raw_text),
        "line_total":       first_item.get("line_total") or extract_line_total(raw_text),
        "grand_total":      grand_total,
        "line_items":       line_items,
        "num_line_items":   len(line_items),
        "all_amounts":      extract_amounts(raw_text),
        "raw_text":         raw_text
    }
    return(invoice_data)


def build_dataframe(list_of_invoices):
    """
    Takes a list of invoice dictionaries and converts
    them into a pandas DataFrame - like an Excel table.
    Each invoice = one row.
    Each field = one column.
    """
    df = pd.DataFrame(list_of_invoices)
    return df
