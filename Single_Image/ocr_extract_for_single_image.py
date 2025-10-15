# import os
# from PIL import Image
# import pytesseract
# import cv2

# # If Tesseract isn’t found automatically, uncomment and update this path:
# pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# # Path to your image
# image_path = "file.jpg"  # 👈 change this

# # --- Optional: clean the image before OCR ---
# img = cv2.imread(image_path)
# gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

# # Save temporary processed version
# cv2.imwrite("processed.jpg", thresh)

# # Perform OCR using Sinhala + English (fallback)
# text = pytesseract.image_to_string(Image.open("processed.jpg"), lang="sin+eng")

# # Print the extracted text
# print("===== Extracted Text =====\n")
# print(text)

import  os
from PIL import Image
import pytesseract

# If Tesseract isn't in PATH, uncomment this:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

text = pytesseract.image_to_string(Image.open("page3.jpg"), lang="sin+eng")
print(text)


























