from fastapi import FastAPI, UploadFile
import os, tempfile
from app.ocr_pipeline import process_with_tesseract_and_gemini

app = FastAPI()

@app.post("/process_pdf/")
async def process_pdf(file: UploadFile):
    # ✅ Use cross-platform temp directory
    input_path = os.path.join(tempfile.gettempdir(), file.filename)
    
    # Save uploaded file
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Run OCR + Gemini logic
    final_output = process_with_tesseract_and_gemini(input_path)

    # ✅ Return JSON directly
    return {"status": "completed", "data": final_output}
