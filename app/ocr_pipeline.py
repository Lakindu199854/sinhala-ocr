import os
from dotenv import load_dotenv
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from google import genai
from google.genai import types
import json

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TESSERACT_PATH = os.getenv("TESSERACT_PATH")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Load system prompt
with open("app/system_prompt.md", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

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
                        }
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


def run_ocr(image_path):
    """Runs Tesseract OCR on a given image file."""
    try:
        return pytesseract.image_to_string(Image.open(image_path), lang="sin+eng")
    except Exception as e:
        print(f"❌ Error during OCR for {image_path}: {e}")
        return ""


def process_with_tesseract_and_gemini(pdf_path: str) -> str:
    """
    Converts PDF to images, performs OCR, sends to Gemini,
    and writes the combined JSON output.
    Returns the output JSON path.
    """
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    base_dir = os.path.join(os.path.dirname(pdf_path), pdf_name)
    llm_dir = os.path.join(base_dir, "corrected_output")

    os.makedirs(llm_dir, exist_ok=True)

    client = genai.Client(api_key=GEMINI_API_KEY)
    merged_questions = []

    pages = convert_from_path(pdf_path, dpi=300)
    for i, page in enumerate(pages, start=1):
        img_path = os.path.join(base_dir, f"{pdf_name}_page-{i:04d}.jpg")
        page.save(img_path, "JPEG")

        print(f"🔍 OCR on {img_path}")
        raw_text = run_ocr(img_path)

        if not raw_text.strip():
            print(f"⚠️ No text in page-{i:04d}, skipping.")
            continue

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
                contents=[raw_text],
            )

            page_data = json.loads(response.text)
            if "questions" in page_data:
                merged_questions.extend(page_data["questions"])
        except Exception as e:
            print(f"❌ Error processing page-{i:04d}: {e}")

    final_output_path = os.path.join(base_dir, "final_questions.json")
    with open(final_output_path, "w", encoding="utf-8") as f:
        json.dump(merged_questions, f, ensure_ascii=False, indent=2)

    print(f"🎉 Done: {final_output_path}")
    return merged_questions