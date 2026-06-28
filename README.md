# Automated Invoice Processing and Anomaly Detection

A end-to-end Python pipeline that digitizes invoice images, extracts structured 
financial data, validates mathematical integrity, and flags suspicious invoices 
using machine learning.

Built as a Data Science internship project.

---

## Pipeline Overview

| Module | File | Purpose |
|---|---|---|
| Image Preprocessing | `preprocessing.py` | Grayscale, noise reduction, binarization |
| OCR Engine | `ocr_engine.py` | Text extraction via Tesseract |
| Parser | `parser.py` | RegEx-based field extraction into DataFrame |
| Validator | `validator.py` | Math integrity and date validity checks |
| Anomaly Detector | `anomaly_detector.py` | Z-score + Isolation Forest ML model |
| Visualizer | `visualize.py` | Box plot and scatter plot generation |

---

## Key Features

- Supports both labeled and tabular invoice formats
- Multi-line item extraction and per-item math validation
- Dual OCR pass with automatic quality scoring
- Separates rule-based anomaly reasons from ML-based reasons
- Tested on 111 synthetic invoices across 4 vendors

---

## Anomaly Detection Methods

**Z-score analysis** — flags invoices where the amount deviates significantly 
from that vendor's historical average.

**Isolation Forest** — unsupervised ML model that identifies invoices deviating 
from the multivariate distribution of the dataset without requiring labeled 
training data.

**Rule-based checks** — duplicate invoice detection, future date flagging, 
and mathematical integrity validation.

---

## Output

The pipeline produces:
- `output/processed_invoices.csv` — structured data with `is_anomaly`, 
  `rule_anomaly_reason`, and `ml_anomaly_reason` columns
- `output/boxplot_by_vendor.png` — invoice amount distribution per vendor
- `output/scatter_anomalies.png` — scatter plot with anomalies highlighted
- `output/preprocessed_images/` — cleaned invoice images for inspection

---

## Installation

```bash
pip install opencv-python pytesseract pandas numpy scikit-learn pillow matplotlib seaborn fuzzywuzzy python-Levenshtein
```

Install Tesseract OCR engine:
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- After installing, update the path in `ocr_engine.py`:

```python
pytesseract.pytesseract.tesseract_cmd = r'C:\path\to\tesseract.exe'
```

---

## Usage

```bash
# Step 1: Generate sample invoices
python create_samples.py

# Step 2: Run the full pipeline
python main.py

# Step 3: Generate visualizations
python visualize.py
```

---

## Sample Results

| Invoice | Vendor | Grand Total | Anomaly | Reason |
|---|---|---|---|---|
| INV-GEN-HIGH-AMOUNT | TechSupplies Co. | $15,000 | ✅ Yes | Unusual amount (Z-score); Isolation Forest |
| INV-GEN-DUP-A | GlobalParts Inc. | $2,100 | ✅ Yes | Possible duplicate invoice details |
| INV-GEN-FUTURE-DATE | Skyline Logistics | $5,400 | ✅ Yes | Invoice date is in the future |

---

## Known Limitations

- Tabular invoice layouts with complex column structures require specialized 
  table-extraction tools beyond RegEx parsing
- Vendors with inherently high price variance may cause Isolation Forest 
  to over-flag legitimate invoices
- OCR accuracy is sensitive to image resolution and font quality

---

## Tech Stack

Python 3.14 · OpenCV · Tesseract · pytesseract · Pandas · NumPy · 
scikit-learn · Matplotlib · Seaborn · PIL
