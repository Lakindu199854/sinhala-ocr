import os
from dotenv import load_dotenv
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import openai

# =======================================================
# LOAD ENVIRONMENT VARIABLES
# =======================================================
load_dotenv()

ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
SUBSCRIPTION_KEY = os.getenv("AZURE_OPENAI_KEY")
POPPLER_PATH = os.getenv("POPPLER_PATH")
TESSERACT_PATH = os.getenv("TESSERACT_PATH")

# =======================================================
# CONFIGURATION
# =======================================================
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
openai.api_type = "azure"
openai.api_base = ENDPOINT
openai.api_version = API_VERSION
openai.api_key = SUBSCRIPTION_KEY

# Path to your input PDF
PDF_PATH = r"C:\Users\beecom\Desktop\MyProjects\ALPapers\2023-Physics.pdf"

# =======================================================
# FOLDER STRUCTURE
# =======================================================
pdf_name = os.path.splitext(os.path.basename(PDF_PATH))[0]
base_dir = os.path.join(os.path.dirname(PDF_PATH), pdf_name)
ocr_dir = os.path.join(base_dir, "ocr_output")
llm_dir = os.path.join(base_dir, "corrected_output")

os.makedirs(ocr_dir, exist_ok=True)
os.makedirs(llm_dir, exist_ok=True)

print(f"📁 Base folder: {base_dir}")

# =======================================================
# STEP 1: PDF → IMAGES
# =======================================================
print("📄 Converting PDF to images...")
pages = convert_from_path(PDF_PATH, dpi=300, poppler_path=POPPLER_PATH)

for i, page in enumerate(pages, start=1):
    img_path = os.path.join(base_dir, f"{pdf_name}_page-{i:04d}.jpg")
    page.save(img_path, "JPEG")
    print(f"🖼️ Saved image: {img_path}")

# =======================================================
# STEP 2: OCR EACH IMAGE
# =======================================================
def run_ocr(image_path):
    return pytesseract.image_to_string(Image.open(image_path), lang="sin+eng")

ocr_texts = []
for i in range(len(pages)):
    img_path = os.path.join(base_dir, f"{pdf_name}_page-{i+1:04d}.jpg")
    text = run_ocr(img_path)
    ocr_path = os.path.join(ocr_dir, f"page-{i+1:04d}.txt")
    with open(ocr_path, "w", encoding="utf-8") as f:
        f.write(text)
    ocr_texts.append((ocr_path, text))
    print(f"📝 OCR output saved: {ocr_path}")

# =======================================================
# STEP 3: SEND TO AZURE OPENAI FOR CORRECTION
# =======================================================
SYSTEM_PROMPT = (
    "You are a Sinhala OCR correction assistant. I will give you raw Sinhala text that was extracted "
    "from an image using OCR. Your task is to fix only visual or technical inconsistencies such as misplaced spaces, "
    "misrecognized Sinhala letters, broken conjuncts, mixed Latin/Sinhala symbols, or punctuation errors. "
    "Do not change, replace, or interpret any words. Do not rephrase, simplify, or guess missing parts. "
    "Keep the exact same Sinhala words, order, and meaning exactly as in the OCR text. "
    "Only repair the text so that every Sinhala word is properly written, spaced, and readable — "
    "preserving all numbers, symbols, and equations exactly as they appear."
)

print("🤖 Sending OCR text to GPT-5-mini for correction...")

for ocr_path, raw_text in ocr_texts:
    page_name = os.path.basename(ocr_path).replace(".txt", "")
    corrected_path = os.path.join(llm_dir, f"{page_name}_corrected.txt")

    try:
        response = openai.ChatCompletion.create(
            engine=DEPLOYMENT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": raw_text}
            ],
            temperature=0,
        )
        corrected_text = response["choices"][0]["message"]["content"]

        with open(corrected_path, "w", encoding="utf-8") as f:
            f.write(corrected_text)

        print(f"✅ Corrected output saved: {corrected_path}")

    except Exception as e:
        print(f"❌ Error correcting {ocr_path}: {e}")

print("🎉 Done — All OCR text processed and corrected.")
