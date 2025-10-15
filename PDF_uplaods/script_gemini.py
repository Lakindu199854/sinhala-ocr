import os
from dotenv import load_dotenv
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from google import genai  # Google’s GenAI client
from google.genai import types
import json



# --- Load env vars ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TESSERACT_PATH = os.getenv("TESSERACT_PATH")

# --- Setup Tesseract ---
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

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
    """Runs Tesseract OCR on a given image file."""
    try:
        return pytesseract.image_to_string(Image.open(image_path), lang="sin+eng")
    except Exception as e:
        print(f"❌ Error during OCR for {image_path}: {e}")
        return ""

# --- Gemini correction calls ---
with open("system_prompt.md", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# Define the schema for the expected JSON output to guide the model
response_schema = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question_number": {"type": "integer"},
                    "question_text": {"type": "string"},
                    "options": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "number": {"type": "string"},
                                "text": {"type": "string"}
                            },
                            "required": ["number", "text"]
                        },
                        "description": "List of options, each with a number and text"
                    },
                    "correct_answer": {"type": "string"},
                    "explanation": {"type": "string"}
                },
                "required": [
                    "question_number",
                    "question_text",
                    "options",
                    "correct_answer",
                    "explanation"
                ]
            }
        }
    },
    "required": ["questions"]
}


# --- Gemini correction calls ---
print("🤖 Sending OCR text to Gemini for correction...")

client = genai.Client(api_key=GEMINI_API_KEY)
merged_questions = []

for i, page in enumerate(pages, start=1):
    img_path = os.path.join(base_dir, f"{pdf_name}_page-{i:04d}.jpg")
    page_name = f"page-{i:04d}"
    corrected_json_path = os.path.join(llm_dir, f"{page_name}_corrected.json")

    print(f"🔍 Running OCR on {page_name}...")
    print(img_path)
    raw_text = run_ocr(img_path)

    if not raw_text.strip():
        print(f"⚠️ No text detected in {page_name}, skipping.")
        continue

    try:
        # Send OCR text directly to Gemini (no saving)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
            contents=[raw_text],
        )

        # Parse JSON response
        page_data = json.loads(response.text)

        # Save page-level JSON
        with open(corrected_json_path, "w", encoding="utf-8") as f:
            json.dump(page_data, f, ensure_ascii=False, indent=2)

        print(f"✅ JSON saved for {page_name}: {corrected_json_path}")

        # Add to merged questions
        if "questions" in page_data:
            merged_questions.extend(page_data["questions"])
            print(f"🟢 {len(page_data['questions'])} questions added from {page_name}")
        else:
            print(f"🟡 No questions found in {page_name}")

    except Exception as e:
        print(f"❌ Error processing {page_name}: {e}")
        continue

# --- Save final merged JSON ---
final_output_path = os.path.join(base_dir, "final_questions.json")
with open(final_output_path, "w", encoding="utf-8") as f:
    json.dump(merged_questions, f, ensure_ascii=False, indent=2)

print(f"🎉 Done — Merged all questions into: {final_output_path}")
