# validator.py
# Rule-based checks - run BEFORE the ML model, catches simple logic errors

from datetime import datetime, timedelta


def check_math_integrity(row):
    """
    Now validates EVERY line item, not just the first one.
    Also checks that sum of all line totals = Grand Total.
    Returns True only if ALL checks pass.
    """
    line_items = row.get('line_items', [])
    grand_total = row.get('grand_total', 0)

    if not line_items:
        return None

    running_sum = 0
    for item in line_items:
        qty = item.get('qty')
        price = item.get('unit_price')
        total = item.get('line_total')

        if qty is None or price is None or total is None:
            return None 

        expected = qty * price
        if abs(expected - total) > 1.0:
            return False  

        running_sum += total

    if grand_total and abs(running_sum - grand_total) > 1.0:
        return False

    return True


def check_date_validity(row, max_age_days=90):
    """
    Flags invoices with future dates or dates older than max_age_days.
    Our dates are in DD/MM/YYYY format.
    """
    date_str = row.get('date')
    if date_str == "NOT FOUND" or date_str is None:
        return None  # Can't check

    try:
        invoice_date = datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        return None  # Date format couldn't be parsed

    today = datetime.now()

    if invoice_date > today:
        return "FUTURE_DATE"
    elif (today - invoice_date) > timedelta(days=max_age_days):
        return "TOO_OLD"
    else:
        return "VALID"


def run_validation(df):
    """
    THE MAIN FUNCTION - applies both checks to every row in the DataFrame
    and adds two new columns: math_valid and date_status
    """
    df['math_valid'] = df.apply(check_math_integrity, axis=1)
    df['date_status'] = df.apply(check_date_validity, axis=1)

    return df  