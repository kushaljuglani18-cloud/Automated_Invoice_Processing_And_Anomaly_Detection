# ocr_engine.py
# Station 2: Read the text from the cleaned invoice image

import pytesseract        # The bridge between Python and Tesseract
from PIL import Image     # PIL helps Python handle image files

# Tell Python exactly where Tesseract is installed on your computer
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Kushal Juglani\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'


OCR_CONFIG = "--psm 4"


def extract_text(clean_image):
    """
    Takes a clean image (output from preprocessing.py)
    and returns all the text found in it as a string.
    """
    # Convert the image to a format PIL understands
    pil_image = Image.fromarray(clean_image)

    # PSM 4 works well for standard invoices with tables/columns.
    raw_text = pytesseract.image_to_string(pil_image, config=OCR_CONFIG)

    return raw_text


def extract_text_from_path(image_path, save_preprocessed=False):
    """
    A convenience function - give it an image path directly
    and it handles preprocessing + extraction in one shot.
    This is useful for quick testing.
    """
    from preprocessing import preprocess_image   # Import our Station 1

    original_text = pytesseract.image_to_string(Image.open(image_path), config=OCR_CONFIG)
    clean_image = preprocess_image(image_path, save_debug=save_preprocessed)    # Clean it first
    clean_text = extract_text(clean_image)         # Then read it

    # Clean images help noisy scans, but generated table invoices often OCR
    # better before thresholding. Keep the richer result.
    raw_text = max([original_text, clean_text], key=_ocr_text_score)

    return raw_text


def _ocr_text_score(text):
    """
    Scores OCR output so extract_text_from_path can pick the pass that kept
    the most useful invoice fields and table values.
    """
    money_count = text.count("$") + text.count("₹") + text.count("€") + text.count("£")
    digit_count = sum(char.isdigit() for char in text)
    keyword_count = sum(
        1 for keyword in ("Invoice", "Vendor", "Date", "Description", "Qty", "Total")
        if keyword.lower() in text.lower()
    )
    return (money_count * 10) + digit_count + (keyword_count * 5) + len(text.splitlines())
