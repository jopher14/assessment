import pytesseract
from pdf2image import convert_from_path
import pandas as pd
import re
import cv2
import numpy as np
import os

PDF_FOLDER = r"C:\Users\Kristine\Desktop\PYTHON\company-assessment\AIML-assessment\pdf"
POPPLER_PATH = r"C:\poppler\poppler-26.02.0\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

data = []

for file in sorted(os.listdir(PDF_FOLDER)):
    if file.lower().endswith(".pdf"):
        pdf_path = os.path.join(PDF_FOLDER, file)

        print(f"\nProcessing: {file}")

        pages = convert_from_path(pdf_path, dpi=500, poppler_path=POPPLER_PATH)

        for i, page in enumerate(pages):
            img = np.array(page)

            # Preprocess
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

            # OCR
            text = pytesseract.image_to_string(thresh, config="--oem 3 --psm 6")

            receipt_no = re.search(r"(?:OR\s*(?:No\.?|#)?|No\.?)\s*[:\-]?\s*([A-Z0-9\-]+)", text, re.IGNORECASE)
            doctor = re.search(r"Dr\.?\s*([A-Za-z\s]+)",text)
            prc = re.search(r"PRC\s*(?:Lic(?:ense)?\.?)?\s*(?:No\.?)?\s*[:\-]?\s*([0-9]+)",text, re.IGNORECASE)
            hospital = re.search(r"([A-Z][A-Za-z\s]+(?:Medical Center|Hospital))", text)
            date = re.search(r"([A-Za-z]+\s+\d{1,2},?\s+\d{4})", text)
            patient = re.search(r"(?:Patient|Pt\.?)\s*[:\-]?\s*([A-Za-z\s]+)", text, re.IGNORECASE)
            amount_match = re.search(r"TOTAL[^\d]{0,50}([\d,]+\.\d{2})", text, re.IGNORECASE | re.DOTALL)

            if amount_match:
                amount_value = amount_match.group(1)
            else:
                amounts = re.findall(r"[\d,]+\.\d{2}", text)
                amount_value = amounts[-1] if amounts else ""

            data.append({
                "File": file,
                "Page": i + 1,
                "Receipt No": receipt_no.group(1) if receipt_no else "",
                "Doctor Name": doctor.group(1).strip() if doctor else "",
                "PRC License": prc.group(1) if prc else "",
                "Hospital": hospital.group(1).strip() if hospital else "",
                "Date": date.group(1) if date else "",
                "Patient Name": patient.group(1).strip() if patient else "",
                "Total Amount (PHP)": amount_value,
                "Signature": "Yes" if "signature" in text.lower() or "physician" in text.lower() else ""
            })

df = pd.DataFrame(data)
df.to_excel("output.xlsx", index=False)

print("\nExtraction complete! Saved to output.xlsx")