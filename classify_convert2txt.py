import os
from pathlib import Path
from pdfminer.high_level import extract_text
from pdf2image import convert_from_path 
import fitz  # PyMuPDF
import pytesseract 

input_root = Path("/path/to/input/directory")  # Directory containing raw PDFs
output_root = Path("/path/to/output/directory")  # Directory for processed text files
temp_ocr_dir = Path("/path/to/temp/ocr/directory")  # Temporary directory for OCR results
output_format = "text"  # Output format is set to "text" only

temp_ocr_dir.mkdir(parents=True, exist_ok=True)
output_root.mkdir(parents=True, exist_ok=True)

def classify_pdf(file_path, min_text_length=500, min_text_per_page=100, image_page_ratio=0.8):
    """Classify PDFs into 'searchable' or 'image-based'."""
    try:
        # Extract embedded text to determine the text length
        text = extract_text(file_path)
        text_length = len(text.strip())

        doc = fitz.open(file_path)
        num_pages = len(doc)
        text_per_page = text_length / num_pages if num_pages else 0
        image_pages = sum(1 for page in doc if page.get_images())
        image_ratio = image_pages / num_pages if num_pages else 0

        # Classify based on thresholds
        if text_length < min_text_length or text_per_page < min_text_per_page or image_ratio > image_page_ratio:
            return "image", text_length, text_per_page, image_ratio
        else:
            return "searchable", text_length, text_per_page, image_ratio
    except Exception as e:
        return f"error: {e}", None, None, None

def ocr_pdf(original_pdf_path, ocr_pdf_path):
    """Perform OCR on image-based PDFs."""
    try:
        images = convert_from_path(original_pdf_path, dpi=300)
        merged_pdf = fitz.open()
        for img in images:
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension="pdf")
            single_page_pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
            merged_pdf.insert_pdf(single_page_pdf)
        merged_pdf.save(ocr_pdf_path)
        merged_pdf.close()
        return True
    except Exception as e:
        print(f"OCR failed for {original_pdf_path}: {e}")
        return False

def convert_pdf_to_text(pdf_path, output_path):
    """Extract text from PDFs and save to .txt files."""
    try:
        text = extract_text(pdf_path)
        with open(output_path.with_suffix(".txt"), "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        print(f"Failed to extract text: {pdf_path}: {e}")

def process_pdfs(input_root, output_root):
    """Process PDFs to classify and extract text."""
    for dirpath, _, filenames in os.walk(input_root):
        for filename in filenames:
            if filename.lower().endswith(".pdf"):
                pdf_path = Path(dirpath) / filename
                rel_path = pdf_path.relative_to(input_root)
                output_path = output_root / rel_path.with_suffix("")
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Classify the PDF
                classification, text_len, tpp, img_ratio = classify_pdf(pdf_path)

                if classification == "searchable":
                    print(f"Searchable: {pdf_path} (Text: {text_len}, TPP: {tpp:.1f}, ImgRatio: {img_ratio:.2f})")
                    convert_pdf_to_text(pdf_path, output_path)

                elif classification == "image":
                    print(f"Scanned: {pdf_path} → Performing OCR...")
                    ocr_pdf_path = temp_ocr_dir / rel_path.name
                    success = ocr_pdf(pdf_path, ocr_pdf_path)
                    if success:
                        try:
                            fitz.open(ocr_pdf_path)  # Validate the OCR result
                            convert_pdf_to_text(ocr_pdf_path, output_path)
                        except Exception as e:
                            print(f"Skipping invalid OCR output {ocr_pdf_path}: {e}")
                    else:
                        print(f"⚠ OCR failed, skipping: {pdf_path}")

                else:
                    print(f"⚠ Error with {pdf_path}: {classification}")
