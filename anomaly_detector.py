# anomaly_detector.py
# Station 4: Detect suspicious/anomalous invoices

from sklearn.ensemble import IsolationForest


DEFAULT_FEATURE_COLUMNS = [
    "grand_total",
    "num_line_items",
    "quantity",
    "unit_price",
    "line_total",
]


def calculate_zscore(df, column="grand_total", group_by="vendor"):
    """
    Calculates Z-score for each invoice amount, per vendor.
    """
    df["zscore"] = df.groupby(group_by)[column].transform(
        lambda x: (x - x.mean()) / x.std() if x.std() != 0 else 0
    )
    df["zscore"] = df["zscore"].fillna(0)
    return df


def run_isolation_forest(df, feature_columns=None, contamination=0.08):
    """
    Runs Isolation Forest on numeric invoice features.
    contamination=0.08 means "expect roughly 8% anomalies".
    """
    if feature_columns is None:
        feature_columns = [
            column for column in DEFAULT_FEATURE_COLUMNS
            if column in df.columns
        ]

    if len(df) < 2 or not feature_columns:
        df["anomaly_score"] = 1
        return df

    model = IsolationForest(contamination=contamination, random_state=42)
    X = df[feature_columns].fillna(0)
    df["anomaly_score"] = model.fit_predict(X)

    return df


def detect_duplicates(df):
    """
    Flags likely duplicate invoices using stronger keys than amount alone.
    """
    df["duplicate_invoice_number"] = (
        df["invoice_number"].ne("NOT FOUND")
        & df.duplicated(subset=["invoice_number"], keep=False)
    )

    comparable_columns = [
        column for column in [
            "vendor",
            "date",
            "grand_total",
            "num_line_items",
        ]
        if column in df.columns
    ]

    if comparable_columns:
        df["duplicate_invoice_details"] = df.duplicated(
            subset=comparable_columns,
            keep=False
        )
    else:
        df["duplicate_invoice_details"] = False

    df["is_duplicate"] = (
        df["duplicate_invoice_number"] | df["duplicate_invoice_details"]
    )
    return df


def build_rule_reasons(row):
    reasons = []

    if row.get("duplicate_invoice_number"):
        reasons.append("Duplicate invoice number")
    elif row.get("duplicate_invoice_details"):
        reasons.append("Possible duplicate invoice details")

    if row.get("math_valid") == False:
        reasons.append("Line-item math does not match invoice total")

    if row.get("date_status") == "FUTURE_DATE":
        reasons.append("Invoice date is in the future")
    elif row.get("date_status") == "TOO_OLD":
        reasons.append("Invoice date is older than the allowed range")

    return reasons


def build_ml_reasons(row):
    reasons = []

    if abs(row["zscore"]) > 1.5:
        reasons.append("Unusual amount for this vendor (Z-score)")

    if row["anomaly_score"] == -1:
        reasons.append("Flagged by Isolation Forest model")

    return reasons


def flag_anomalies(df):
    """
    Combines rule-based checks and statistical checks into anomaly columns.
    """
    df = calculate_zscore(df)
    df = run_isolation_forest(df)
    df = detect_duplicates(df)

    rule_reason_values = []
    ml_reason_values = []
    anomaly_reason_values = []
    is_anomaly_values = []

    for _, row in df.iterrows():
        rule_reasons = build_rule_reasons(row)
        ml_reasons = build_ml_reasons(row)
        all_reasons = rule_reasons + ml_reasons

        rule_reason_values.append("; ".join(rule_reasons) if rule_reasons else "None")
        ml_reason_values.append("; ".join(ml_reasons) if ml_reasons else "None")
        anomaly_reason_values.append("; ".join(all_reasons) if all_reasons else "None")
        is_anomaly_values.append(bool(all_reasons))

    df["rule_anomaly_reason"] = rule_reason_values
    df["ml_anomaly_reason"] = ml_reason_values
    df["anomaly_reason"] = anomaly_reason_values
    df["is_anomaly"] = is_anomaly_values

    return df
