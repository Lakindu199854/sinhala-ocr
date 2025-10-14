import os
from dotenv import load_dotenv
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from google import genai  # Google’s GenAI client

# --- Load env vars ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TESSERACT_PATH = os.getenv("TESSERACT_PATH")

# --- Setup Tesseract ---
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# --- Setup Gemini client ---
client = genai.Client(api_key=GEMINI_API_KEY)

# --- Pipeline config ---
PDF_PATH = "20232024-AL-Physics-Paper-Sinhala-Medium-1-10.pdf"
pdf_name = os.path.splitext(os.path.basename(PDF_PATH))[0]
base_dir = os.path.join(os.path.dirname(PDF_PATH), pdf_name)
ocr_dir = os.path.join(base_dir, "ocr_output")
llm_dir = os.path.join(base_dir, "corrected_output")

os.makedirs(ocr_dir, exist_ok=True)
os.makedirs(llm_dir, exist_ok=True)

print(f"📁 Base folder: {base_dir}")

# --- PDF → images ---
print("📄 Converting PDF to images...")
pages = convert_from_path(PDF_PATH, dpi=300)
for i, page in enumerate(pages, start=1):
    img_path = os.path.join(base_dir, f"{pdf_name}_page-{i:04d}.jpg")
    page.save(img_path, "JPEG")
    print(f"🖼️ Saved: {img_path}")

# --- OCR each page ---
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

# --- Gemini correction calls ---
SYSTEM_PROMPT = (
    "You are a Sinhala OCR correction assistant. I will give you raw Sinhala text that was extracted "
    "from an image using OCR. Your task is to fix only visual or technical inconsistencies such as misplaced spaces, "
    "misrecognized Sinhala letters, broken conjuncts, mixed Latin/Sinhala symbols, or punctuation errors. "
    "Do not change, replace, or interpret any words. Do not rephrase, simplify, or guess missing parts. "
    "Keep the exact same Sinhala words, order, and meaning exactly as in the OCR text. "
    "Only repair the text so that every Sinhala word is properly written, spaced, and readable — "
    "preserving all numbers, symbols, and equations exactly as they appear."
    "At the end of each question and its answers give the correct answer with an explanatuion in sinhala.There are some questions with figures,so dont give answers to those."
)

print("🤖 Sending OCR text to Gemini for correction...")

for ocr_path, raw_text in ocr_texts:
    page_name = os.path.basename(ocr_path).replace(".txt", "")
    corrected_path = os.path.join(llm_dir, f"{page_name}_corrected.txt")
    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash",  # or whichever Gemini model you're using
            contents=[raw_text,SYSTEM_PROMPT]
        )
        corrected_text = resp.text  # or resp.whatever field has the text

        with open(corrected_path, "w", encoding="utf-8") as f:
            f.write(corrected_text)
        print(f"✅ Corrected output saved: {corrected_path}")
    except Exception as e:
        print(f"❌ Error correcting {ocr_path}: {e}")

print("🎉 Done — All OCR text processed and corrected with Gemini.")
