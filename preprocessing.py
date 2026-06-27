# preprocessing.py
# Station 1: Clean the invoice image before reading it
import cv2 # OpenCV - the image processing library
import os


MIN_WIDTH_FOR_OCR = 1400
DEFAULT_PREPROCESSED_DIR = os.path.join("output", "preprocessed_images")


def load_image(image_path):
    """
    Load the image from a file path
    image_path = the location of the image on your computer
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")
    return image


def resize_for_ocr(image):
    """
    Enlarges small invoice images so table text and prices are easier to read.
    Already-large images are left unchanged.
    """
    height, width = image.shape[:2]
    if width >= MIN_WIDTH_FOR_OCR:
        return image

    scale = MIN_WIDTH_FOR_OCR / width
    new_size = (int(width * scale), int(height * scale))
    return cv2.resize(image, new_size, interpolation=cv2.INTER_CUBIC)


def convert_to_grayscale(image):
    """
    Converts a colorful image to black and white.
    Color is unnecessary for reading text - this process simplifies the image.
    """

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return gray


def reduce_noise(gray_image):
    """
    Blurs the image slightly to remove random specks and noise.
    Think of it like wiping dust off a document.
    5, 5 = the size of the blur (small enough to not blur the text)
    0 = calculated autommatically by OpenCV
    """
    blurred = cv2.medianBlur(gray_image, 3)
    return blurred


def binarize(blurred_image):
    """
    Converts the image to PURE black and white - no grey allowed.
    This makes text pop out sharply for the OCR engine to read.

    ADAPTIVE = it adjusts the black/white threshold for different
               parts of the image (handles uneven lighting)
    GAUSSIAN_C = the math formula used to calculate the threshold
    BINARY     = output is binary (black or white only)
    11         = how many pixels around each point it considers
    2          = fine-tuning constant subtracted from the result
    """
    binary = cv2.adaptiveThreshold(
        blurred_image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )
    return binary


def save_processed_image(clean_image, image_path, output_dir=DEFAULT_PREPROCESSED_DIR):
    """
    Saves the processed OCR-ready image for inspection/debugging.
    The output is kept outside sample_invoices so main.py does not process it
    as another invoice.
    """
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}_preprocessed.png")
    cv2.imwrite(output_path, clean_image)
    return output_path


def preprocess_image(image_path, save_debug=False, output_dir=DEFAULT_PREPROCESSED_DIR):
    """
    THE MAIN FUNCTION - runs all 4 steps in order.
    This is the only function other files will call.
    Give it an image path, it returns a clean image.
    """
    image = load_image(image_path)
    image = resize_for_ocr(image)
    gray = convert_to_grayscale(image)
    blurred = reduce_noise(gray)
    clean = binarize(blurred)

    if save_debug:
        save_processed_image(clean, image_path, output_dir)

    return clean


# =====================================================================
# Folder Discovery & Pipeline Verification Testing
# =====================================================================
from pathlib import Path

def discover_and_preprocess_invoices(input_folder, debug_output_dir=DEFAULT_PREPROCESSED_DIR):
    """
    Scans a folder for invoice images, runs the preprocessing pipeline on each,
    and saves the visual debug output to verify that everything works.
    """
    input_path = Path(input_folder)
    
    # 1. Check if the source folder exists
    if not input_path.exists():
        print(f"❌ Error: The folder '{input_folder}' does not exist.")
        return []

    # 2. Find all common image formats (case-insensitive extensions)
    valid_extensions = ("*.png", "*.jpg", "*.jpeg", "*.tiff", "*.bmp")
    invoice_files = []
    for ext in valid_extensions:
        # rglob scans the folder AND any subfolders inside it
        invoice_files.extend(list(input_path.rglob(ext)))
        invoice_files.extend(list(input_path.rglob(ext.upper())))

    print(f"🔍 Found {len(invoice_files)} invoice(s) inside '{input_folder}'.")

    # 3. Process each discovered invoice file
    processed_paths = []
    for i, file_path in enumerate(invoice_files, 1):
        str_path = str(file_path)
        print(f"[{i}/{len(invoice_files)}] Processing: {file_path.name}...")
        
        try:
            # Run the main pipeline and force save_debug=True to visually inspect results
            preprocess_image(str_path, save_debug=True, output_dir=debug_output_dir)
            processed_paths.append(str_path)
            
        except Exception as e:
            print(f"❌ Failed to preprocess {file_path.name}. Error: {e}")

    print(f"\n✅ Done! Check your preprocessed images in: '{debug_output_dir}'")
    return processed_paths


if __name__ == "__main__":
    # Define where your raw invoices are located
    # Change "sample_invoices" to the actual name of your input folder
    INPUT_INVOICES_FOLDER = "sample_invoices" 
    
    print("--- Starting ML Pipeline Preprocessing Verification ---")
    discover_and_preprocess_invoices(INPUT_INVOICES_FOLDER)
