import os
from PIL import Image
import pytesseract
import cv2

# If Tesseract isn’t found automatically, uncomment and update this path:
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Path to your image
image_folder = "images"  # 👈 change this

for filename in os.listdir(image_folder):
    image_path = os.path.join(image_folder, filename)
    print(f"\n===== Extracting from: {filename} =====")

    # # --- Optional: clean the image before OCR ---
    # img = cv2.imread(image_path)
    # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

    # # Save temporary processed version
    
    # processed_path = os.path.join(image_folder, "processed_temp.jpg")
    # cv2.imwrite(processed_path, thresh)

    # Perform OCR using Sinhala + English (fallback)
    text = pytesseract.image_to_string(Image.open("image_path"), lang="sin+eng")

    # Print the extracted text
    print("===== Extracted Text =====\n")
    print(text)
print("\n✅ OCR extraction completed for all images in the folder.")
